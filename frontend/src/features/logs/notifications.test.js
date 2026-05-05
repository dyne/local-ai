import { describe, expect, it } from "vitest";

import { upsertErrorNotification } from "./notifications";

describe("upsertErrorNotification", () => {
  it("ignores non-error events", () => {
    expect(upsertErrorNotification([], { level: "INFO" })).toEqual([]);
  });

  it("deduplicates by source and message", () => {
    const first = upsertErrorNotification([], { level: "ERROR", source: "voice.runtime", message: "boom", timestamp: "t1" });
    const second = upsertErrorNotification(first, { level: "ERROR", source: "voice.runtime", message: "boom", timestamp: "t2" });

    expect(second).toHaveLength(1);
    expect(second[0].count).toBe(2);
    expect(second[0].timestamp).toBe("t2");
  });

  it("caps visible notifications", () => {
    let list = [];
    for (let i = 0; i < 5; i += 1) {
      list = upsertErrorNotification(list, { level: "ERROR", source: "app", message: `e${i}`, timestamp: `t${i}` }, { maxVisible: 3 });
    }
    expect(list).toHaveLength(3);
    expect(list[0].message).toBe("e4");
  });
});
