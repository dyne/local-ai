export function pickFirstMediaFile(filesLike) {
  const files = Array.from(filesLike ?? []);
  for (const file of files) {
    if (!file || typeof file.name !== "string") {
      continue;
    }
    const type = (file.type || "").toLowerCase();
    if (type.startsWith("audio/") || type.startsWith("video/")) {
      return file;
    }
    const lowerName = file.name.toLowerCase();
    if (/\.(wav|mp3|m4a|ogg|webm|mp4|mov|mkv|flac|aac)$/.test(lowerName)) {
      return file;
    }
  }
  return null;
}

