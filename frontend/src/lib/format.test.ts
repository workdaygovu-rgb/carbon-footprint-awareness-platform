import { describe, expect, it } from "vitest";
import { categoryLabel, formatDate, formatKg, formatTonnes } from "./format";

describe("format helpers", () => {
  it("formats kilograms with a unit and no decimals", () => {
    expect(formatKg(1234.6)).toMatch(/kg$/);
    expect(formatKg(1234.6)).not.toMatch(/\./);
  });

  it("formats tonnes with a unit", () => {
    expect(formatTonnes(2.5)).toMatch(/t$/);
  });

  it("maps known category keys to friendly labels", () => {
    expect(categoryLabel("home")).toBe("Home energy");
    expect(categoryLabel("transport")).toBe("Transport");
  });

  it("falls back to the raw key for unknown categories", () => {
    expect(categoryLabel("mystery")).toBe("mystery");
  });

  it("returns the raw string for an invalid date", () => {
    expect(formatDate("not-a-date")).toBe("not-a-date");
  });

  it("renders a locale string for a valid ISO date", () => {
    const formatted = formatDate("2026-01-15T12:30:00Z");
    expect(formatted).not.toBe("2026-01-15T12:30:00Z");
    expect(formatted).toMatch(/2026/);
  });
});
