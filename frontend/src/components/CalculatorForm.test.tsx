import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { CalculatorForm } from "./CalculatorForm";

describe("CalculatorForm", () => {
  it("has no accessibility violations", async () => {
    const { container } = render(<CalculatorForm onSubmit={() => {}} loading={false} />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it("submits the entered values via onSubmit", async () => {
    const onSubmit = vi.fn();
    render(<CalculatorForm onSubmit={onSubmit} loading={false} />);

    const carKm = screen.getByLabelText(/car distance per week/i);
    await userEvent.clear(carKm);
    await userEvent.type(carKm, "120");

    await userEvent.selectOptions(screen.getByLabelText(/diet/i), "vegan");
    await userEvent.click(screen.getByRole("button", { name: /calculate my footprint/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    const payload = onSubmit.mock.calls[0][0];
    expect(payload.transport.car_km_per_week).toBe(120);
    expect(payload.diet).toBe("vegan");
  });

  it("captures every field of a fully filled-in form", async () => {
    const onSubmit = vi.fn();
    render(<CalculatorForm onSubmit={onSubmit} loading={false} />);

    const fill = async (label: RegExp, value: string) => {
      const field = screen.getByLabelText(label);
      await userEvent.clear(field);
      await userEvent.type(field, value);
    };

    await fill(/car distance per week/i, "100");
    await userEvent.selectOptions(screen.getByLabelText(/car fuel type/i), "electric");
    await fill(/public transit per week/i, "40");
    await fill(/short-haul flights/i, "2");
    await fill(/long-haul flights/i, "1");
    await fill(/electricity per month/i, "250");
    await fill(/natural gas per month/i, "120");
    await fill(/people in household/i, "3");
    await userEvent.selectOptions(screen.getByLabelText(/diet/i), "vegetarian");
    await fill(/goods spending per month/i, "300");
    await fill(/landfill waste per week/i, "5");
    await userEvent.click(screen.getByRole("button", { name: /calculate my footprint/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toEqual({
      transport: {
        car_km_per_week: 100,
        car_fuel: "electric",
        public_transit_km_per_week: 40,
        short_haul_flights_per_year: 2,
        long_haul_flights_per_year: 1,
      },
      home: {
        electricity_kwh_per_month: 250,
        natural_gas_kwh_per_month: 120,
        household_size: 3,
      },
      diet: "vegetarian",
      consumption: {
        goods_spend_usd_per_month: 300,
        waste_kg_per_week: 5,
      },
    });
  });

  it("disables the submit button and marks it busy while loading", () => {
    render(<CalculatorForm onSubmit={() => {}} loading={true} />);
    const button = screen.getByRole("button", { name: /calculating/i });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
  });

  it("associates the household hint with its input for screen readers", () => {
    render(<CalculatorForm onSubmit={() => {}} loading={false} />);
    expect(screen.getByLabelText(/people in household/i)).toHaveAccessibleDescription(
      /home energy is shared/i,
    );
  });

  it("constrains numeric inputs to the documented bounds", () => {
    render(<CalculatorForm onSubmit={() => {}} loading={false} />);
    expect(screen.getByLabelText(/car distance per week/i)).toHaveAttribute("max", "20000");
    expect(screen.getByLabelText(/short-haul flights/i)).toHaveAttribute("max", "200");
    expect(screen.getByLabelText(/people in household/i)).toHaveAttribute("max", "50");
  });
});
