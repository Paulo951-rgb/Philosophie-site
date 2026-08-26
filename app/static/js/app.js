import * as History from "./history.js";
import * as Cards from "./cards.js";

// ------------------------------------------------------------ état global

const state = {
  meta: null,
  settings: loadSettings(),
  current: null, // { input, text, attribution, params, mode, entryId }
  placeholders: ["J'ai faim.", "Le bus est en retard.",
                 "Mon chat dort toute la journée.", "Je dois acheter du pain."],
};

function loadSettings() {
  try {
    const raw = localStorage.getItem("gp.settings");
    return raw ? JSON.parse(raw) : { theme: "sombre", defaults: null };
  } catch {
    return { theme: "sombre", defaults: null };
  }
}
function saveSettings() {
  localStorage.setItem("gp.settings", JSON.stringify(state.settings));
}

// ------------------------------------------------------------ utilitaires

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

// Compteur du texte d'entrée — fonction de portée module (les gestionnaires
// de l'historique l'appellent aussi ; avant, elle vivait dans init() et
// n'était joignable que via window).
function updateCount() {
  const ta = $("#input-text");
  if (!ta) return;
  const len = ta.value.length;
  $("#char-count").textContent = `${len} / 2000`;
  $("#char-warn").hidden = len <= 2000;
}

function themeIcon() {
  return state.settings.theme === "sombre" ? "☾" : state.settings.theme === "clair" ? "☀" : "◐";
}
function applyTheme() {
  document.documentElement.dataset.theme = state.settings.theme;
  $("#theme-toggle").textContent = themeIcon();
}

const ROUTES = {
  "/": "view-home",
  "/histoire": "view-histoire",
  "/favoris": "view-favoris",
  "/a-propos": "view-a-propos",
  "/parametres": "view-parametres",
};

function router() {
  const path = window.location.pathname;
  const id = ROUTES[path] || "view-home";
  $$(".view").forEach((v) => (v.hidden = v.id !== id));
  $$(".navlinks a").forEach((a) =>
    a.classList.toggle("active", a.getAttribute("href") === path));
  if (id === "view-histoire") renderHistory(false);
  if (id === "view-favoris") renderHistory(true);
  window.scrollTo({ top: 0 });
}

// ------------------------------------------------------------ paramètres

function readParams() {
  const styles = $$(".style-chip.selected").map((c) => c.dataset.style);
  return {
    depth: $("#p-depth").value,
    exaggeration: $("#p-exaggeration").value,
    length: $("#p-length").value,
    complexity: $("#p-complexity").value,
    mode: $("#p-mode").value,
    styles: styles.length ? styles : (state.meta?.defaults.styles || ["francais"]),
  };
}

function applyParams(params) {
  if (!params) return;
  const set = (sel, val) => { if (val) $(sel).value = val; };
  set("#p-depth", params.depth);
  set("#p-exaggeration", params.exaggeration);
  set("#p-length", params.length);
  set("#p-complexity", params.complexity);
  set("#p-mode", params.mode || "standard");
  (params.styles || []).forEach((s) => {
    const chip = $(`.style-chip[data-style="${s}"]`);
    if (chip) chip.classList.add("selected");
  });
  updateRecap();
}

function styleLabels() {
  const map = {};
  Object.entries(state.meta?.styles || {}).forEach(([id, s]) => (map[id] = s.label));
  return map;
}

function updateRecap() {
  const p = readParams();
  const names = (p.styles || []).map((s) => styleLabels()[s] || s).join(" et ");
  const recaps = [
    `style ${names || "libre"}`,
    `« ${exagDesc(p.exaggeration)} »`,
    `longueur ${lengthLabel(p.length)}`,
    `registre ${complexityLabel(p.complexity)}`,
    p.mode === "dissertation" ? "en vraie dissertation" :
      p.mode === "citation" ? "en aphorisme ciselé" : "en réflexion libre",
  ];
  $("#profile-recap").textContent =
    `Profil choisi : ${recaps.join(", ")}.`;
  $("#profile-summary").textContent = ` — ${names || "style libre"}`;
}

function exagDesc(v) {
  return {
    serieux: "sérieux",
    subtile: "subtilement absurde",
    dramatique: "très dramatique",
    caricatural: "complètement caricatural",
    "trop-serieux": "bouleversé par rien",
  }[v];
}
function lengthLabel(v) {
  return {
    court: "courte",
    moyen: "moyenne",
    long: "longue",
    "tres-long": "très longue",
    pqdm: "interminable",
  }[v];
}
function complexityLabel(v) {
  return {
    simple: "simple",
    soutenu: "soutenu",
    "tres-soutenu": "très soutenu",
    intimidant: "intellectuellement intimidant",
    pompeux: "complètement pompeux",
  }[v];
}

function buildStylePicker() {
  const zone = $("#style-picker");
  zone.innerHTML = "";
  for (const [id, s] of Object.entries(state.meta.styles)) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "style-chip";
    b.dataset.style = id;
    b.title = s.desc;
    b.textContent = s.label;
    b.addEventListener("click", () => {
      if (b.classList.contains("selected")) {
        b.classList.remove("selected");
      } else {
        const selected = $$(".style-chip.selected");
        if (selected.length >= 2) selected[0].classList.remove("selected");
        b.classList.add("selected");
      }
      updateRecap();
    });
    zone.appendChild(b);
  }
}

// ------------------------------------------------------------ voile

let veilTimer = null;
let veilStarted = null;

function showVeil() {
  // Deux générations concurrentes ne doivent pas empiler des timers.
  if (veilTimer) clearInterval(veilTimer);
  const veil = $("#generation-veil");
  veil.hidden = false;
  veilStarted = Date.now();
  const phrases = state.meta?.loading_phrases || ["Pesée des mots…"];
  let i = 0;
  $("#veil-phrase").textContent = phrases[0];
  $("#veil-long").hidden = true;
  veilTimer = setInterval(() => {
    if (Date.now() - veilStarted > 8000) $("#veil-long").hidden = false;
    i = (i + 1) % phrases.length;
    const el = $("#veil-phrase");
    el.style.opacity = 0;
    setTimeout(() => {
      el.textContent = phrases[i];
      el.style.opacity = 1;
    }, 400);
  }, 1600);
}

function hideVeil() {
  $("#generation-veil").hidden = true;
  if (veilTimer) clearInterval(veilTimer);
  veilTimer = null;
}

// ------------------------------------------------------------ génération

async function generate(input) {
  const params = readParams();
  showVeil();
  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input_text: input, ...params }),
    });
    hideVeil();
    if (!res.ok) throw new Error(`generation ${res.status}`);
    const data = await res.json();
    setResult({ input, text: data.text, attribution: data.attribution, params, mode: params.mode });
  } catch (e) {
    hideVeil();
    alert("La matière n'a pu se composer : veuillez réessayer.");
  }
}

async function transform(action) {
  if (!state.current) return;
  showVeil();
  try {
    const res = await fetch("/api/transform", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        previous_text: state.current.text,
        original_input: state.current.input,
        styles: state.current.params.styles,
      }),
    });
    hideVeil();
    if (!res.ok) throw new Error(`transform ${res.status}`);
    const data = await res.json();
    setResult({ ...state.current, text: data.text });
  } catch (e) {
    hideVeil();
    alert("La transformation est tombée en aporie.");
  }
}

function setResult(r) {
  state.current = { ...r, attribution: r.attribution || null };
  renderResult();
  const entry = History.addEntry({
    input: r.input,
    text: r.text,
    attribution: r.attribution,
    params: r.params,
    mode: r.mode,
  });
  state.current.entryId = entry.id;
  $("#result-zone").hidden = false;
  $("#result-zone").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderResult() {
  const zone = $("#result-text");
  zone.innerHTML = "";
  const paragraphs = state.current.text.split("\n\n");
  for (const para of paragraphs) {
    let text = para;
    let isSubtitle = false;
    if (/^#{3}\s/.test(para)) {
      text = para.replace(/^#{3}\s*/, "");
      isSubtitle = true;
    } else if (/^(Conclusion|[IVXLCDM]+\.\s)/.test(para)) {
      const [title, ...rest] = para.split("\n");
      const span = document.createElement("span");
      span.className = "subtitle";
      span.textContent = title;
      zone.appendChild(span);
      const body = document.createElement("span");
      body.textContent = rest.join("\n") + "\n\n";
      zone.appendChild(body);
      continue;
    }
    if (isSubtitle) {
      const span = document.createElement("span");
      span.className = "subtitle";
      span.textContent = text + "\n\n";
      zone.appendChild(span);
      continue;
    }
    const span = document.createElement("span");
    span.textContent = para + "\n\n";
    zone.appendChild(span);
  }
  const ap = $("#result-attribution");
  if (state.current.attribution) {
    ap.textContent = state.current.attribution;
    ap.hidden = false;
    const badge = document.createElement("span");
    badge.className = "badge-inline";
    badge.textContent = "citation humoristique · attribution fictive";
    ap.appendChild(badge);
  } else {
    ap.hidden = true;
  }
}

// ------------------------------------------------------------ historique

function renderHistory(onlyFav) {
  const search = $(onlyFav ? "#fav-search" : "#history-search");
  const styleSel = $(onlyFav ? "#fav-style" : "#history-style");
  const listEl = $(onlyFav ? "#fav-list" : "#history-list");
  const emptyEl = $(onlyFav ? "#fav-empty" : "#history-empty");
  const galleryZone = $(onlyFav ? "#fav-gallery-zone" : null);
  const galleryBtn = $(onlyFav ? "#fav-gallery" : null);

  const q = search?.value || "";
  const style = styleSel?.value || "";
  const entries = History.search(q, onlyFav, style);

  emptyEl.hidden = entries.length !== 0;
  listEl.innerHTML = "";
  if (galleryZone) galleryZone.hidden = false;
  if (onlyFav && galleryZone) galleryZone.innerHTML = "";

  const labels = styleLabels();
  for (const e of entries) {
    const styleNames = (e.style_tag || "").split("+")
      .map((s) => labels[s] || s).join(" + ");
    const div = document.createElement("div");
    div.className = "entry";
    // innerHTML uniquement pour la structure fixe (pas de donnée utilisateur) ;
    // les contenus dynamiques passent ensuite par textContent.
    div.innerHTML = `
      <div class="entry-head">
        <h3 class="entry-input"></h3>
        <button class="fav-star ${e.fav ? "on" : ""}" title="favori">★</button>
      </div>
      <p class="entry-meta"></p>
      <p class="entry-extract"></p>
      <div class="entry-actions">
        <button class="act re-open">Rouvrir</button>
        <button class="act duplicate">Dupliquer</button>
        <button class="act export-card">Exporter</button>
        <button class="act delete">Supprimer</button>
      </div>`;
    div.querySelector(".entry-meta").textContent =
      `${styleNames} · ${new Date(e.ts).toLocaleString("fr-FR")}`;
    div.querySelector(".entry-input").textContent =
      e.input.length > 64 ? e.input.slice(0, 64) + "…" : e.input;
    div.querySelector(".entry-extract").textContent =
      e.text.slice(0, 160) + (e.text.length > 160 ? "…" : "");

    div.querySelector(".fav-star").addEventListener("click", (el) => {
      const upd = History.updateEntry(e.id, { fav: !e.fav });
      el.target.classList.toggle("on", upd?.fav);
      if (onlyFav) renderHistory(true);
    });
    div.querySelector(".re-open").addEventListener("click", () => {
      historyRoute("/");
      $("#input-text").value = e.input;
      updateCount();
    });
    div.querySelector(".duplicate").addEventListener("click", () => {
      historyRoute("/");
      generate(e.input);
    });
    div.querySelector(".delete").addEventListener("click", () => {
      History.removeEntry(e.id);
      renderHistory(onlyFav);
    });
    div.querySelector(".export-card").addEventListener("click", () => openCardModal(e));
    listEl.appendChild(div);

    if (onlyFav && galleryZone) {
      const canvas = document.createElement("canvas");
      galleryZone.appendChild(canvas);
      Cards.renderCard(canvas, e, "square");
      canvas.addEventListener("click", () => openCardModal(canvasEntry(e)));
    }
  }
}

// ------------------------------------------------------------ cartes

function canvasEntry(e) {
  return {
    text: e.text,
    input: e.input,
    attribution: e.attribution,
    mode: e.mode,
    params: e.params,
  };
}

function openCardModal(entry) {
  const modal = $("#card-modal");
  modal.hidden = false;
  const canvas = $("#card-canvas");
  const formatSel = $("#card-format");
  let format = formatSel.value;
  Cards.renderCard(canvas, entry, format);
  formatSel.onchange = () => {
    format = formatSel.value;
    canvas.width = 0;
    Cards.renderCard(canvas, entry, formatSel.value);
  };
  $("#card-close").onclick = () => (modal.hidden = true);
  $("#card-download").onclick = () =>
    Cards.downloadCard(canvas, `reflexion-${format}.png`);
  $("#card-copy").onclick = async () => {
    try {
      await Cards.copyCard(canvas);
      alert("Image copiée dans le presse-papiers.");
    } catch {
      alert("Copie impossible : téléchargez le PNG.");
    }
  };
  if (navigator.canShare) {
    $("#card-share").hidden = false;
    $("#card-share").onclick = async () => {
      await Cards.shareCard(canvas, "La Grande Réflexion");
    };
  }
  $("#card-publish").onclick = async () => {
    try {
      const path = await Cards.publishCard(canvasEntry(entry));
      const url = location.origin + path;
      await navigator.clipboard.writeText(url);
      alert(`Lien public copié :\n${url}`);
    } catch {
      alert("Publication impossible pour le moment.");
    }
  };
}

function historyRoute(path) {
  window.history.pushState({}, "", path);
  router();
}

// ------------------------------------------------------------ init

async function init() {
  applyTheme();
  $("#theme-toggle").addEventListener("click", () => {
    const seq = ["sombre", "clair", "auto"];
    const cur = seq.indexOf(state.settings.theme);
    state.settings.theme = seq[(cur + 1) % seq.length];
    applyTheme();
    saveSettings();
  });

  let metaOk = true;
  try {
    const metaRes = await fetch("/api/meta");
    if (!metaRes.ok) throw new Error(`meta ${metaRes.status}`);
    state.meta = await metaRes.json();
  } catch (err) {
    // Sans meta, l'app resterait bloquée : on bascule sur des valeurs de
    // repli suffisantes pour utiliser le générateur.
    metaOk = false;
    state.meta = {
      styles: {
        francais: { label: "Philosophe français", desc: "Style par défaut" },
      },
      defaults: { styles: ["francais"] },
      loading_phrases: ["Pesée des mots…"],
      transform_actions: {},
    };
  }
  buildStylePicker();
  applyParams(state.settings.defaults || state.meta.defaults || {});
  updateRecap();
  if (!metaOk) {
    const warning = document.createElement("p");
    warning.className = "meta-warning";
    warning.textContent =
      "Le serveur n'a pas fourni la configuration complète ; l'app tourne en mode simplifié.";
    document.querySelector(".hero").appendChild(warning);
  }

  // route interception
  document.addEventListener("click", (e) => {
    const a = e.target.closest("a[data-route]");
    if (a) {
      e.preventDefault();
      historyRoute(a.getAttribute("href"));
    }
  });
  window.addEventListener("popstate", router);

  // textarea & compteur
  const ta = $("#input-text");
  ta.addEventListener("input", updateCount);
  $("#btn-clear").addEventListener("click", () => { ta.value = ""; updateCount(); });
  $("#btn-paste").addEventListener("click", async () => {
    const text = await navigator.clipboard.readText().catch(() => "");
    if (text) { ta.value = text; updateCount(); }
  });
  $$(".ex").forEach((a) =>
    a.addEventListener("click", (e) => {
      e.preventDefault();
      ta.value = a.textContent.replace(/[«»]/g, "").trim();
      updateCount();
      ta.focus();
    }));

  // placeholder rotatif
  let pi = 0;
  setInterval(() => {
    if (!document.activeElement || document.activeElement !== ta) {
      ta.placeholder = state.placeholders[pi];
      pi = (pi + 1) % state.placeholders.length;
    }
  }, 2500);

  // bouton principal
  $("#btn-generate").addEventListener("click", () => {
    const val = ta.value.trim();
    if (!val) {
      ta.focus();
      return;
    }
    generate(val);
  });
  ta.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      $("#btn-generate").click();
    }
  });

  // actions du résultat
  $("#act-copy").addEventListener("click", async () => {
    if (!state.current) return;
    const text = state.current.attribution
      ? `${state.current.text}\n${state.current.attribution}`
      : state.current.text;
    await navigator.clipboard.writeText(text).catch(() => {});
    $("#act-copy").textContent = "Copié ✓";
    setTimeout(() => ($("#act-copy").textContent = "Copier"), 1200);
  });
  $("#act-regen").addEventListener("click", () => {
    if (state.current) generate(state.current.input);
  });
  $("#act-params").addEventListener("click", () => {
    $("#params").open = true;
    $("#params").scrollIntoView({ behavior: "smooth" });
  });
  $("#act-export").addEventListener("click", () => {
    if (state.current) openCardModal(canvasEntry(state.current));
  });

  // boutons magiques (menu déroulé)
  const menu = $("#magic-menu");
  const magicBtn = $("#act-magic");
  function buildMagic() {
    menu.innerHTML = "";
    for (const [id, label] of Object.entries(state.meta.transform_actions)) {
      const b = document.createElement("button");
      b.textContent = label;
      b.addEventListener("click", () => {
        menu.hidden = true;
        transform(id);
      });
      menu.appendChild(b);
    }
  }
  buildMagic();
  magicBtn.addEventListener("click", () => (menu.hidden = !menu.hidden));
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".magic-wrap")) menu.hidden = true;
  });

  // options des panneaux
  for (const sel of ["#p-depth", "#p-exaggeration", "#p-length", "#p-complexity", "#p-mode"]) {
    $(sel).addEventListener("change", updateRecap);
  }

  // page paramètres
  const themeSel = $("#s-theme");
  themeSel.value = state.settings.theme;
  themeSel.addEventListener("change", () => {
    state.settings.theme = themeSel.value;
    applyTheme();
    saveSettings();
  });
  $("#btn-save-defaults").addEventListener("click", () => {
    state.settings.defaults = readParams();
    saveSettings();
    alert("Réglages mémorisés pour vos prochaines entrées.");
  });

  // pages historique/favoris : recherche & filtres
  wireFilter("#history-style", false);
  wireFilter("#fav-style", true);
  wireSearch("#history-search", false);
  wireSearch("#fav-search", true);
  $("#history-clear").addEventListener("click", () => {
    if (confirm("Vider l'historique ? C'est comme brûler la bibliothèque de Babylone.")) {
      History.clearAll();
      renderHistory(false);
    }
  });
  $("#fav-gallery").addEventListener("click", () => {
    const zone = $("#fav-gallery-zone");
    const list = $("#fav-list");
    zone.hidden = !zone.hidden;
    list.hidden = !list.hidden;
  });

  router();
}

function wireFilter(sel, fav) {
  const el = $(sel);
  const used = History.stylesUsed();
  const labels = styleLabels();
  el.innerHTML = `<option value="">Tous les styles</option>` +
    used.map((id) => `<option value="${id}">${labels[id] || id}</option>`).join("");
  el.addEventListener("change", () => renderHistory(fav));
}
function wireSearch(sel, fav) {
  $(sel).addEventListener("input", () => renderHistory(fav));
}

init();
