// Display formatting helpers.

/** Format a kg CO₂e amount for display, e.g. `1,235 kg`. */
export function formatKg(kg: number): string {
  return `${kg.toLocaleString(undefined, { maximumFractionDigits: 0 })} kg`;
}

/** Format a tonnes CO₂e amount for display, e.g. `2.5 t`. */
export function formatTonnes(tonnes: number): string {
  return `${tonnes.toLocaleString(undefined, { maximumFractionDigits: 2 })} t`;
}

const CATEGORY_LABELS: Record<string, string> = {
  transport: "Transport",
  home: "Home energy",
  diet: "Diet",
  consumption: "Goods & waste",
};

/** Map an emission category key to its friendly label (falls back to the key). */
export function categoryLabel(key: string): string {
  return CATEGORY_LABELS[key] ?? key;
}

/** Format an ISO timestamp in the user's locale; pass through invalid input. */
export function formatDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
}
