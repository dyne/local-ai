const FALLBACK_ROLES = Object.freeze([
  {
    id: "voice",
    label: "Voice",
    summary: "Realtime microphone transcription with local Whisper.",
    status: "available",
    route: "voice",
    primary_action: "Start recording",
  },
  {
    id: "documents",
    label: "Documents",
    summary: "Document workspace and ingestion flow.",
    status: "planned",
    route: "documents",
    primary_action: null,
  },
  {
    id: "ocr",
    label: "OCR",
    summary: "Image and page text extraction workflows.",
    status: "planned",
    route: "ocr",
    primary_action: null,
  },
]);

function normalizeRole(value) {
  if (!value || typeof value !== "object") {
    return null;
  }
  const role = {
    id: typeof value.id === "string" ? value.id : "",
    label: typeof value.label === "string" ? value.label : "",
    summary: typeof value.summary === "string" ? value.summary : "",
    status: typeof value.status === "string" ? value.status : "",
    route: typeof value.route === "string" ? value.route : "",
    primary_action: typeof value.primary_action === "string" ? value.primary_action : null,
  };
  if (!role.id || !role.label || !role.route || !role.status) {
    return null;
  }
  return role;
}

export function parseRolesResponse(payload) {
  const source = Array.isArray(payload?.roles) ? payload.roles : [];
  const roles = source.map(normalizeRole).filter(Boolean);
  return roles.length > 0 ? roles : [...FALLBACK_ROLES];
}

export function fallbackRoles() {
  return [...FALLBACK_ROLES];
}

