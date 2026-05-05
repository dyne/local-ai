export function shouldDisplayTranscriptLine(value) {
  const line = String(value || "").trim();
  if (!line) {
    return false;
  }
  return !(line.startsWith("[server error]") || line.startsWith("[error]") || line.startsWith("[debug]"));
}
