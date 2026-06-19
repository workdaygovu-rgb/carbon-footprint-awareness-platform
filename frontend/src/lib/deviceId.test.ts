import { beforeEach, describe, expect, it, vi } from "vitest";
import { getDeviceId } from "./deviceId";

describe("getDeviceId", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("generates an id and persists it to localStorage", () => {
    const id = getDeviceId();
    expect(id).toMatch(/^dev-[A-Za-z0-9]+$/);
    expect(localStorage.getItem("carbon_device_id")).toBe(id);
  });

  it("returns the same id on subsequent calls", () => {
    expect(getDeviceId()).toBe(getDeviceId());
  });

  it("reuses an id that already exists in storage", () => {
    localStorage.setItem("carbon_device_id", "dev-existing1234");
    expect(getDeviceId()).toBe("dev-existing1234");
  });

  it("still returns an ephemeral id when localStorage is unavailable", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("denied (privacy mode)");
    });
    const id = getDeviceId();
    expect(id).toMatch(/^dev-/);
  });

  it("falls back to a timestamp-based id without crypto.randomUUID", () => {
    vi.stubGlobal("crypto", {});
    try {
      const id = getDeviceId();
      expect(id).toMatch(/^dev-[a-z0-9]+$/);
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
