export function normalizeLocalMediaPath(value) {
  return String(value || "").trim();
}

export function isLikelyAbsolutePath(value) {
  const path = normalizeLocalMediaPath(value);
  if (!path) return false;
  return /^[a-zA-Z]:\\/.test(path) || path.startsWith("/") || path.startsWith("\\\\");
}
