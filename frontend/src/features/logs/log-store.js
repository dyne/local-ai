import { parseLogEvent, eventSearchText } from "../../lib/log-events";

const DEFAULT_MAX_HISTORY = 500;

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export function createLogStore({ maxHistory = DEFAULT_MAX_HISTORY, fetchImpl = fetch, eventSourceFactory = (url) => new EventSource(url) } = {}) {
  let events = [];
  const listeners = new Set();
  let source = null;

  function notify() {
    for (const listener of listeners) {
      listener(events);
    }
  }

  function upsert(input) {
    const event = parseLogEvent(input);
    const index = events.findIndex((item) => item.id === event.id);
    if (index >= 0) {
      events = [...events.slice(0, index), event, ...events.slice(index + 1)];
    } else {
      events = [...events, event];
      const limit = clamp(maxHistory, 1, 5000);
      if (events.length > limit) {
        events = events.slice(events.length - limit);
      }
    }
    notify();
    return event;
  }

  function clearView() {
    events = [];
    notify();
  }

  function subscribe(listener) {
    listeners.add(listener);
    listener(events);
    return () => listeners.delete(listener);
  }

  async function loadHistory({ limit = 200, level = "", source: sourceFilter = "", q = "" } = {}) {
    const query = new URLSearchParams();
    query.set("limit", String(clamp(limit, 1, 500)));
    if (level) query.set("level", level);
    if (sourceFilter) query.set("source", sourceFilter);
    if (q) query.set("q", q);
    const response = await fetchImpl(`/api/app/logs?${query.toString()}`);
    if (!response.ok) {
      throw new Error(`Failed to load logs: ${response.status}`);
    }
    const payload = await response.json();
    const loaded = Array.isArray(payload?.events) ? payload.events : [];
    for (const item of loaded) {
      upsert(item);
    }
  }

  function connectLive() {
    if (source) {
      return () => source?.close();
    }
    source = eventSourceFactory("/api/app/logs/events");
    source.onmessage = (event) => {
      try {
        upsert(JSON.parse(event.data));
      } catch {
        upsert(event.data);
      }
    };
    source.onerror = () => {};
    return () => {
      source?.close();
      source = null;
    };
  }

  function filterEvents({ level = "", source: sourceFilter = "", query = "" } = {}) {
    const normalizedLevel = level.trim().toUpperCase();
    const normalizedSource = sourceFilter.trim();
    const normalizedQuery = query.trim().toLowerCase();
    return events.filter((event) => {
      if (normalizedLevel && event.level !== normalizedLevel) {
        return false;
      }
      if (normalizedSource && event.source !== normalizedSource) {
        return false;
      }
      if (!normalizedQuery) {
        return true;
      }
      return eventSearchText(event).includes(normalizedQuery);
    });
  }

  return {
    subscribe,
    upsert,
    clearView,
    loadHistory,
    connectLive,
    filterEvents,
    get events() {
      return events;
    },
  };
}
