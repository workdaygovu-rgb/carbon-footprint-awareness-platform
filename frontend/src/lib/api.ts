// Typed client for the backend API. Same-origin in production; proxied in dev.

import type { CarbonInput, Entry, FootprintResult, InsightsResponse } from "./types";

/** POST a JSON body and parse the JSON response, throwing on non-2xx status. */
async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`Request to ${path} failed (${res.status})`);
  }
  return (await res.json()) as T;
}

/** Compute the annual footprint breakdown for the given lifestyle inputs. */
export function calculate(input: CarbonInput): Promise<FootprintResult> {
  return postJson<FootprintResult>("/api/calculate", input);
}

/** Fetch personalized reduction advice (Gemini with rule-based fallback). */
export function getInsights(input: CarbonInput): Promise<InsightsResponse> {
  return postJson<InsightsResponse>("/api/insights", input);
}

/** Save a footprint snapshot to the device's anonymous history. */
export function saveEntry(
  deviceId: string,
  input: CarbonInput,
  result: FootprintResult,
): Promise<Entry> {
  return postJson<Entry>("/api/entries", {
    device_id: deviceId,
    input,
    result,
  });
}

/** List the device's saved entries, newest first. */
export async function listEntries(deviceId: string): Promise<Entry[]> {
  const res = await fetch(`/api/entries/${encodeURIComponent(deviceId)}`);
  if (!res.ok) {
    throw new Error(`Failed to load history (${res.status})`);
  }
  return (await res.json()) as Entry[];
}
