import type { FootprintResult } from "../lib/types";
import { categoryLabel, formatKg, formatTonnes } from "../lib/format";

interface Props {
  result: FootprintResult;
}

/**
 * Shows the total footprint and a per-category bar chart. The chart is built
 * from semantic markup with text values beside each bar, so it is fully
 * understandable without color or vision (no canvas, no color-only encoding).
 */
export function ResultBreakdown({ result }: Props) {
  const entries = Object.entries(result.breakdown_kg);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  const overTarget = result.comparison.ratio_to_sustainable_target > 1;

  return (
    <section className="card" aria-labelledby="result-heading">
      <h2 id="result-heading">Your estimated footprint</h2>

      <p>
        <span className={`total ${overTarget ? "over" : "under"}`}>
          {overTarget ? "↑ " : "↓ "}
          {formatTonnes(result.total_annual_tonnes)} CO₂e
        </span>{" "}
        per year
        <span className="visually-hidden">
          {overTarget ? " — above the sustainable target" : " — at or below the sustainable target"}
        </span>
      </p>
      <p>
        That is <strong>{result.comparison.ratio_to_sustainable_target.toFixed(1)}×</strong> the
        sustainable target ({formatTonnes(result.comparison.sustainable_target_annual_kg / 1000)})
        and <strong>{result.comparison.ratio_to_global_average.toFixed(1)}×</strong> the global
        average.
      </p>

      <h3>Breakdown by category</h3>
      <div
        role="img"
        aria-label="Bar chart of emissions by category, values listed in the table below"
      >
        {entries.map(([key, value]) => (
          <div
            className="bar-row"
            key={key}
            aria-label={`${categoryLabel(key)}: ${formatKg(value)} kg CO₂e per year`}
          >
            <span>{categoryLabel(key)}</span>
            <span className="bar-track" aria-hidden="true">
              <span className="bar-fill" style={{ width: `${(value / max) * 100}%` }} />
            </span>
            <span>{formatKg(value)}</span>
          </div>
        ))}
      </div>

      {/* Accessible data table equivalent of the chart. */}
      <table className="history">
        <caption className="visually-hidden">Annual emissions by category in kg CO2e</caption>
        <thead>
          <tr>
            <th scope="col">Category</th>
            <th scope="col">kg CO₂e / year</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([key, value]) => (
            <tr key={key}>
              <th scope="row">{categoryLabel(key)}</th>
              <td>{formatKg(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
