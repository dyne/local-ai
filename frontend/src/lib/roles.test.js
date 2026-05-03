import { describe, expect, it } from "vitest";

import { fallbackRoles, parseRolesResponse } from "./roles";

describe("roles", () => {
  it("returns fallback roles when payload is missing", () => {
    const roles = parseRolesResponse(null);
    expect(roles.map((item) => item.id)).toEqual(["voice", "documents", "ocr"]);
  });

  it("returns parsed roles when payload shape is valid", () => {
    const roles = parseRolesResponse({
      roles: [
        {
          id: "voice",
          label: "Voice",
          summary: "Test",
          status: "available",
          route: "voice",
          primary_action: "Start recording",
        },
      ],
    });
    expect(roles).toHaveLength(1);
    expect(roles[0].id).toBe("voice");
  });

  it("keeps fallback catalog stable", () => {
    const roles = fallbackRoles();
    expect(roles[1].status).toBe("planned");
    expect(roles[2].label).toBe("OCR");
  });
});

