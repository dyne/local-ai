import { describe, expect, it, vi } from "vitest";

import { createLogStore } from "./log-store";

function okJson(value) {
  return Promise.resolve({ ok: true, json: async () => value });
}

describe("createLogStore", () => {
  it("merges by id", () => {
    const store = createLogStore({ fetchImpl: vi.fn() });

    store.upsert({ id: "evt-1", level: "INFO", source: "app", message: "a" });
    store.upsert({ id: "evt-1", level: "ERROR", source: "app", message: "b" });

    expect(store.events).toHaveLength(1);
    expect(store.events[0].level).toBe("ERROR");
  });

  it("caps history size", () => {
    const store = createLogStore({ maxHistory: 2, fetchImpl: vi.fn() });
    store.upsert({ id: "1", level: "INFO", source: "app", message: "1" });
    store.upsert({ id: "2", level: "INFO", source: "app", message: "2" });
    store.upsert({ id: "3", level: "INFO", source: "app", message: "3" });

    expect(store.events.map((item) => item.id)).toEqual(["2", "3"]);
  });

  it("loads history from backend", async () => {
    const fetchImpl = vi.fn().mockImplementation(() => okJson({ events: [{ id: "evt-1", level: "INFO", source: "app", message: "loaded" }] }));
    const store = createLogStore({ fetchImpl });

    await store.loadHistory({ limit: 50 });

    expect(fetchImpl).toHaveBeenCalledOnce();
    expect(store.events).toHaveLength(1);
  });

  it("filters by level source and query", () => {
    const store = createLogStore({ fetchImpl: vi.fn() });
    store.upsert({ id: "1", level: "INFO", source: "app", message: "ready" });
    store.upsert({ id: "2", level: "ERROR", source: "voice.upload", message: "upload failed", details: ["mime"] });

    expect(store.filterEvents({ level: "ERROR" }).map((item) => item.id)).toEqual(["2"]);
    expect(store.filterEvents({ source: "voice.upload" }).map((item) => item.id)).toEqual(["2"]);
    expect(store.filterEvents({ query: "mime" }).map((item) => item.id)).toEqual(["2"]);
  });

  it("ingests SSE message payload", () => {
    const events = [];
    const eventSourceFactory = vi.fn().mockImplementation(() => {
      const source = { onmessage: null, onerror: null, close: vi.fn() };
      events.push(source);
      return source;
    });
    const store = createLogStore({ fetchImpl: vi.fn(), eventSourceFactory });

    store.connectLive();
    events[0].onmessage({ data: JSON.stringify({ id: "evt-9", level: "ERROR", source: "app", message: "boom" }) });

    expect(store.events[0].id).toBe("evt-9");
  });
});
