// unpick UI. Vanilla JS, no build step. Every value from a scanned file is untrusted, so the DOM is
// built with textContent only; nothing from the server is ever assigned to innerHTML.
"use strict";

const TOKEN = document.querySelector('meta[name="unpick-token"]').content;

function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined) n.append(kid);
  return n;
}

async function api(path, body) {
  const opts = { headers: { "X-Unpick-Token": TOKEN } };
  if (body !== undefined) {
    opts.method = "POST";
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({}));
  return { status: r.status, data };
}

// ---- navigation and theme -------------------------------------------------------------------------
const screens = ["inventory", "scan", "check", "rehearse", "verify", "backends"];
function show() {
  const name = screens.includes(location.hash.slice(1)) ? location.hash.slice(1) : "scan";
  for (const s of screens) document.getElementById(`screen-${s}`).hidden = s !== name;
  document.querySelectorAll("nav a").forEach(a => a.dataset.screen === name ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current"));
  if (name === "inventory" && !inventoryLoaded) loadInventory();
  if (name === "backends") loadBackends();
}
window.addEventListener("hashchange", show);

const themeBtn = document.getElementById("theme");
function setTheme(t) {
  document.documentElement.dataset.theme = t;
  themeBtn.textContent = t === "dark" ? "Light" : "Dark";
  localStorage.setItem("unpick-theme", t);
}
themeBtn.addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
setTheme(localStorage.getItem("unpick-theme") || "light");

// Exports go through fetch so the token header is sent; the browser then saves the blob.
document.addEventListener("click", async (e) => {
  const a = e.target.closest("[data-export]");
  if (!a) return;
  e.preventDefault();
  const r = await fetch(a.dataset.export, { headers: { "X-Unpick-Token": TOKEN } });
  if (!r.ok) { alertStrip("Nothing to export yet."); return; }
  const blob = await r.blob();
  const name = (r.headers.get("Content-Disposition") || "").split("filename=")[1] || "unpick-export";
  const link = el("a", { href: URL.createObjectURL(blob), download: name });
  link.click();
  URL.revokeObjectURL(link.href);
});

// ---- inventory --------------------------------------------------------------------------------------
let inventoryLoaded = false;
let inventoryRows = [];
async function loadInventory() {
  inventoryLoaded = true;
  const { data } = await api("/api/inventory");
  inventoryRows = data;
  fillFilter("inv-host", [...new Set(data.map(r => r.host))].sort());
  fillFilter("inv-kind", [...new Set(data.map(r => r.kind))].sort());
  renderInventory();
}
function fillFilter(id, values) {
  const sel = document.getElementById(id);
  for (const v of values) sel.append(el("option", { value: v, text: v }));
  sel.addEventListener("change", renderInventory);
}
function renderInventory() {
  const host = document.getElementById("inv-host").value;
  const kind = document.getElementById("inv-kind").value;
  const rows = inventoryRows.filter(r => (!host || r.host === host) && (!kind || r.kind === kind));
  const tbody = document.querySelector("#inv-table tbody");
  tbody.replaceChildren(...rows.map(r => el("tr", {},
    el("td", {}, el("input", { type: "checkbox", class: "inv-pick", "data-path": r.path.split("#")[0], "aria-label": `Select ${r.name}` })),
    el("td", {}, el("span", { class: `chip ${r.kind}`, text: r.kind })),
    el("td", { text: r.host }), el("td", { text: r.scope }), el("td", { text: r.name }),
    el("td", { class: "mono", text: r.display_path }),
    el("td", { class: "mono", text: r.sha256.slice(0, 12), title: r.sha256 }),
    el("td", { text: r.modified.slice(0, 10) }))));
  document.getElementById("inv-empty").hidden = rows.length > 0;
  tbody.querySelectorAll(".inv-pick").forEach(c => c.addEventListener("change", pickChanged));
  pickChanged();
}
function pickChanged() {
  document.getElementById("inv-scan").disabled = !document.querySelector(".inv-pick:checked");
}
document.getElementById("inv-all").addEventListener("change", (e) => {
  document.querySelectorAll(".inv-pick").forEach(c => { c.checked = e.target.checked; });
  pickChanged();
});
document.getElementById("inv-scan").addEventListener("click", () => {
  const paths = [...new Set([...document.querySelectorAll(".inv-pick:checked")].map(c => c.dataset.path))];
  queue = paths.slice(1);
  document.getElementById("scan-path").value = paths[0];
  location.hash = "#scan";
  runScan();
});

// ---- scan -------------------------------------------------------------------------------------------
let last = null;
let queue = [];
let consentGiven = [];
let currentFile = null;

document.getElementById("scan-form").addEventListener("submit", (e) => { e.preventDefault(); queue = []; runScan(); });

async function loadJudges() {
  const { data } = await api("/api/judges");
  const sel = document.getElementById("scan-judge");
  if (data.default) sel.append(el("option", { value: "auto", text: `Auto: ${data.default} (on-device)` }));
  for (const j of data.judges.filter(j => j.usable !== false)) {
    sel.append(el("option", { value: j.id, text: `${j.id} (${j.kind}${j.kind === "hosted" ? ", asks first" : ""})` }));
  }
}

async function runScan() {
  const path = document.getElementById("scan-path").value.trim();
  if (!path) return;
  alertStrip(`Scanning ${path} ...`);
  const body = {
    path, judge: document.getElementById("scan-judge").value || null, consent: consentGiven,
    backends: document.getElementById("scan-backends").checked ? installedBackends : [],
  };
  const { status, data } = await api("/api/scan", body);
  if (status === 409 && data.need_consent) {
    if (await askConsent(data.prompt)) { consentGiven.push(data.need_consent); return runScan(); }
    alertStrip("Hosted judge declined; nothing was sent.");
    return;
  }
  if (status !== 200) { alertStrip(data.error || `Scan failed (${status}).`); return; }
  last = data;
  renderScan();
}

let installedBackends = [];
async function loadInstalledBackends() {
  const { data } = await api("/api/backends");
  installedBackends = data.filter(b => b.installed && !b.needs_online).map(b => b.name);
  const label = document.getElementById("scan-backends").parentElement;
  label.title = installedBackends.length ? installedBackends.join(", ") : "No offline scanners installed";
  document.getElementById("scan-backends").disabled = !installedBackends.length;
}

function askConsent(text) {
  const d = document.getElementById("consent");
  document.getElementById("consent-text").textContent = text.replace(" Send it? [yes/N] ", "");
  return new Promise((resolve) => {
    const done = (v) => { d.close(); resolve(v); };
    document.getElementById("consent-yes").onclick = () => done(true);
    document.getElementById("consent-no").onclick = () => done(false);
    d.showModal();
  });
}

function alertStrip(text) {
  document.getElementById("runstrip").replaceChildren(el("span", { text }));
}

function renderScan() {
  const strip = document.getElementById("runstrip");
  const parts = [el("span", {}, el("b", { text: "ran " }), "built-in checks")];
  for (const r of last.runs) {
    parts.push(el("span", {}, el("b", { text: r.source + " " }), `${r.version || ""} ${r.on_device === false ? "hosted" : "local"} (${r.status})`));
  }
  const net = last.summary.network_calls;
  parts.push(net.length ? el("span", { class: "net", text: "NETWORK: " + net.map(r => `${r.source}: ${r.network_detail}`).join("; ") })
                        : el("span", {}, el("b", { text: "network " }), "none"));
  parts.push(el("span", {}, el("b", { text: "open " }), String(last.summary.open), el("b", { text: "  accepted " }), String(last.summary.accepted)));
  strip.replaceChildren(...parts);

  const counts = {};
  for (const f of last.findings) counts[f.path] = (counts[f.path] || 0) + 1;
  const files = [...last.files].sort((a, b) => (counts[b] || 0) - (counts[a] || 0) || a.localeCompare(b));
  document.getElementById("file-list").replaceChildren(...files.map(p => el("li", {},
    el("button", { type: "button", onclick: () => openFile(p), "aria-current": p === currentFile ? "true" : "false" },
      el("span", { text: p }), el("span", { class: "count" + (counts[p] ? "" : " zero"), text: String(counts[p] || 0) })))));
  openFile(files[0]);
}

function absolute(rel) {
  const t = last.target;
  if (last.files.length === 1 && !t.endsWith("/") && t.split(/[\\/]/).pop() === rel) return t;
  return `${t.replace(/[\\/]$/, "")}/${rel}`;
}

async function openFile(rel) {
  if (!rel) return;
  currentFile = rel;
  document.querySelectorAll(".files li button").forEach(b => b.setAttribute("aria-current", b.firstChild.textContent === rel ? "true" : "false"));
  const findings = last.findings.concat(last.accepted).filter(f => f.path === rel);
  const flagged = new Set(findings.map(f => f.line));
  const { data } = await api(`/api/raw?path=${encodeURIComponent(absolute(rel))}`);
  const rows = Array.isArray(data) ? data : [];
  document.getElementById("split").replaceChildren(...rows.map(r => el("div", {
      class: `row${flagged.has(r.line) ? " flag" : ""}${r.differs ? " differs" : ""}`, id: `L${r.line}` },
    el("div", { class: "ln", text: String(r.line) }),
    el("div", { class: "rendered", text: r.rendered }),
    el("div", { class: "raw", title: bytesTitle(r.raw) }, ...rawParts(r.raw),
      r.reasons.length ? el("span", { class: "hidden-note", text: "hidden: " + r.reasons.join("; ") }) : null))));
  renderFindings(findings);
}

// Long runs of escaped invisible characters collapse to a count; hover shows the exact code points.
function rawParts(raw) {
  const out = [];
  let i = 0;
  for (const m of raw.matchAll(/(?:\\u\{[0-9A-F]+\}){6,}/g)) {
    out.push(raw.slice(i, m.index));
    const n = m[0].split("\\u{").length - 1;
    out.push(el("span", { class: "collapsed", title: m[0], text: `${m[0].slice(0, 24)} ... +${n - 3} more hidden characters` }));
    i = m.index + m[0].length;
  }
  out.push(raw.slice(i));
  return out;
}

function bytesTitle(raw) {
  const hidden = raw.match(/\\u\{[0-9A-F]+\}/g);
  return hidden ? `Hidden code points: ${[...new Set(hidden)].slice(0, 12).join(" ")}${hidden.length > 12 ? " ..." : ""}` : "";
}

function renderFindings(findings) {
  const box = document.getElementById("findings");
  if (!findings.length) { box.replaceChildren(el("div", { class: "card empty", text: "No findings in this file." })); return; }
  box.replaceChildren(...findings.map(f => {
    const kind = f.source.split(":")[0];
    const ctx = el("pre", {}, ...f.context.map(c => el("span", { class: c.line === f.line ? "hit" : null, text: `${String(c.line).padStart(4)}  ${c.text}\n` })));
    const choices = ["accept", "reject", "ask-author"].map(choice => el("button", {
      type: "button", "aria-pressed": f.decision === choice ? "true" : "false", text: choice,
      onclick: async () => {
        const { status } = await api("/api/decide", { id: f.id, choice });
        if (status === 200) { f.decision = choice; renderFindings(findings); }
      } }));
    return el("article", { class: `finding${f.decision === "accept" ? " decided" : ""}` },
      el("div", { class: "top" },
        el("span", { class: `sev ${f.severity}`, text: f.severity.toUpperCase() }),
        el("span", { class: `badge ${kind}`, text: kind === "judge" ? `judge: ${f.source.slice(6)}` : f.source }),
        el("span", { class: "rule", text: f.rule_id }),
        el("a", { href: `#L${f.line}`, text: `line ${f.line}`, onclick: (e) => { e.preventDefault(); document.getElementById(`L${f.line}`)?.scrollIntoView({ block: "center" }); } })),
      el("p", { class: "msg", text: f.message }),
      ctx,
      el("p", { class: "why", text: "Why: " + f.why }),
      el("p", { class: "why", text: "False positive when: " + f.false_positive }),
      el("p", { class: "agree", text: `Agreed by ${f.agreed_by.length} of ${last.sources.length}: ${f.agreed_by.join(", ")}` }),
      el("div", { class: "decide" }, choices));
  }));
}

// ---- backends and judges ----------------------------------------------------------------------------
async function loadBackends() {
  const [{ data: be }, { data: ju }] = await Promise.all([api("/api/backends"), api("/api/judges")]);
  document.querySelector("#be-table tbody").replaceChildren(...be.map(b => el("tr", {},
    el("td", { class: "mono", text: b.name }), el("td", { text: b.installed ? "yes" : "no" }), el("td", { text: b.version || "-" }),
    el("td", { text: b.tested_version }), el("td", { text: b.maintainer }), el("td", { text: b.license }),
    el("td", { text: b.network + (b.unverified ? " (UNVERIFIED)" : "") }))));
  document.querySelector("#ju-table tbody").replaceChildren(...ju.judges.map(j => el("tr", {},
    el("td", { class: "mono", text: j.id }), el("td", { text: j.kind + (j.provider ? ` (${j.provider})` : "") }),
    el("td", { class: "mono", text: j.found_by || "" }), el("td", { text: j.consent }),
    el("td", { text: j.usable === false ? `no: ${j.reason}` : "yes" }),
    el("td", { text: !j.adversarial ? "not recorded" : j.adversarial.reliable ? `reliable (${j.adversarial.recorded})`
      : `UNRELIABLE: fooled on ${j.adversarial.missed_files} of ${j.adversarial.files} files` }))));
  document.getElementById("ju-default").textContent = `Auto picks: ${ju.default || "none (no on-device judge found)"}. Hosted judges are never picked automatically.`;
  const agreement = last ? Object.entries(last.summary.agreement) : [];
  document.querySelector("#agree-table tbody").replaceChildren(...agreement.map(([k, v]) => el("tr", {},
    el("td", { class: "mono", text: k }), el("td", { text: v === null ? "neither flagged anything" : `${Math.round(v * 100)}%` }))));
  document.getElementById("agree-empty").hidden = agreement.length > 0;
}

// ---- check -------------------------------------------------------------------------------------------
let checked = null;
document.getElementById("check-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const ref = document.getElementById("check-ref").value.trim();
  if (!ref) return;
  const strip = document.getElementById("check-strip");
  strip.replaceChildren(el("span", { text: `Fetching ${ref} into quarantine. Nothing is executed.` }));
  const { status, data } = await api("/api/check", { ref, offline: document.getElementById("check-offline").checked });
  if (status !== 200) { strip.replaceChildren(el("span", { class: "net", text: data.error || "check failed" })); return; }
  checked = data;
  strip.replaceChildren(el("span", {}, el("b", { text: "quarantine " }), data.id),
    el("span", {}, el("b", { text: "network " }), data.network.length ? data.network.join("; ") : "none"));
  const facts = Object.entries(data.provenance || {}).filter(([k, v]) => v !== null && v !== "" && k !== "project_urls" && !(Array.isArray(v) && !v.length));
  document.getElementById("check-facts").replaceChildren(...facts.flatMap(([k, v]) => [el("dt", { text: k.replaceAll("_", " ") }), el("dd", { text: Array.isArray(v) ? v.join(", ") : String(v) })]));
  const qs = data.questions.length ? data.questions.map(q => el("li", { class: "bad", text: q }))
    : [el("li", { text: data.provenance && Object.keys(data.provenance).length ? "Nothing stood out. That is not the same as safe." : "No provenance lookup was made." })];
  document.getElementById("check-questions").replaceChildren(...qs);
  document.getElementById("check-card").hidden = false;
  const s = data.scan.summary;
  document.getElementById("check-summary").textContent = `${s.open} open finding(s) in ${data.scan.files.length} file(s). Read each one before approving.`;
  document.getElementById("check-result").hidden = false;
  document.getElementById("check-command").hidden = true;
});
document.getElementById("check-open").addEventListener("click", () => {
  if (!checked) return;
  last = checked.scan;
  location.hash = "#scan";
  document.getElementById("scan-path").value = checked.root;
  renderScan();
});
document.getElementById("check-approve").addEventListener("click", async () => {
  if (!checked) return;
  const { status, data } = await api("/api/check/approve", { id: checked.id });
  const pre = document.getElementById("check-command");
  pre.textContent = status === 200 ? `# Not run. Copy it yourself if you agree:\n${data.install_command}\n# Locked in ${data.lockfile}` : data.error;
  pre.hidden = false;
});

// ---- rehearse ----------------------------------------------------------------------------------------
document.getElementById("rehearse-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const path = document.getElementById("rehearse-path").value.trim();
  if (!path) return;
  const strip = document.getElementById("rehearse-strip");
  document.getElementById("rehearse-timeline").replaceChildren();
  document.getElementById("rehearse-verdict").hidden = true;
  const { status, data } = await api("/api/rehearse", { path, task: document.getElementById("rehearse-task").value });
  if (status !== 200) { strip.replaceChildren(el("span", { class: "net", text: data.error })); return; }
  strip.replaceChildren(el("span", { text: "Box running: no network, fake secrets, local model. This takes a few minutes." }));
  pollRehearse(data.job);
});

function eventItem(ev, evidence) {
  const blob = JSON.stringify(ev.input || {});
  const hit = evidence.some(i => typeof i.at === "string" && i.at === ev.ts);
  return el("li", { class: hit ? "hit" : null }, el("span", { text: `${(ev.ts || "").slice(11, 19)}  ` }),
    el("span", { class: "tool", text: ev.tool }), ` ${blob.slice(0, 220)}`);
}

async function pollRehearse(job) {
  const { data } = await api(`/api/rehearse/${job}`);
  const evidence = data.result ? data.result.evidence : [];
  document.getElementById("rehearse-timeline").replaceChildren(...data.events.map(ev => eventItem(ev, evidence)),
    ...evidence.filter(i => typeof i.at === "number").map(i => el("li", { class: "hit", text: `trace  ${i.rule}  ${i.detail}` })));
  if (data.status === "error") {
    document.getElementById("rehearse-strip").replaceChildren(el("span", { class: "net", text: data.error }));
    return;
  }
  if (data.status !== "done") { setTimeout(() => pollRehearse(job), 2000); return; }
  const r = data.result;
  const card = document.getElementById("rehearse-verdict");
  card.className = `card verdict${r.findings.length ? " bad" : ""}`;
  document.getElementById("rehearse-verdict-text").textContent = r.verdict;
  document.getElementById("rehearse-evidence").replaceChildren(...r.evidence.map(i => el("li", { class: "bad", text: `${i.rule}: ${i.detail}` })));
  document.getElementById("rehearse-scope").textContent = r.scope;
  card.hidden = false;
  document.getElementById("rehearse-strip").replaceChildren(el("span", {}, el("b", { text: "done " }), `${r.events.length} tool call(s), network none, model ${r.box.model}`));
}

// ---- verify ------------------------------------------------------------------------------------------
function diffClass(line) {
  if (line.startsWith("+") && !line.startsWith("+++")) return "add";
  if (line.startsWith("-") && !line.startsWith("---")) return "del";
  return null;
}

function diffBlock(text) {
  return el("pre", { class: "diff" }, ...text.split("\n").map(line => el("span", { class: diffClass(line), text: line + "\n" })));
}

document.getElementById("verify-run").addEventListener("click", async () => {
  const strip = document.getElementById("verify-strip");
  const { status, data } = await api("/api/verify");
  if (status !== 200) { strip.replaceChildren(el("span", { class: "net", text: data.error })); return; }
  strip.replaceChildren(el("span", {}, el("b", { text: "unchanged " }), String(data.unchanged)),
    el("span", {}, el("b", { text: "changed " }), String(data.changed.length)),
    el("span", {}, el("b", { text: "added " }), String(data.added.length)), el("span", {}, el("b", { text: "removed " }), String(data.removed.length)));
  const cards = data.changed.map(c => el("article", { class: "card change" },
    el("h2", { text: `${c.name} ` }, el("span", { class: `chip ${c.kind}`, text: c.kind })),
    el("p", { class: "muted", text: c.path + (c.commit ? `  commit ${c.commit.old} -> ${c.commit.new}` : "") }),
    ...(c.config_changes || []).map(ch => el("p", { class: "mono", text: `${ch.field}: ${JSON.stringify(ch.old)} -> ${JSON.stringify(ch.new)}` })),
    ...(c.files || []).flatMap(f => [el("p", { class: "mono", text: `${f.status} ${f.file}` }), f.diff ? diffBlock(f.diff) : null]),
    c.scan ? el("p", { text: `Re-scan: ${c.scan.open} open finding(s).` }) : null));
  const simple = [...data.added.map(a => el("p", { text: `added: ${a.kind} ${a.name} ${a.display_path}` })),
                  ...data.removed.map(a => el("p", { text: `removed: ${a.kind} ${a.name} ${a.path}` }))];
  document.getElementById("verify-list").replaceChildren(...cards, ...(simple.length ? [el("div", { class: "card" }, ...simple)] : []),
    ...(data.ok ? [el("div", { class: "card", text: "Everything matches the lockfile." })] : []));
});
document.getElementById("verify-pin").addEventListener("click", async () => {
  const { data } = await api("/api/lock", {});
  document.getElementById("verify-strip").replaceChildren(el("span", { text: `Pinned ${data.components} component(s) in unpick.lock.json.` }));
});

loadJudges();
loadInstalledBackends();
show();
