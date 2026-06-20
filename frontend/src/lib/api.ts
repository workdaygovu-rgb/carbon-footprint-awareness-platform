// Typed client for the backend API. Same-origin in production; proxied in dev.

import type { CarbonInput, Entry, FootprintResult, InsightsResponse } from "./types";

/** Distinct error class so callers can distinguish API failures from bugs. */
export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions {
  signal?: AbortSignal;
}

/** POST a JSON body and parse the JSON response, throwing on non-2xx status. */
async function postJson<T>(path: string, body: unknown, options: RequestOptions = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: options.signal,
    });
  } catch {
    throw new ApiError("Network error — please check your connection.", 0);
  }

  if (!res.ok) {
    let detail: string | undefined;
    try {
      const errBody = (await res.json()) as { detail?: string };
      detail = errBody.detail;
    } catch {
      // Ignore malformed error bodies; fall back to status-only message.
    }
    const message = detail
      ? `Request to ${path} failed (${res.status}): ${detail}`
      : `Request to ${path} failed (${res.status})`;
    throw new ApiError(message, res.status);
  }

  try {
    return (await res.json()) as T;
  } catch {
    throw new ApiError(`Invalid JSON response from ${path}`, res.status);
  }
}

/** Compute the annual footprint breakdown for the given lifestyle inputs. */
export function calculate(input: CarbonInput, options?: RequestOptions): Promise<FootprintResult> {
  return postJson<FootprintResult>("/api/calculate", input, options);
}

/** Fetch personalized reduction advice (Gemini with rule-based fallback). */
export function getInsights(
  input: CarbonInput,
  options?: RequestOptions,
): Promise<InsightsResponse> {
  return postJson<InsightsResponse>("/api/insights", input, options);
}

/** Save a footprint snapshot to the device's anonymous history. */
export function saveEntry(
  deviceId: string,
  input: CarbonInput,
  result: FootprintResult,
  options?: RequestOptions,
): Promise<Entry> {
  return postJson<Entry>(
    "/api/entries",
    {
      device_id: deviceId,
      input,
      result,
    },
    options,
  );
}

/** List the device's saved entries, newest first. */
export async function listEntries(
  deviceId: string,
  options: RequestOptions = {},
): Promise<Entry[]> {
  let res: Response;
  try {
    res = await fetch(`/api/entries/${encodeURIComponent(deviceId)}`, {
      signal: options.signal,
    });
  } catch {
    throw new ApiError("Network error — please check your connection.", 0);
  }

  if (!res.ok) {
    throw new ApiError(`Failed to load history (${res.status})`, res.status);
  }

  try {
    return (await res.json()) as Entry[];
  } catch {
    throw new ApiError("Invalid history response from server", res.status);
  }
}
