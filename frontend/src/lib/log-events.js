export const LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"];

function normalizedLevel(value) {
  const level = String(value || "INFO").trim().toUpperCase();
  return LOG_LEVELS.includes(level) ? level : "INFO";
}

function coerceLegacyMessage(raw) {
  const value = String(raw || "").trim();
  if (value.startsWith("[server error]")) {
    return { level: "ERROR", source: "voice.runtime", message: value.slice(14).trim() };
  }
  if (value.startsWith("[error]")) {
    return { level: "ERROR", source: "voice.runtime", message: value.slice(7).trim() };
  }
  return { level: "INFO", source: "voice.runtime", message: value };
}

export function parseLogEvent(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    const legacy = coerceLegacyMessage(input);
    return {
      id: `legacy:${legacy.message}`,
      timestamp: new Date().toISOString(),
      ...legacy,
      details: [],
      context: {},
      notification: legacy.level === "ERROR",
    };
  }

  const source = String(input.source || "app").trim() || "app";
  const message = String(input.message || "").trim();
  const details = Array.isArray(input.details)
    ? input.details.map((item) => String(item))
    : [];
  const context = input.context && typeof input.context === "object" ? input.context : {};
  const level = normalizedLevel(input.level);
  const timestamp = typeof input.timestamp === "string" && input.timestamp ? input.timestamp : new Date().toISOString();
  const id = typeof input.id === "string" && input.id ? input.id : `${source}:${timestamp}:${message}`;

  return {
    id,
    timestamp,
    level,
    source,
    message,
    details,
    context,
    notification: Boolean(input.notification ?? level === "ERROR"),
  };
}

export function eventSearchText(event) {
  const contextText = Object.entries(event.context || {})
    .map(([key, value]) => `${key}:${String(value)}`)
    .join(" ");
  return `${event.source} ${event.level} ${event.message} ${(event.details || []).join(" ")} ${contextText}`
    .toLowerCase()
    .trim();
}
