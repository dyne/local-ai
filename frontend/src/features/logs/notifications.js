export function upsertErrorNotification(list, event, { maxVisible = 4 } = {}) {
  if (!event || event.level !== "ERROR") {
    return list;
  }
  const key = `${event.source}:${event.message}`;
  const existing = list.find((item) => item.key === key);
  if (existing) {
    return list.map((item) => (item.key === key ? { ...item, count: item.count + 1, timestamp: event.timestamp } : item));
  }
  return [{ key, source: event.source, message: event.message, timestamp: event.timestamp, count: 1 }, ...list].slice(0, maxVisible);
}
