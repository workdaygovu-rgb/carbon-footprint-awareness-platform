import { useState } from "react";
import { type CarbonInput, type CarFuel, type DietType, emptyInput } from "../lib/types";
import { NumberField } from "./NumberField";

interface Props {
  onSubmit: (input: CarbonInput) => void;
  loading: boolean;
}

// Input ceilings mirror the backend Pydantic bounds (app/models.py) so the
// browser blocks out-of-range values before the API would reject them.
const MAX_KM_WEEK = 20_000;
const MAX_KWH_MONTH = 100_000;
const MAX_FLIGHTS = 200;
const MAX_USD_MONTH = 1_000_000;
const MAX_WASTE_WEEK = 1_000;
const MAX_HOUSEHOLD = 50;

const DIET_OPTIONS: { value: DietType; label: string }[] = [
  { value: "heavy_meat", label: "Heavy meat eater" },
  { value: "medium_meat", label: "Average meat eater" },
  { value: "low_meat", label: "Low meat" },
  { value: "pescatarian", label: "Pescatarian" },
  { value: "vegetarian", label: "Vegetarian" },
  { value: "vegan", label: "Vegan" },
];

const FUEL_OPTIONS: { value: CarFuel; label: string }[] = [
  { value: "petrol", label: "Petrol" },
  { value: "diesel", label: "Diesel" },
  { value: "hybrid", label: "Hybrid" },
  { value: "electric", label: "Electric" },
];

/** Accessible footprint input form: labelled controls grouped in fieldsets. */
export function CalculatorForm({ onSubmit, loading }: Props) {
  const [input, setInput] = useState<CarbonInput>(emptyInput);

  // Type-safe section updaters — each patch is checked against the schema.
  const patchTransport = (patch: Partial<CarbonInput["transport"]>) =>
    setInput((p) => ({ ...p, transport: { ...p.transport, ...patch } }));
  const patchHome = (patch: Partial<CarbonInput["home"]>) =>
    setInput((p) => ({ ...p, home: { ...p.home, ...patch } }));
  const patchConsumption = (patch: Partial<CarbonInput["consumption"]>) =>
    setInput((p) => ({ ...p, consumption: { ...p.consumption, ...patch } }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(input);
  };

  return (
    <form className="card" onSubmit={handleSubmit} aria-labelledby="calc-heading">
      <h2 id="calc-heading">Estimate your annual footprint</h2>

      <fieldset>
        <legend>Transport</legend>
        <NumberField
          id="car_km"
          label="Car distance per week (km)"
          max={MAX_KM_WEEK}
          value={input.transport.car_km_per_week}
          onChange={(v) => patchTransport({ car_km_per_week: v })}
        />
        <div className="field">
          <label htmlFor="car_fuel">Car fuel type</label>
          <select
            id="car_fuel"
            value={input.transport.car_fuel}
            onChange={(e) => patchTransport({ car_fuel: e.target.value as CarFuel })}
          >
            {FUEL_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <NumberField
          id="transit_km"
          label="Public transit per week (km)"
          max={MAX_KM_WEEK}
          value={input.transport.public_transit_km_per_week}
          onChange={(v) => patchTransport({ public_transit_km_per_week: v })}
        />
        <NumberField
          id="short_flights"
          label="Short-haul flights per year"
          max={MAX_FLIGHTS}
          step={1}
          value={input.transport.short_haul_flights_per_year}
          onChange={(v) => patchTransport({ short_haul_flights_per_year: v })}
        />
        <NumberField
          id="long_flights"
          label="Long-haul flights per year"
          max={MAX_FLIGHTS}
          step={1}
          value={input.transport.long_haul_flights_per_year}
          onChange={(v) => patchTransport({ long_haul_flights_per_year: v })}
        />
      </fieldset>

      <fieldset>
        <legend>Home energy</legend>
        <NumberField
          id="electricity"
          label="Electricity per month (kWh)"
          max={MAX_KWH_MONTH}
          value={input.home.electricity_kwh_per_month}
          onChange={(v) => patchHome({ electricity_kwh_per_month: v })}
        />
        <NumberField
          id="gas"
          label="Natural gas per month (kWh)"
          max={MAX_KWH_MONTH}
          value={input.home.natural_gas_kwh_per_month}
          onChange={(v) => patchHome({ natural_gas_kwh_per_month: v })}
        />
        <NumberField
          id="household"
          label="People in household"
          min={1}
          max={MAX_HOUSEHOLD}
          step={1}
          hint="Home energy is shared across this many people."
          value={input.home.household_size}
          onChange={(v) => patchHome({ household_size: v })}
        />
      </fieldset>

      <fieldset>
        <legend>Diet &amp; consumption</legend>
        <div className="field">
          <label htmlFor="diet">Diet</label>
          <select
            id="diet"
            value={input.diet}
            onChange={(e) => setInput((p) => ({ ...p, diet: e.target.value as DietType }))}
          >
            {DIET_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <NumberField
          id="goods"
          label="Goods spending per month (USD)"
          max={MAX_USD_MONTH}
          value={input.consumption.goods_spend_usd_per_month}
          onChange={(v) => patchConsumption({ goods_spend_usd_per_month: v })}
        />
        <NumberField
          id="waste"
          label="Landfill waste per week (kg)"
          max={MAX_WASTE_WEEK}
          value={input.consumption.waste_kg_per_week}
          onChange={(v) => patchConsumption({ waste_kg_per_week: v })}
        />
      </fieldset>

      <button className="btn" type="submit" disabled={loading} aria-busy={loading}>
        {loading ? "Calculating…" : "Calculate my footprint"}
      </button>
    </form>
  );
}
