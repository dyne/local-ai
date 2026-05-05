export async function getJson(url) {
  const response = await fetch(url);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload?.detail || `Request failed: ${response.status}`);
  }
  return payload;
}

export async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body?.detail || body?.message || `Request failed: ${response.status}`);
  }
  return body;
}

export function summarizeHealth(healthPayload) {
  const status = healthPayload?.status ?? "unknown";
  const error = healthPayload?.error ?? "";
  return { status, error };
}
