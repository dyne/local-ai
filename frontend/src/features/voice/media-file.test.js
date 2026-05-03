import { describe, expect, it } from "vitest";

import { pickFirstMediaFile } from "./media-file";

describe("pickFirstMediaFile", () => {
  it("picks the first audio/video mime item", () => {
    const file = pickFirstMediaFile([
      { name: "a.txt", type: "text/plain" },
      { name: "b.webm", type: "video/webm" },
    ]);
    expect(file?.name).toBe("b.webm");
  });

  it("falls back to extension matching", () => {
    const file = pickFirstMediaFile([{ name: "speech.wav", type: "" }]);
    expect(file?.name).toBe("speech.wav");
  });

  it("returns null when no supported file exists", () => {
    expect(pickFirstMediaFile([{ name: "x.txt", type: "text/plain" }])).toBeNull();
  });
});

