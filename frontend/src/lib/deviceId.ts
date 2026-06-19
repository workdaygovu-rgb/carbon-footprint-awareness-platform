// Anonymous device identity: a random id stored in localStorage. This lets us
// persist a user's history in Firestore without any login or personal data.

const STORAGE_KEY = "carbon_device_id";

function generateId(): string {
  // Prefer the platform CSPRNG; fall back to a timestamp-based id if absent.
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `dev-${crypto.randomUUID().replace(/-/g, "")}`;
  }
  return `dev-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
}

/** Return the persistent anonymous device id, creating one if needed. */
export function getDeviceId(): string {
  try {
    const existing = localStorage.getItem(STORAGE_KEY);
    if (existing) return existing;
    const id = generateId();
    localStorage.setItem(STORAGE_KEY, id);
    return id;
  } catch {
    // localStorage unavailable (e.g. privacy mode) — use an ephemeral id.
    return generateId();
  }
}
