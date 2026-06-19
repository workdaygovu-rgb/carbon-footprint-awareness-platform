import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { axe } from "vitest-axe";
import { HistoryPanel } from "./HistoryPanel";
import type { Entry, FootprintResult } from "../lib/types";

function makeEntry(id: string, createdAt: string, tonnes: number): Entry {
  const result: FootprintResult = {
    breakdown_kg: { transport: 0, home: 0, diet: tonnes * 1000, consumption: 0 },
    total_annual_kg: tonnes * 1000,
    total_annual_tonnes: tonnes,
    comparison: {
      global_average_annual_kg: 4800,
      sustainable_target_annual_kg: 2000,
      ratio_to_global_average: 1,
      ratio_to_sustainable_target: 1,
    },
  };
  return {
    id,
    created_at: createdAt,
    device_id: "dev-test-1234",
    input: {} as never,
    result,
  };
}

describe("HistoryPanel", () => {
  it("has no accessibility violations with entries", async () => {
    const entries = [
      makeEntry("e2", "2026-02-01T10:00:00Z", 4.2),
      makeEntry("e1", "2026-01-01T10:00:00Z", 5.0),
    ];
    const { container } = render(<HistoryPanel entries={entries} />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it("shows an inviting empty state when there are no entries", () => {
    render(<HistoryPanel entries={[]} />);
    expect(screen.getByText(/no saved entries yet/i)).toBeInTheDocument();
  });

  it("announces a downward trend when the footprint shrinks", () => {
    const entries = [
      makeEntry("e2", "2026-02-01T10:00:00Z", 4.0),
      makeEntry("e1", "2026-01-01T10:00:00Z", 5.0),
    ];
    render(<HistoryPanel entries={entries} />);
    expect(screen.getByText(/down 1 t since your last entry/i)).toBeInTheDocument();
  });

  it("announces an upward trend when the footprint grows", () => {
    const entries = [
      makeEntry("e2", "2026-02-01T10:00:00Z", 6.0),
      makeEntry("e1", "2026-01-01T10:00:00Z", 5.0),
    ];
    render(<HistoryPanel entries={entries} />);
    expect(screen.getByText(/up 1 t since your last entry/i)).toBeInTheDocument();
  });

  it("reports no change for an identical footprint", () => {
    const entries = [
      makeEntry("e2", "2026-02-01T10:00:00Z", 5.0),
      makeEntry("e1", "2026-01-01T10:00:00Z", 5.0),
    ];
    render(<HistoryPanel entries={entries} />);
    expect(screen.getByText(/no change since your last entry/i)).toBeInTheDocument();
  });

  it("renders one table row per saved entry", () => {
    const entries = [
      makeEntry("e3", "2026-03-01T10:00:00Z", 4.0),
      makeEntry("e2", "2026-02-01T10:00:00Z", 4.5),
      makeEntry("e1", "2026-01-01T10:00:00Z", 5.0),
    ];
    render(<HistoryPanel entries={entries} />);
    // One header row plus one row per entry.
    expect(screen.getAllByRole("row")).toHaveLength(4);
  });
});
