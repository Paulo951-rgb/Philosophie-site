/* Historique local persistant (§12 du cahier des charges).
   Stockage par appareil : clé "gp.history", tri inversé chronologique,
   recherche full-text sur original + généré. */

const KEY = "gp.history";
const LIMIT = 300; // plan gratuit : les 300 dernières générations

function read() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function write(entries) {
  localStorage.setItem(KEY, JSON.stringify(entries.slice(0, LIMIT)));
}

export function addEntry(entry) {
  const entries = read();
  const item = {
    id: `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    ts: Date.now(),
    input: entry.input,
    text: entry.text,
    attribution: entry.attribution || null,
    params: entry.params,
    mode: entry.mode || "standard",
    fav: false,
    style_tag: (entry.params?.styles || []).join("+"),
  };
  entries.unshift(item);
  write(entries);
  return item;
}

export function updateEntry(id, patch) {
  const entries = read();
  const idx = entries.findIndex((e) => e.id === id);
  if (idx >= 0) {
    entries[idx] = { ...entries[idx], ...patch };
    write(entries);
    return entries[idx];
  }
  return null;
}

export function removeEntry(id) {
  const entries = read().filter((e) => e.id !== id);
  write(entries);
}

export function clearAll() {
  write([]);
}

export function list(onlyFav = false) {
  const entries = read();
  return onlyFav ? entries.filter((e) => e.fav) : entries;
}

export function search(query, onlyFav = false, style = "") {
  const q = (query || "").toLowerCase();
  return list(onlyFav).filter((e) => {
    if (style && !e.style_tag.includes(style)) return false;
    if (!q) return true;
    return (
      e.input.toLowerCase().includes(q) ||
      e.text.toLowerCase().includes(q)
    );
  });
}

export function stylesUsed() {
  const set = new Set();
  for (const e of read()) {
    (e.style_tag || "").split("+").forEach((s) => set.add(s));
  }
  set.delete("");
  return [...set].sort();
}
