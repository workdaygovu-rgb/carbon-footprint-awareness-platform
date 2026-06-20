import { afterEach, describe, expect, it, vi } from "vitest";
import * as api from "./api";
import { emptyInput } from "./types";
import type { FootprintResult } from "./types";

const result: FootprintResult = {
  breakdown_kg: { transport: 0, home: 0, diet: 1050, consumption: 0 },
  total_annual_kg: 1050,
  total_annual_tonnes: 1.05,
  comparison: {
    global_average_annual_kg: 4800,
    sustainable_target_annual_kg: 2000,
    ratio_to_global_average: 0.219,
    ratio_to_sustainable_target: 0.525,
  },
};

function mockFetch(status: number, body: unknown) {
  const fn = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

function mockFetchWithJsonError(status: number) {
  const fn = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.reject(new Error("bad json")),
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client", () => {
  it("posts the input to /api/calculate and returns the result", async () => {
    const fetchMock = mockFetch(200, result);
    const controller = new AbortController();
    const res = await api.calculate(emptyInput(), { signal: controller.signal });
    expect(res.total_annual_kg).toBe(1050);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/calculate");
    expect(init.method).toBe("POST");
    expect(init.headers["Content-Type"]).toBe("application/json");
    expect(init.signal).toBe(controller.signal);
  });

  it("throws a descriptive error when the server responds non-2xx", async () => {
    mockFetch(422, { detail: "invalid" });
    await expect(api.getInsights(emptyInput())).rejects.toThrow(/\/api\/insights.*422/);
  });

  it("falls back to a status-only error when the error body is malformed", async () => {
    mockFetchWithJsonError(500);
    await expect(api.getInsights(emptyInput())).rejects.toThrow(
      "Request to /api/insights failed (500)",
    );
  });

  it("throws a network ApiError when POST fetch fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    await expect(api.calculate(emptyInput())).rejects.toMatchObject({
      name: "ApiError",
      status: 0,
    });
  });

  it("throws when a successful POST response is not JSON", async () => {
    mockFetchWithJsonError(200);
    await expect(api.calculate(emptyInput())).rejects.toThrow(
      "Invalid JSON response from /api/calculate",
    );
  });

  it("sends device id, input and result when saving an entry", async () => {
    const fetchMock = mockFetch(201, {
      id: "e1",
      created_at: "2026-01-01T00:00:00Z",
      device_id: "dev-abc12345",
      input: emptyInput(),
      result,
    });
    await api.saveEntry("dev-abc12345", emptyInput(), result);
    const [, init] = fetchMock.mock.calls[0];
    const payload = JSON.parse(init.body);
    expect(payload.device_id).toBe("dev-abc12345");
    expect(payload.result.total_annual_kg).toBe(1050);
  });

  it("URL-encodes the device id when listing entries", async () => {
    const fetchMock = mockFetch(200, []);
    const controller = new AbortController();
    await api.listEntries("dev-abc 12345", { signal: controller.signal });
    expect(fetchMock.mock.calls[0][0]).toBe("/api/entries/dev-abc%2012345");
    expect(fetchMock.mock.calls[0][1].signal).toBe(controller.signal);
  });

  it("throws when history cannot be loaded", async () => {
    mockFetch(500, {});
    await expect(api.listEntries("dev-abc12345")).rejects.toThrow(/500/);
  });

  it("throws a network ApiError when history fetch fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    await expect(api.listEntries("dev-abc12345")).rejects.toMatchObject({
      name: "ApiError",
      status: 0,
    });
  });

  it("throws when history returns invalid JSON", async () => {
    mockFetchWithJsonError(200);
    await expect(api.listEntries("dev-abc12345")).rejects.toThrow(
      "Invalid history response from server",
    );
  });
});
