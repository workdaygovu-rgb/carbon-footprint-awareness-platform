import type { Entry } from "../lib/types";
import { formatDate, formatTonnes } from "../lib/format";

interface Props {
  entries: Entry[];
}

/** Tracking history: shows past footprint snapshots so users see their trend. */
export function HistoryPanel({ entries }: Props) {
  if (entries.length === 0) {
    return (
      <section className="card" aria-labelledby="history-heading">
        <h2 id="history-heading">Your history</h2>
        <p>No saved entries yet. Calculate and save a footprint to start tracking your progress.</p>
      </section>
    );
  }

  const latest = entries[0].result.total_annual_tonnes;
  const previous = entries.length > 1 ? entries[1].result.total_annual_tonnes : null;
  const trend = previous === null ? null : latest - previous;

  return (
    <section className="card" aria-labelledby="history-heading">
      <h2 id="history-heading">Your history</h2>

      {trend !== null && (
        <p aria-live="polite">
          {trend < 0 ? (
            <span className="under">
              ▼ Down {formatTonnes(Math.abs(trend))} since your last entry.
            </span>
          ) : trend > 0 ? (
            <span className="over">▲ Up {formatTonnes(trend)} since your last entry.</span>
          ) : (
            <span>No change since your last entry.</span>
          )}
        </p>
      )}

      <table className="history">
        <caption className="visually-hidden">Saved footprint entries, newest first</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Total (t CO₂e / year)</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e) => (
            <tr key={e.id}>
              <th scope="row">{formatDate(e.created_at)}</th>
              <td>{formatTonnes(e.result.total_annual_tonnes)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
