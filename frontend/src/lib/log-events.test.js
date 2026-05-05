import { describe, expect, it } from "vitest";

import { eventSearchText, parseLogEvent } from "./log-events";

describe("parseLogEvent", () => {
  it("keeps structured event fields", () => {
    const parsed = parseLogEvent({
      id: "evt-1",
      timestamp: "2026-05-05T10:00:00.000Z",
      level: "warning",
      source: "documents.index",
      message: "Index completed",
      details: ["10 files"],
      context: { source_id: "abc" },
      notification: false,
    });

    expect(parsed).toEqual({
      id: "evt-1",
      timestamp: "2026-05-05T10:00:00.000Z",
      level: "WARNING",
      source: "documents.index",
      message: "Index completed",
      details: ["10 files"],
      context: { source_id: "abc" },
      notification: false,
    });
  });

  it("converts legacy server error text into ERROR event", () => {
    const parsed = parseLogEvent("[server error] Audio stream failed");

    expect(parsed.level).toBe("ERROR");
    expect(parsed.source).toBe("voice.runtime");
    expect(parsed.message).toBe("Audio stream failed");
  });

  it("returns fallback INFO event for malformed input", () => {
    const parsed = parseLogEvent(null);

    expect(parsed.level).toBe("INFO");
    expect(parsed.source).toBe("voice.runtime");
  });
});

describe("eventSearchText", () => {
  it("includes message details and context", () => {
    const text = eventSearchText(
      parseLogEvent({
        level: "ERROR",
        source: "voice.upload",
        message: "Upload failed",
        details: ["bad mime"],
        context: { source_name: "a.wav" },
      }),
    );

    expect(text).toContain("upload failed");
    expect(text).toContain("bad mime");
    expect(text).toContain("source_name:a.wav");
  });
});
