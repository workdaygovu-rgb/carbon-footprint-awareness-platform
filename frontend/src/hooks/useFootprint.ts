import { useCallback, useEffect, useState } from "react";
import * as api from "../lib/api";
import { getDeviceId } from "../lib/deviceId";
import type { CarbonInput, Entry, FootprintResult, InsightsResponse } from "../lib/types";

/**
 * Owns all asynchronous application state: footprint calculation, insights,
 * saving entries, and history loading. Components stay presentational; this
 * hook is the single place that talks to the API.
 *
 * `status` carries polite screen-reader announcements (rendered in a
 * `role="status"` live region) so async outcomes are audible, not just visible.
 */
export function useFootprint() {
  const [deviceId] = useState(getDeviceId);
  const [result, setResult] = useState<FootprintResult | null>(null);
  const [lastInput, setLastInput] = useState<CarbonInput | null>(null);
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");

  const loadHistory = useCallback(async () => {
    try {
      setEntries(await api.listEntries(deviceId));
    } catch {
      // History is non-critical; fail silently rather than blocking the app.
    }
  }, [deviceId]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  /** Calculate the footprint and fetch personalized insights for the input. */
  const calculate = async (input: CarbonInput) => {
    setLoading(true);
    setError(null);
    setStatus("");
    try {
      const [calc, ins] = await Promise.all([api.calculate(input), api.getInsights(input)]);
      setResult(calc);
      setInsights(ins);
      setLastInput(input);
      setStatus("Your footprint results and personalized insights are ready below.");
    } catch {
      setError("Something went wrong calculating your footprint. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  /** Persist the latest result to the device's history and refresh it. */
  const save = async () => {
    if (!result || !lastInput) return;
    setSaving(true);
    setError(null);
    try {
      await api.saveEntry(deviceId, lastInput, result);
      await loadHistory();
      setStatus("Entry saved to your history.");
    } catch {
      setError("Could not save this entry. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return { result, insights, entries, loading, saving, error, status, calculate, save };
}
