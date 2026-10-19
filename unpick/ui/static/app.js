// unpick UI. Vanilla JS, no build step. Every value from a scanned file is untrusted, so the DOM is built
// with textContent only; nothing from the server is ever assigned to innerHTML.
"use strict";

const TOKEN = document.querySelector('meta[name="unpick-token"]').content;
const NL = String.fromCharCode(10);
const BS = String.fromCharCode(92);

// ---- small helpers ----------------------------------------------------------------------------------
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
  try {
    const r = await fetch(path, opts);
    const data = await r.json().catch(() => ({}));
    return { status: r.status, data };
  } catch {
    return { status: 0, data: { error: "Could not reach unpick. Is it still running in your terminal? Try again." } };
  }
}

const $ = (id) => document.getElementById(id);
const sentence = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);
const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;

function setError(inputId, message) {
  const input = $(inputId);
  const err = $(`${inputId}-err`);
  if (!err) return;
  if (message) {
    err.textContent = message;
    err.hidden = false;
    input.setAttribute("aria-invalid", "true");
    input.focus();
  } else {
    err.hidden = true;
    input.removeAttribute("aria-invalid");
  }
}

async function busy(button, label, work) {
  const original = button.textContent;
  button.disabled = true;
  button.textContent = label;
  button.setAttribute("aria-busy", "true");
  try {
    return await work();
  } finally {
    button.disabled = false;
    button.textContent = original;
    button.removeAttribute("aria-busy");
  }
}

function strip(id, ...parts) {
  const s = $(id);
  s.hidden = false;
  s.replaceChildren(...parts.map(p => (typeof p === "string" ? el("span", { text: p }) : p)));
}

function errorStrip(id, message) {
  const s = $(id);
  s.hidden = false;
  s.replaceChildren(el("span", { class: "err-label", text: "ERROR " }), el("span", { text: message }));
}

function confirmDialog({ title, text, yes, danger = true }) {
  const d = $("confirm");
  $("confirm-title").textContent = title;
  $("confirm-text").textContent = text;
  const yesBtn = $("confirm-yes");
  yesBtn.textContent = yes;
  yesBtn.className = danger ? "j-btn danger" : "j-btn";
  return new Promise((resolve) => {
    const done = (v) => { d.close(); resolve(v); };
    yesBtn.onclick = () => done(true);
    $("confirm-no").onclick = () => done(false);
    d.oncancel = () => resolve(false);
    d.showModal();
    $("confirm-no").focus();
  });
}

// ---- navigation, theme, presenter mode -------------------------------------------------------------
const screens = ["start", "inventory", "check", "scan", "rehearse", "verify", "recover", "backends"];
function show() {
  const wanted = location.hash.slice(1);
  const name = screens.includes(wanted) ? wanted : "start";
  for (const s of screens) $(`screen-${s}`).hidden = s !== name;
  document.querySelectorAll("[data-screen]").forEach(a => {
    if (a.dataset.screen === name) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  if (name === "inventory" && !inventoryLoaded) loadInventory();
  if (name === "backends") loadBackends();
  const heading = $(`screen-${name}`).querySelector("h1");
  if (heading && document.activeElement !== document.body) heading.focus();
}
window.addEventListener("hashchange", show);

function setTheme(t) {
  document.documentElement.dataset.theme = t;
  $("theme").textContent = t === "dark" ? "Light" : "Dark";
  localStorage.setItem("unpick-theme", t);
}
$("theme").addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
setTheme(localStorage.getItem("unpick-theme") || "light");

function setPresent(on) {
  document.body.classList.toggle("present", on);
  $("present").setAttribute("aria-pressed", on ? "true" : "false");
  localStorage.setItem("unpick-present", on ? "1" : "");
}
$("present").addEventListener("click", () => setPresent(!document.body.classList.contains("present")));
setPresent(localStorage.getItem("unpick-present") === "1" || new URLSearchParams(location.search).has("present"));

// Downloads go through fetch so the token header is sent; the browser then saves the file.
document.addEventListener("click", async (e) => {
  const a = e.target.closest("[data-export]");
  if (!a) return;
  e.preventDefault();
  const r = await fetch(a.dataset.export, { headers: { "X-Unpick-Token": TOKEN } }).catch(() => null);
  if (!r || !r.ok) { errorStrip("runstrip", "Nothing to download yet: run it first."); return; }
  const blob = await r.blob();
  const name = (r.headers.get("Content-Disposition") || "").split("filename=")[1] || "unpick-report";
  const link = el("a", { href: URL.createObjectURL(blob), download: name });
  link.click();
  URL.revokeObjectURL(link.href);
});

// ---- start: samples --------------------------------------------------------------------------------
let samples = null;
async function sample(kind) {
  if (!samples) {
    const { status, data } = await api("/api/demo", {});
    if (status !== 200) { errorStrip("runstrip", data.error || "Could not create the samples."); return; }
    samples = data.samples;
  }
  $("scan-path").value = samples[kind];
  location.hash = "#scan";
  runScan();
}
$("try-dangerous").addEventListener("click", () => sample("dangerous"));
$("try-safe").addEventListener("click", () => sample("safe"));
document.querySelectorAll("[data-sample]").forEach(b => b.addEventListener("click", () => sample(b.dataset.sample)));
$("start-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const v = $("start-path").value.trim();
  if (!v) { setError("start-path", "Paste the path of a file or folder, for example ~/Downloads/some-skill."); return; }
  setError("start-path", null);
  $("scan-path").value = v;
  location.hash = "#scan";
  runScan();
});

// ---- inventory -------------------------------------------------------------------------------------
let inventoryLoaded = false;
let inventoryRows = [];
async function loadInventory() {
  inventoryLoaded = true;
  $("inv-count").textContent = "Looking in the places agents keep add-ons...";
  const { status, data } = await api("/api/inventory");
  if (status !== 200) { $("inv-count").textContent = data.error || "Could not list add-ons."; return; }
  inventoryRows = data;
  fillFilter("inv-host", [...new Set(data.map(r => r.host))].sort());
  fillFilter("inv-kind", [...new Set(data.map(r => r.kind))].sort());
  renderInventory();
}
function fillFilter(id, values) {
  const sel = $(id);
  for (const v of values) sel.append(el("option", { value: v, text: v }));
  sel.addEventListener("change", renderInventory);
}
$("inv-search").addEventListener("input", () => renderInventory());

function scanPath(path) {
  $("scan-path").value = path;
  location.hash = "#scan";
  runScan();
}

function renderInventory() {
  const host = $("inv-host").value;
  const kind = $("inv-kind").value;
  const q = $("inv-search").value.trim().toLowerCase();
  const rows = inventoryRows.filter(r => (!host || r.host === host) && (!kind || r.kind === kind)
    && (!q || r.name.toLowerCase().includes(q) || r.display_path.toLowerCase().includes(q)));
  $("inv-count").textContent = `Showing ${rows.length} of ${plural(inventoryRows.length, "add-on", "add-ons")}.`;
  $("inv-table").querySelector("tbody").replaceChildren(...rows.map(r => {
    const path = r.path.split("#")[0];
    return el("tr", {},
      el("td", {}, el("input", { type: "checkbox", class: "inv-pick", "data-path": path, "aria-label": `Select ${r.name}` })),
      el("td", { class: "name", title: `SHA-256 ${r.sha256}` }, r.name),
      el("td", {}, el("span", { class: `chip ${r.kind}`, text: r.kind.replace("-", " ") })),
      el("td", { class: "nowrap", text: r.host }),
      el("td", { class: "mono path", text: r.display_path }),
      el("td", { class: "nowrap", text: r.modified.slice(0, 10) }),
      el("td", {}, el("button", { type: "button", class: "j-btn secondary small", text: "Scan", "aria-label": `Scan ${r.name}`, onclick: () => scanPath(path) })));
  }));
  $("inv-empty").hidden = rows.length > 0;
  document.querySelectorAll(".inv-pick").forEach(c => c.addEventListener("change", pickChanged));
  pickChanged();
}
function pickChanged() {
  const n = document.querySelectorAll(".inv-pick:checked").length;
  $("inv-scan").disabled = n === 0;
  $("inv-scan").textContent = n ? `Scan ${plural(n, "selected add-on", "selected add-ons")}` : "Scan selected";
}
$("inv-all").addEventListener("change", (e) => {
  document.querySelectorAll(".inv-pick").forEach(c => { c.checked = e.target.checked; });
  pickChanged();
});
$("inv-scan").addEventListener("click", () => {
  const paths = [...new Set([...document.querySelectorAll(".inv-pick:checked")].map(c => c.dataset.path))];
  scanPath(paths[0]);
});

// ---- scan ------------------------------------------------------------------------------------------
let last = null;
let consentGiven = [];
let currentFile = null;
let installedBackends = [];

$("scan-form").addEventListener("submit", (e) => { e.preventDefault(); runScan(); });

async function loadJudges() {
  const { data } = await api("/api/judges");
  const sel = $("scan-judge");
  if (!data.judges) return;
  for (const j of data.judges.filter(j => j.usable !== false)) {
    const where = j.kind === "hosted" ? `online: ${j.provider || j.id}, sends the file, asks first` : "on this computer";
    sel.append(el("option", { value: j.id, text: `${j.id} (${where})` }));
  }
}

async function loadInstalledBackends() {
  const { data } = await api("/api/backends");
  installedBackends = Array.isArray(data) ? data.filter(b => b.installed && !b.needs_online).map(b => b.name) : [];
  const box = $("scan-backends");
  box.disabled = installedBackends.length === 0;
  $("scan-backends-label").textContent = installedBackends.length
    ? `Also run ${plural(installedBackends.length, "other scanner", "other scanners")} installed here, offline (${installedBackends.join(", ")})`
    : "No other scanners installed (the built-in checks still run)";
}

async function runScan() {
  const path = $("scan-path").value.trim();
  if (!path) { setError("scan-path", "Paste the path of a file or folder, or try a sample below."); return; }
  setError("scan-path", null);
  const body = { path, judge: $("scan-judge").value || null, consent: consentGiven,
                 backends: $("scan-backends").checked ? installedBackends : [] };
  const { status, data } = await busy($("scan-go"), "Scanning...", () => api("/api/scan", body));
  if (status === 409 && data.need_consent) {
    const ok = await confirmDialog({ title: "Send this file to an online AI?", yes: "Yes, send it",
      text: data.prompt.replace(" Send it? [yes/N] ", "") });
    if (ok) { consentGiven.push(data.need_consent); return runScan(); }
    setError("scan-path", "Nothing was sent. Choose an AI that runs on this computer, or none.");
    return;
  }
  if (status !== 200) {
    setError("scan-path", data.error && data.error.includes("does not exist")
      ? `There is no file or folder at ${path}. Check the spelling, or paste the full path.` : (data.error || `Scan failed (${status}).`));
    return;
  }
  last = data;
  $("scan-empty").hidden = true;
  $("scan-results").hidden = false;
  renderScan();
}

const SEV_WORD = { high: "SERIOUS", medium: "WARNING", low: "NOTE", info: "INFO" };
const DECISION_LABEL = { accept: "False alarm", reject: "Real problem", "ask-author": "Ask the author" };
const DECISION_DONE = { accept: "Marked as a false alarm.", reject: "Marked as a real problem.", "ask-author": "Marked: ask the author." };

function allFindings() { return last.findings.concat(last.accepted); }
function openFindings() { return allFindings().filter(f => f.decision !== "accept"); }

function renderVerdict() {
  const open = openFindings();
  const serious = open.filter(f => f.severity === "high").length;
  const other = open.length - serious;
  const dismissed = allFindings().length - open.length;
  const v = $("verdict");
  let level = "ok";
  let head = "No warnings from these checks";
  let sub = "That is not the same as safe. Read it raw, and test-run it before you trust it.";
  if (serious) {
    level = "bad";
    head = `Do not install yet: ${plural(serious, "serious problem", "serious problems")}`;
    sub = other ? `${plural(other, "more warning", "more warnings")} to review below.` : "Review each one below.";
  } else if (other) {
    level = "review";
    head = `Review before installing: ${plural(other, "warning", "warnings")}`;
    sub = "None looks serious on its own. Read each one and decide.";
  }
  v.className = `verdict-banner ${level}`;
  v.replaceChildren(el("span", { class: "verdict-word", text: { bad: "STOP", review: "REVIEW", ok: "CLEAR" }[level] }),
    el("div", {}, el("p", { class: "verdict-head", text: head }),
      el("p", { class: "verdict-sub", text: sub + (dismissed ? ` ${plural(dismissed, "warning", "warnings")} marked as false alarms.` : "") })));
}

function renderScan() {
  renderVerdict();
  const net = last.summary.network_calls;
  const sources = last.sources.length;
  $("runstrip").replaceChildren(
    el("span", { text: `Checked ${plural(last.files.length, "file", "files")} with ${plural(sources, "checker", "checkers")}` }),
    el("span", { class: net.length ? "net" : null, text: net.length ? `Sent: ${net.map(r => r.network_detail).join("; ")}` : "Nothing left this computer" }),
    ...(last.skipped && last.skipped.length ? [el("span", { text: `${plural(last.skipped.length, "file", "files")} not readable` })] : []));
  const counts = {};
  for (const f of openFindings()) counts[f.path] = (counts[f.path] || 0) + 1;
  const files = [...last.files].sort((a, b) => (counts[b] || 0) - (counts[a] || 0) || a.localeCompare(b));
  $("file-list").replaceChildren(...files.map(p => el("li", {},
    el("button", { type: "button", "data-file": p, onclick: () => openFile(p), "aria-current": p === currentFile ? "true" : "false" },
      el("span", { class: "fname", text: p }), el("span", { class: "count" + (counts[p] ? "" : " zero"), text: String(counts[p] || 0),
        "aria-label": plural(counts[p] || 0, "warning", "warnings") })))));
  openFile(currentFile && files.includes(currentFile) ? currentFile : files[0]);
}

function absolute(rel) {
  const t = last.target;
  const sep = t.includes(BS) && !t.includes("/") ? BS : "/";
  if (last.files.length === 1 && t.split(sep).pop() === rel) return t;
  return t.replace(/[/]$/, "") + sep + rel;
}

async function openFile(rel) {
  if (!rel) return;
  currentFile = rel;
  document.querySelectorAll("#file-list button").forEach(b => b.setAttribute("aria-current", b.dataset.file === rel ? "true" : "false"));
  const findings = allFindings().filter(f => f.path === rel);
  renderFindings(findings);
  const flagged = new Set(findings.filter(f => f.decision !== "accept").map(f => f.line));
  const { data } = await api(`/api/raw?path=${encodeURIComponent(absolute(rel))}`);
  const rows = Array.isArray(data) ? data : [];
  $("split").replaceChildren(...rows.flatMap(r => splitRow(r, flagged.has(r.line))));
}

function hiddenSentence(reasons) {
  const marker = "tag characters spell: ";
  const r = reasons.find(x => x.includes(marker));
  return r ? r.slice(r.indexOf(marker) + marker.length).replace(/^'|'$/g, "") : null;
}

function splitRow(r, flagged) {
  const row = el("div", { role: "row", class: `row${flagged ? " flag" : ""}${r.differs ? " differs" : ""}`, id: `L${r.line}` },
    el("div", { role: "cell", class: "ln" }, el("span", { text: String(r.line) }), flagged ? el("span", { class: "flag-word", text: "FLAGGED" }) : null),
    el("div", { role: "cell", class: "rendered", text: r.rendered }),
    el("div", { role: "cell", class: "raw" }, ...rawParts(r.raw)));
  const out = [row];
  const secret = hiddenSentence(r.reasons);
  if (secret) {
    out.push(el("div", { role: "row", class: "hidden-row" }, el("div", { role: "cell", class: "ln" }),
      el("div", { role: "cell", class: "hidden-text" }, el("b", { text: "HIDDEN TEXT THE AI READS: " }), secret)));
  } else if (r.reasons.length) {
    out.push(el("div", { role: "row", class: "hidden-row soft" }, el("div", { role: "cell", class: "ln" }),
      el("div", { role: "cell", class: "hidden-text", text: `Hidden from viewers: ${r.reasons.join("; ")}` })));
  }
  return out;
}

// Long runs of escaped invisible characters collapse to a count; hover shows the exact code points.
function rawParts(raw) {
  const token = BS + "u{";
  const out = [];
  let i = 0;
  let text = "";
  while (i < raw.length) {
    if (raw.startsWith(token, i)) {
      let j = i;
      let n = 0;
      while (raw.startsWith(token, j)) {
        const close = raw.indexOf("}", j);
        if (close < 0) break;
        j = close + 1;
        n += 1;
      }
      if (n >= 6) {
        if (text) out.push(text);
        text = "";
        const run = raw.slice(i, j);
        out.push(el("span", { class: "collapsed", title: run, text: `[${n} hidden characters]` }));
        i = j;
        continue;
      }
    }
    text += raw[i];
    i += 1;
  }
  if (text) out.push(text);
  return out;
}

function agreementText(f) {
  if (last.sources.length < 2) return "Found by the built-in checks.";
  return `Flagged by ${f.agreed_by.length} of ${plural(last.sources.length, "checker", "checkers")}: ${f.agreed_by.join(", ")}.`;
}

function showInFile(line) {
  const row = $(`L${line}`);
  if (!row) return;
  row.scrollIntoView({ block: "center" });
  row.classList.add("pulse");
  setTimeout(() => row.classList.remove("pulse"), 1600);
}

function renderFindings(findings) {
  const box = $("findings");
  if (!findings.length) {
    box.replaceChildren(el("div", { class: "card empty", text: "No warnings in this file." }));
    return;
  }
  const order = { high: 0, medium: 1, low: 2, info: 3 };
  const sorted = [...findings].sort((a, b) => (a.decision === "accept") - (b.decision === "accept") || order[a.severity] - order[b.severity] || a.line - b.line);
  box.replaceChildren(...sorted.map(f => findingCard(f, findings)));
}

function findingCard(f, findings) {
  const kind = f.source.split(":")[0];
  const decided = f.decision ? el("p", { class: "decided-line" }, el("b", { text: DECISION_DONE[f.decision] + " " }),
    el("button", { type: "button", class: "link-btn", text: "Undo", onclick: () => decide(f, "undo", findings) })) : null;
  const choices = Object.entries(DECISION_LABEL).map(([choice, label]) => el("button", {
    type: "button", class: "j-btn secondary small", "aria-pressed": f.decision === choice ? "true" : "false", text: label,
    onclick: () => decide(f, choice, findings) }));
  const ctx = el("pre", {}, ...f.context.map(c => el("span", { class: c.line === f.line ? "hit" : null, text: `${String(c.line).padStart(4)}  ${c.text}${NL}` })));
  return el("article", { class: `finding sev-${f.severity}${f.decision === "accept" ? " dismissed" : ""}`, "aria-label": `${SEV_WORD[f.severity]}: ${f.message}` },
    el("div", { class: "top" }, el("span", { class: `sev ${f.severity}`, text: SEV_WORD[f.severity] }),
      kind === "judge" ? el("span", { class: "badge judge", text: "AI opinion" }) : null,
      f.line ? el("button", { type: "button", class: "link-btn", text: `Show line ${f.line} in the file`, onclick: () => showInFile(f.line) }) : null),
    el("h3", { class: "msg", text: sentence(f.message) }),
    el("p", { class: "why" }, el("b", { text: "Why it matters: " }), f.why),
    el("p", { class: "why" }, el("b", { text: "When it is harmless: " }), f.false_positive),
    f.context.length ? ctx : null,
    decided || el("div", { class: "decide", role: "group", "aria-label": "Your decision" }, choices),
    el("p", { class: "meta", text: `${agreementText(f)} Rule ${f.rule_id}.` }));
}

async function decide(f, choice, findings) {
  const { status } = await api("/api/decide", { id: f.id, choice });
  if (status !== 200) return;
  f.decision = choice === "undo" ? null : choice;
  renderVerdict();
  renderFindings(findings);
  const counts = {};
  for (const x of openFindings()) counts[x.path] = (counts[x.path] || 0) + 1;
  document.querySelectorAll("#file-list button").forEach(b => {
    const c = b.querySelector(".count");
    const n = counts[b.dataset.file] || 0;
    c.textContent = String(n);
    c.className = "count" + (n ? "" : " zero");
  });
  const flagged = new Set(findings.filter(x => x.decision !== "accept").map(x => x.line));
  document.querySelectorAll("#split .row").forEach(row => {
    const on = flagged.has(Number(row.id.slice(1)));
    row.classList.toggle("flag", on);
  });
  const card = [...document.querySelectorAll(".finding")].find(c => c.getAttribute("aria-label").endsWith(f.message));
  if (card) (card.querySelector(".decided-line button") || card.querySelector(".decide button")).focus();
}

// ---- check -----------------------------------------------------------------------------------------
let checked = null;
$("check-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const ref = $("check-ref").value.trim();
  if (!ref) { setError("check-ref", "Paste a GitHub link, npm:package, pypi:package, or a local path."); return; }
  setError("check-ref", null);
  strip("check-strip", `Downloading ${ref} into quarantine. Nothing is run.`);
  const { status, data } = await busy($("check-go"), "Checking...", () => api("/api/check", { ref, offline: $("check-offline").checked }));
  if (status !== 200) { $("check-strip").hidden = true; setError("check-ref", data.error || "The check failed."); return; }
  checked = data;
  strip("check-strip", `Saved in quarantine as ${data.id}.`, data.network.length ? `Contacted: ${data.network.join("; ")}.` : "Nothing was sent.");
  const facts = Object.entries(data.provenance || {}).filter(([k, v]) => v !== null && v !== "" && k !== "project_urls" && !(Array.isArray(v) && !v.length));
  $("check-facts").replaceChildren(...facts.flatMap(([k, v]) => [el("dt", { text: k.replaceAll("_", " ") }), el("dd", { text: Array.isArray(v) ? v.join(", ") : String(v) })]));
  let qs = data.questions.map(q => el("li", { class: "bad", text: q }));
  if (!qs.length) qs = [el("li", { text: facts.length ? "Nothing stood out about who made it. That is not the same as safe." : "No who-made-it lookup was made." })];
  $("check-questions").replaceChildren(...qs);
  $("check-card").hidden = false;
  const open = data.scan.summary.open;
  $("check-summary").textContent = open ? `${plural(open, "warning", "warnings")} in ${plural(data.scan.files.length, "file", "files")}. Review them before you approve.`
    : `No warnings in ${plural(data.scan.files.length, "file", "files")}. That is not the same as safe.`;
  $("check-open").className = open ? "j-btn" : "j-btn secondary";
  $("check-open").textContent = open ? `Review the ${plural(open, "warning", "warnings")}` : "Read it raw";
  $("check-result").hidden = false;
  $("check-command").hidden = true;
});
$("check-open").addEventListener("click", () => {
  if (!checked) return;
  last = checked.scan;
  $("scan-path").value = checked.root;
  location.hash = "#scan";
  $("scan-empty").hidden = true;
  $("scan-results").hidden = false;
  renderScan();
});
$("check-approve").addEventListener("click", async () => {
  if (!checked) return;
  const open = checked.scan.summary.open;
  if (open) {
    const ok = await confirmDialog({ title: `Approve with ${plural(open, "open warning", "open warnings")}?`, yes: "Approve anyway",
      text: "You have not marked these warnings as false alarms. Approving records this exact copy as trusted, and unpick will only warn you again if it changes." });
    if (!ok) return;
  }
  const { status, data } = await api("/api/check/approve", { id: checked.id });
  const pre = $("check-command");
  pre.textContent = status === 200 ? `# Not run. Copy it yourself if you agree:${NL}${data.install_command}${NL}# Saved as approved in ${data.lockfile}` : data.error;
  pre.hidden = false;
});

// ---- rehearse --------------------------------------------------------------------------------------
$("rehearse-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const path = $("rehearse-path").value.trim();
  if (!path) { setError("rehearse-path", "Paste the path of the add-on, or a check id from step 1."); return; }
  setError("rehearse-path", null);
  $("rehearse-timeline").replaceChildren();
  $("rehearse-verdict").hidden = true;
  const { status, data } = await api("/api/rehearse", { path, task: $("rehearse-task").value });
  if (status !== 200) { setError("rehearse-path", data.error); return; }
  $("rehearse-go").disabled = true;
  strip("rehearse-strip", "Test run in progress: no network, fake secrets, local model. This takes a few minutes.");
  pollRehearse(data.job);
});

function eventItem(ev, evidence) {
  const hit = evidence.some(i => typeof i.at === "string" && i.at === ev.ts);
  return el("li", { class: hit ? "hit" : null }, hit ? el("b", { text: "WARNING SIGN  " }) : null,
    el("span", { text: `${(ev.ts || "").slice(11, 19)}  ` }), el("span", { class: "tool", text: ev.tool }), ` ${JSON.stringify(ev.input || {}).slice(0, 220)}`);
}

async function pollRehearse(job) {
  const { data } = await api(`/api/rehearse/${job}`);
  const evidence = data.result ? data.result.evidence : [];
  $("rehearse-timeline").replaceChildren(...(data.events || []).map(ev => eventItem(ev, evidence)),
    ...evidence.filter(i => typeof i.at === "number").map(i => el("li", { class: "hit" }, el("b", { text: "WARNING SIGN  " }), i.detail)));
  if (data.status === "error" || data.error) {
    $("rehearse-go").disabled = false;
    errorStrip("rehearse-strip", data.error || "The test run failed.");
    return;
  }
  if (data.status !== "done") { setTimeout(() => pollRehearse(job), 2000); return; }
  $("rehearse-go").disabled = false;
  const r = data.result;
  $("rehearse-verdict").className = `card verdict${r.findings.length ? " bad" : ""}`;
  $("rehearse-verdict-text").textContent = r.verdict;
  $("rehearse-evidence").replaceChildren(...r.evidence.map(i => el("li", { class: "bad", text: i.detail })));
  $("rehearse-verdict").hidden = false;
  strip("rehearse-strip", `Finished: ${plural(r.events.length, "action", "actions")} by the test agent, nothing could leave the box.`);
}

// ---- verify ----------------------------------------------------------------------------------------
function diffClass(line) {
  if (line.startsWith("+") && !line.startsWith("+++")) return "add";
  if (line.startsWith("-") && !line.startsWith("---")) return "del";
  return null;
}

function diffBlock(text) {
  return el("pre", { class: "diff" }, ...text.split(NL).map(line => el("span", { class: diffClass(line), text: line + NL })));
}

$("verify-run").addEventListener("click", async () => {
  const { status, data } = await busy($("verify-run"), "Checking...", () => api("/api/verify"));
  if (status !== 200) {
    errorStrip("verify-strip", (data.error || "").includes("lockfile") ? "Nothing saved as approved yet. Use \"Save the current state as approved\" first." : data.error);
    return;
  }
  strip("verify-strip", data.ok ? "Everything matches what you approved." :
    `${plural(data.changed.length, "add-on changed", "add-ons changed")}, ${data.added.length} new, ${data.removed.length} removed, ${data.unchanged} unchanged.`);
  const cards = data.changed.map(c => el("article", { class: "card change" },
    el("h2", {}, `${c.name} `, el("span", { class: `chip ${c.kind}`, text: c.kind })),
    el("p", { class: "muted", text: c.path + (c.commit ? `  commit ${c.commit.old} to ${c.commit.new}` : "") }),
    ...(c.config_changes || []).map(ch => el("p", { class: "mono", text: `${ch.field}: ${JSON.stringify(ch.old)} became ${JSON.stringify(ch.new)}` })),
    ...(c.files || []).flatMap(f => [el("p", { class: "mono", text: `${f.status}: ${f.file}` }), f.diff ? diffBlock(f.diff) : null]),
    c.scan ? el("p", { class: "big-text", text: c.scan.open ? `The new version has ${plural(c.scan.open, "warning", "warnings")}.` : "The new version has no warnings." }) : null));
  const simple = [...data.added.map(a => el("p", { text: `New: ${a.name} (${a.kind}) at ${a.display_path}` })),
                  ...data.removed.map(a => el("p", { text: `Removed: ${a.name} (${a.kind})` }))];
  $("verify-list").replaceChildren(...cards, ...(simple.length ? [el("div", { class: "card" }, ...simple)] : []));
});
$("verify-pin").addEventListener("click", async () => {
  const ok = await confirmDialog({ title: "Save the current state as approved?", yes: "Save as approved", danger: false,
    text: "From now on, unpick compares every add-on with how it is right now. Anything already changed will stop showing as a change." });
  if (!ok) return;
  const { data } = await api("/api/lock", {});
  strip("verify-strip", `Saved ${plural(data.components, "add-on", "add-ons")} as approved.`);
});

// ---- recover ---------------------------------------------------------------------------------------
async function runRecover(apply) {
  const body = { component: $("recover-component").value.trim() || null, since: $("recover-since").value || null, apply };
  strip("recover-strip", apply ? "Disabling it..." : "Working out the recovery steps. Nothing is changed.");
  const { status, data } = await api("/api/recover", body);
  if (status !== 200) { errorStrip("recover-strip", data.error); return null; }
  const planned = data.contain.filter(x => x.startsWith("would"));
  strip("recover-strip", apply ? "Done. Each edited settings file was backed up first." :
    `${planned.length ? "Not disabled yet. Use \"Disable it now\" when you are ready." : "Nothing to disable."} ${plural(Object.keys(data.reach.rotate).length, "service needs", "services need")} new keys.`);
  $("recover-contain-list").replaceChildren(
    ...data.contain.map(x => el("li", { class: x.startsWith("would") ? null : "bad", text: sentence(x.replace(/^would /, "will ")) })),
    ...data.processes.map(p => el("li", { class: "bad", text: `Still running: process ${p.pid}, ${p.command}` })),
    ...(data.contain.length ? [] : [el("li", { text: "No add-on named, so there is nothing to disable." })]));
  $("recover-contain").disabled = apply || planned.length === 0;
  $("recover-rotate").replaceChildren(...Object.values(data.reach.rotate).map(v => el("li", {},
    el("label", {}, el("input", { type: "checkbox" }), `${v.provider}: ${v.what}`),
    el("p", { class: "why", text: v.how }), v.url ? el("p", { class: "because" }, el("a", { href: v.url.startsWith("https://") ? v.url : null, target: "_blank", rel: "noopener noreferrer", text: v.url })) : null,
    el("p", { class: "because", text: "Found: " + v.because.join(", ") }))));
  const lf = data.changed.lockfile;
  $("recover-changed").textContent = lf ? `${lf.changed.length} changed, ${lf.added.length} new and ${lf.removed.length} removed since you last approved; ${plural(data.changed.recent.length, "file", "files")} modified in the window.`
    : `Nothing was saved as approved, so only modification times are known: ${plural(data.changed.recent.length, "file", "files")} modified in the window.`;
  $("recover-egress").textContent = data.egress;
  $("recover-report-to").replaceChildren(...(data.report_to.length ? data.report_to.map(ch => el("li", {}, `${ch.registry}: ${ch.how} `,
    el("a", { href: ch.url.startsWith("https://") ? ch.url : null, target: "_blank", rel: "noopener noreferrer", text: ch.url })))
    : [el("li", { text: "No registry identified; none published." })]));
  $("recover-count").textContent = `${data.timeline.flagged.length} of ${plural(data.timeline.events, "action", "actions")} matter.`;
  $("recover-timeline").replaceChildren(...data.timeline.flagged.slice(-150).map(e => {
    const serious = e.why.some(w => w.startsWith("touches") || w.startsWith("decodes"));
    return el("li", { class: serious ? "hit" : null }, serious ? el("b", { text: "WARNING SIGN  " }) : null,
      el("span", { text: `${(e.ts || "").slice(0, 19).replace("T", " ")}  ${e.agent}  ` }), el("span", { class: "tool", text: e.tool }),
      ` ${e.why.join("; ")}  ${JSON.stringify(e.input).slice(0, 160)}`);
  }));
  return data;
}
$("recover-form").addEventListener("submit", (e) => { e.preventDefault(); runRecover(false); });
$("recover-contain").addEventListener("click", async () => {
  const plan = [...document.querySelectorAll("#recover-contain-list li")].map(li => li.textContent).join(NL);
  const ok = await confirmDialog({ title: "Disable this add-on now?", yes: "Disable it",
    text: `unpick will do exactly this, and back up every settings file it edits:${NL}${plan}` });
  if (ok) runRecover(true);
});

// ---- settings: scanners and AI reviewers -------------------------------------------------------------
async function loadBackends() {
  const [{ data: be }, { data: ju }] = await Promise.all([api("/api/backends"), api("/api/judges")]);
  if (Array.isArray(be)) {
    $("be-table").querySelector("tbody").replaceChildren(...be.map(b => el("tr", {},
      el("td", { class: "mono", text: b.name }), el("td", { text: b.installed ? "yes" : "no" }), el("td", { text: b.version || "-" }),
      el("td", { text: b.tested_version }), el("td", { text: b.maintainer }), el("td", { text: b.license }),
      el("td", { text: b.network + (b.unverified ? " (UNVERIFIED)" : "") }))));
  }
  if (ju && ju.judges) {
    $("ju-table").querySelector("tbody").replaceChildren(...ju.judges.map(j => {
      let trick = "not tested";
      if (j.adversarial) trick = j.adversarial.reliable ? `passed (${j.adversarial.recorded})` : `FOOLED on ${j.adversarial.missed_files} of ${j.adversarial.files} trick files`;
      return el("tr", {},
        el("td", { class: "mono", text: j.id }), el("td", { text: j.kind === "hosted" ? `online (${j.provider})` : "on this computer" }),
        el("td", { class: "mono", text: j.found_by || "" }), el("td", { text: j.consent }),
        el("td", { text: j.usable === false ? `no: ${j.reason}` : "yes" }), el("td", { text: trick }));
    }));
    $("ju-default").textContent = `Suggested: ${ju.default || "none found on this computer"}. unpick never picks an online AI by itself.`;
  }
  const agreement = last ? Object.entries(last.summary.agreement) : [];
  $("agree-table").querySelector("tbody").replaceChildren(...agreement.map(([k, v]) => el("tr", {},
    el("td", { class: "mono", text: k.replace(" ~ ", " and ") }), el("td", { text: v === null ? "neither flagged anything" : `${Math.round(v * 100)}% overlap` }))));
  $("agree-empty").hidden = agreement.length > 0;
}

loadJudges();
loadInstalledBackends();
show();
