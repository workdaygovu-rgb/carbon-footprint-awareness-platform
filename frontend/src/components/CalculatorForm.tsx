import { useState } from "react";
import { type CarbonInput, type CarFuel, type DietType, emptyInput } from "../lib/types";
import { NumberField } from "./NumberField";

/** Convert a raw string to a known CarFuel, falling back to petrol on drift. */
function toCarFuel(value: string): CarFuel {
  const known: CarFuel[] = ["petrol", "diesel", "hybrid", "electric"];
  return known.includes(value as CarFuel) ? (value as CarFuel) : "petrol";
}

/** Convert a raw string to a known DietType, falling back to medium_meat. */
function toDietType(value: string): DietType {
  const known: DietType[] = [
    "heavy_meat", "medium_meat", "low_meat", "pescatarian", "vegetarian", "vegan",
  ];
  return known.includes(value as DietType) ? (value as DietType) : "medium_meat";
}

interface Props {
  onSubmit: (input: CarbonInput) => void;
  loading: boolean;
}

// Input ceilings mirror the backend Pydantic bounds (app/models.py).
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

// ── Sub-components ──────────────────────────────────────────────────────────

interface SectionProps<T> {
  data: T;
  onChange: (patch: Partial<T>) => void;
}

function TransportSection({ data, onChange }: SectionProps<CarbonInput["transport"]>) {
  return (
    <fieldset>
      <legend>Transport</legend>
      <NumberField id="car_km" label="Car distance per week (km)" max={MAX_KM_WEEK} value={data.car_km_per_week} onChange={(v) => onChange({ car_km_per_week: v })} />
      <div className="field">
        <label htmlFor="car_fuel">Car fuel type</label>
        <select id="car_fuel" value={data.car_fuel} onChange={(e) => onChange({ car_fuel: toCarFuel(e.target.value) })}>
          {FUEL_OPTIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
        </select>
      </div>
      <NumberField id="transit_km" label="Public transit per week (km)" max={MAX_KM_WEEK} value={data.public_transit_km_per_week} onChange={(v) => onChange({ public_transit_km_per_week: v })} />
      <NumberField id="short_flights" label="Short-haul flights per year" max={MAX_FLIGHTS} step={1} value={data.short_haul_flights_per_year} onChange={(v) => onChange({ short_haul_flights_per_year: v })} />
      <NumberField id="long_flights" label="Long-haul flights per year" max={MAX_FLIGHTS} step={1} value={data.long_haul_flights_per_year} onChange={(v) => onChange({ long_haul_flights_per_year: v })} />
    </fieldset>
  );
}

function HomeSection({ data, onChange }: SectionProps<CarbonInput["home"]>) {
  return (
    <fieldset>
      <legend>Home energy</legend>
      <NumberField id="electricity" label="Electricity per month (kWh)" max={MAX_KWH_MONTH} value={data.electricity_kwh_per_month} onChange={(v) => onChange({ electricity_kwh_per_month: v })} />
      <NumberField id="gas" label="Natural gas per month (kWh)" max={MAX_KWH_MONTH} value={data.natural_gas_kwh_per_month} onChange={(v) => onChange({ natural_gas_kwh_per_month: v })} />
      <NumberField id="household" label="People in household" min={1} max={MAX_HOUSEHOLD} step={1} hint="Home energy is shared across this many people." value={data.household_size} onChange={(v) => onChange({ household_size: v })} />
    </fieldset>
  );
}

interface ConsumptionSectionProps {
  diet: DietType;
  consumption: CarbonInput["consumption"];
  onDietChange: (diet: DietType) => void;
  onConsumptionChange: (patch: Partial<CarbonInput["consumption"]>) => void;
}

function ConsumptionSection({ diet, consumption, onDietChange, onConsumptionChange }: ConsumptionSectionProps) {
  return (
    <fieldset>
      <legend>Diet &amp; consumption</legend>
      <div className="field">
        <label htmlFor="diet">Diet</label>
        <select id="diet" value={diet} onChange={(e) => onDietChange(toDietType(e.target.value))}>
          {DIET_OPTIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
        </select>
      </div>
      <NumberField id="goods" label="Goods spending per month (USD)" max={MAX_USD_MONTH} value={consumption.goods_spend_usd_per_month} onChange={(v) => onConsumptionChange({ goods_spend_usd_per_month: v })} />
      <NumberField id="waste" label="Landfill waste per week (kg)" max={MAX_WASTE_WEEK} value={consumption.waste_kg_per_week} onChange={(v) => onConsumptionChange({ waste_kg_per_week: v })} />
    </fieldset>
  );
}

// ── Main component ──────────────────────────────────────────────────────────

/** Accessible footprint input form: labelled controls grouped in fieldsets. */
export function CalculatorForm({ onSubmit, loading }: Props) {
  const [input, setInput] = useState<CarbonInput>(emptyInput);

  const patchTransport = (patch: Partial<CarbonInput["transport"]>) =>
    setInput((p) => ({ ...p, transport: { ...p.transport, ...patch } }));
  const patchHome = (patch: Partial<CarbonInput["home"]>) =>
    setInput((p) => ({ ...p, home: { ...p.home, ...patch } }));
  const patchConsumption = (patch: Partial<CarbonInput["consumption"]>) =>
    setInput((p) => ({ ...p, consumption: { ...p.consumption, ...patch } }));

  return (
    <form className="card" onSubmit={(e) => { e.preventDefault(); onSubmit(input); }} aria-labelledby="calc-heading">
      <h2 id="calc-heading">Estimate your annual footprint</h2>

      <TransportSection data={input.transport} onChange={patchTransport} />
      <HomeSection data={input.home} onChange={patchHome} />
      <ConsumptionSection diet={input.diet} consumption={input.consumption} onDietChange={(v) => setInput((p) => ({ ...p, diet: v }))} onConsumptionChange={patchConsumption} />

      <button className="btn" type="submit" disabled={loading} aria-busy={loading}>
        {loading ? "Calculating…" : "Calculate my footprint"}
      </button>
    </form>
  );
}
