import { useCallback, useEffect, useRef, useState } from "react";
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

  // Abort in-flight requests if the component unmounts or a new request starts.
  const abortRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      abortRef.current?.abort();
    };
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const history = await api.listEntries(deviceId);
      if (mountedRef.current) {
        setEntries(history);
      }
    } catch {
      // History is non-critical; fail silently rather than blocking the app.
    }
  }, [deviceId]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  /** Calculate the footprint and fetch personalized insights for the input. */
  const calculate = useCallback(async (input: CarbonInput) => {
    // Cancel any previous calculation/insights request.
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    setStatus("");
    try {
      const [calc, ins] = await Promise.all([api.calculate(input), api.getInsights(input)]);
      if (!mountedRef.current || controller.signal.aborted) return;
      setResult(calc);
      setInsights(ins);
      setLastInput(input);
      setStatus("Your footprint results and personalized insights are ready below.");
    } catch (err) {
      if (!mountedRef.current || controller.signal.aborted) return;
      const message =
        err instanceof api.ApiError
          ? err.message
          : "Something went wrong calculating your footprint. Please try again.";
      setError(message);
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  /** Persist the latest result to the device's history and refresh it. */
  const save = useCallback(async () => {
    if (!result || !lastInput) return;
    setSaving(true);
    setError(null);
    try {
      await api.saveEntry(deviceId, lastInput, result);
      await loadHistory();
      if (!mountedRef.current) return;
      setStatus("Entry saved to your history.");
    } catch (err) {
      if (!mountedRef.current) return;
      const message =
        err instanceof api.ApiError ? err.message : "Could not save this entry. Please try again.";
      setError(message);
    } finally {
      if (mountedRef.current) {
        setSaving(false);
      }
    }
  }, [deviceId, result, lastInput, loadHistory]);

  return { result, insights, entries, loading, saving, error, status, calculate, save };
}
