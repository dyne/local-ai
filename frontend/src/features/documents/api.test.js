import { describe, expect, it } from "vitest";

import { summarizeHealth } from "./api";

describe("documents api helpers", () => {
  it("summarizes status and error fields", () => {
    expect(summarizeHealth({ status: "ready", error: "" })).toEqual({ status: "ready", error: "" });
  });

  it("handles missing values", () => {
    expect(summarizeHealth(null)).toEqual({ status: "unknown", error: "" });
  });
});
