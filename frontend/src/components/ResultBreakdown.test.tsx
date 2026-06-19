import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { axe } from "vitest-axe";
import { ResultBreakdown } from "./ResultBreakdown";
import type { FootprintResult } from "../lib/types";

const result: FootprintResult = {
  breakdown_kg: { transport: 2000, home: 1000, diet: 1500, consumption: 500 },
  total_annual_kg: 5000,
  total_annual_tonnes: 5.0,
  comparison: {
    global_average_annual_kg: 4800,
    sustainable_target_annual_kg: 2000,
    ratio_to_global_average: 1.042,
    ratio_to_sustainable_target: 2.5,
  },
};

describe("ResultBreakdown", () => {
  it("has no accessibility violations", async () => {
    const { container } = render(<ResultBreakdown result={result} />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it("shows the total and a row per category", () => {
    render(<ResultBreakdown result={result} />);
    expect(screen.getByText(/5 t CO₂e/i)).toBeInTheDocument();
    // Category labels appear (in the bar chart and the data table).
    expect(screen.getAllByText("Transport").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Home energy").length).toBeGreaterThan(0);
  });

  it("provides an accessible data table equivalent of the chart", () => {
    render(<ResultBreakdown result={result} />);
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByRole("rowheader", { name: "Diet" })).toBeInTheDocument();
  });
});
