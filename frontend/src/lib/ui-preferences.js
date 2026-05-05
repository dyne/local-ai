const KEY_LEFT = "ui.left_rail_expanded";
const KEY_RIGHT = "ui.right_log_rail_expanded";

function readBool(storage, key, fallback) {
  try {
    const raw = storage?.getItem(key);
    if (raw === "1") return true;
    if (raw === "0") return false;
    return fallback;
  } catch {
    return fallback;
  }
}

function writeBool(storage, key, value) {
  try {
    storage?.setItem(key, value ? "1" : "0");
  } catch {}
}

export function readUiPreferences(storage = globalThis?.localStorage) {
  return {
    leftRailExpanded: readBool(storage, KEY_LEFT, true),
    rightLogRailExpanded: readBool(storage, KEY_RIGHT, false),
  };
}

export function writeLeftRailExpanded(value, storage = globalThis?.localStorage) {
  writeBool(storage, KEY_LEFT, Boolean(value));
}

export function writeRightLogRailExpanded(value, storage = globalThis?.localStorage) {
  writeBool(storage, KEY_RIGHT, Boolean(value));
}
