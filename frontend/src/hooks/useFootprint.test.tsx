import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import { useFootprint } from "./useFootprint";
import * as api from "../lib/api";
import * as deviceId from "../lib/deviceId";
import { emptyInput } from "../lib/types";
import type { Entry, FootprintResult, InsightsResponse } from "../lib/types";

vi.mock("../lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../lib/api")>();
  return {
    ...actual,
    calculate: vi.fn(),
    getInsights: vi.fn(),
    saveEntry: vi.fn(),
    listEntries: vi.fn(),
  };
});
vi.mock("../lib/deviceId", () => ({ getDeviceId: vi.fn() }));

const mockDeviceId = "dev-test-1234";

const result: FootprintResult = {
  breakdown_kg: { transport: 2000, home: 1000, diet: 1500, consumption: 500 },
  total_annual_kg: 5000,
  total_annual_tonnes: 5.0,
  comparison: {
    global_average_annual_kg: 4800,
    sustainable_target_annual_kg: 2000,
    ratio_to_global_average: 1.04,
    ratio_to_sustainable_target: 2.5,
  },
};

const insights: InsightsResponse = {
  summary: "Your footprint is above the sustainable target.",
  recommendations: [
    { category: "transport", action: "Drive less", estimated_annual_savings_kg: 400 },
  ],
  source: "rules",
};

const savedEntry: Entry = {
  id: "e1",
  created_at: new Date().toISOString(),
  device_id: mockDeviceId,
  input: emptyInput(),
  result,
};

describe("useFootprint", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(deviceId.getDeviceId).mockReturnValue(mockDeviceId);
    vi.mocked(api.listEntries).mockResolvedValue([]);
    vi.mocked(api.calculate).mockResolvedValue(result);
    vi.mocked(api.getInsights).mockResolvedValue(insights);
    vi.mocked(api.saveEntry).mockResolvedValue(savedEntry);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loads history on mount", async () => {
    renderHook(() => useFootprint());
    await waitFor(() => expect(api.listEntries).toHaveBeenCalledWith(mockDeviceId));
  });

  it("calculates footprint and insights", async () => {
    const { result: hook } = renderHook(() => useFootprint());
    const input = emptyInput();

    await waitFor(() => expect(api.listEntries).toHaveBeenCalled());
    await act(() => hook.current.calculate(input));

    expect(api.calculate).toHaveBeenCalledWith(input, { signal: expect.any(AbortSignal) });
    expect(api.getInsights).toHaveBeenCalledWith(input, { signal: expect.any(AbortSignal) });
    expect(hook.current.result).toEqual(result);
    expect(hook.current.insights).toEqual(insights);
    expect(hook.current.status).toMatch(/ready below/i);
  });

  it("shows an error when calculation fails", async () => {
    vi.mocked(api.calculate).mockRejectedValueOnce(new api.ApiError("Server error", 500));
    const { result: hook } = renderHook(() => useFootprint());

    await waitFor(() => expect(api.listEntries).toHaveBeenCalled());
    await act(() => hook.current.calculate(emptyInput()));

    expect(hook.current.error).toBe("Server error");
  });

  it("shows a generic error when calculation fails unexpectedly", async () => {
    vi.mocked(api.calculate).mockRejectedValueOnce(new Error("boom"));
    const { result: hook } = renderHook(() => useFootprint());

    await waitFor(() => expect(api.listEntries).toHaveBeenCalled());
    await act(() => hook.current.calculate(emptyInput()));

    expect(hook.current.error).toMatch(/Something went wrong/i);
  });

  it("ignores history loading failures", async () => {
    vi.mocked(api.listEntries).mockRejectedValueOnce(new api.ApiError("offline", 0));

    const { result: hook } = renderHook(() => useFootprint());

    await waitFor(() => expect(api.listEntries).toHaveBeenCalled());
    expect(hook.current.entries).toEqual([]);
    expect(hook.current.error).toBeNull();
  });

  it("does not save before a result exists", async () => {
    const { result: hook } = renderHook(() => useFootprint());

    await waitFor(() => expect(api.listEntries).toHaveBeenCalled());
    await act(() => hook.current.save());

    expect(api.saveEntry).not.toHaveBeenCalled();
  });

  it("saves the latest result and refreshes history", async () => {
    const { result: hook } = renderHook(() => useFootprint());

    await waitFor(() => expect(api.listEntries).toHaveBeenCalled());
    await act(() => hook.current.calculate(emptyInput()));
    expect(hook.current.result).not.toBeNull();

    await act(() => hook.current.save());
    expect(api.saveEntry).toHaveBeenCalledTimes(1);
    expect(api.listEntries).toHaveBeenCalledTimes(2);
  });

  it("shows an error when saving fails", async () => {
    vi.mocked(api.saveEntry).mockRejectedValueOnce(new api.ApiError("Forbidden", 403));
    const { result: hook } = renderHook(() => useFootprint());

    await waitFor(() => expect(api.listEntries).toHaveBeenCalled());
    await act(() => hook.current.calculate(emptyInput()));
    expect(hook.current.result).not.toBeNull();

    await act(() => hook.current.save());
    expect(hook.current.error).toBe("Forbidden");
  });

  it("shows a generic error when saving fails unexpectedly", async () => {
    vi.mocked(api.saveEntry).mockRejectedValueOnce(new Error("boom"));
    const { result: hook } = renderHook(() => useFootprint());

    await waitFor(() => expect(api.listEntries).toHaveBeenCalled());
    await act(() => hook.current.calculate(emptyInput()));
    await act(() => hook.current.save());

    expect(hook.current.error).toMatch(/Could not save/i);
  });
});
