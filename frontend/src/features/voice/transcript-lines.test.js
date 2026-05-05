import { describe, expect, it } from "vitest";

import { shouldDisplayTranscriptLine } from "./transcript-lines";

describe("shouldDisplayTranscriptLine", () => {
  it("keeps transcript and upload content", () => {
    expect(shouldDisplayTranscriptLine("Hello there")).toBe(true);
    expect(shouldDisplayTranscriptLine("[upload:a.wav] done")).toBe(true);
  });

  it("hides operational error/debug lines", () => {
    expect(shouldDisplayTranscriptLine("[server error] boom")).toBe(false);
    expect(shouldDisplayTranscriptLine("[error] boom")).toBe(false);
    expect(shouldDisplayTranscriptLine("[debug] trace")).toBe(false);
  });
});
