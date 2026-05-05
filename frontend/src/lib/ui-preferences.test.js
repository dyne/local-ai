import { describe, expect, it } from "vitest";

import { readUiPreferences, writeLeftRailExpanded, writeRightLogRailExpanded } from "./ui-preferences";

function storageMock() {
  const data = new Map();
  return {
    getItem: (k) => (data.has(k) ? data.get(k) : null),
    setItem: (k, v) => data.set(k, String(v)),
  };
}

describe("ui preferences", () => {
  it("reads defaults", () => {
    expect(readUiPreferences(storageMock())).toEqual({ leftRailExpanded: true, rightLogRailExpanded: false });
  });

  it("persists rail states", () => {
    const storage = storageMock();
    writeLeftRailExpanded(false, storage);
    writeRightLogRailExpanded(true, storage);
    expect(readUiPreferences(storage)).toEqual({ leftRailExpanded: false, rightLogRailExpanded: true });
  });
});
