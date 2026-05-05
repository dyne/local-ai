import { describe, expect, it } from "vitest";

import { isLikelyAbsolutePath, normalizeLocalMediaPath } from "./local-media-path";

describe("local-media-path", () => {
  it("normalizes whitespace", () => {
    expect(normalizeLocalMediaPath("  C:\\a\\b.wav  ")).toBe("C:\\a\\b.wav");
  });

  it("checks likely absolute paths", () => {
    expect(isLikelyAbsolutePath("C:\\a\\b.wav")).toBe(true);
    expect(isLikelyAbsolutePath("/tmp/a.wav")).toBe(true);
    expect(isLikelyAbsolutePath("relative\\a.wav")).toBe(false);
  });
});
