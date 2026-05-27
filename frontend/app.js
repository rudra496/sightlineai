/* global speechSynthesis, SpeechSynthesisUtterance, webkitSpeechRecognition */

const sceneInput = document.getElementById("scene");
const locationInput = document.getElementById("locationLabel");
const routeInput = document.getElementById("routeDescription");
const hazardsInput = document.getElementById("knownHazards");
const analyzeBtn = document.getElementById("analyzeBtn");
const fallbackBtn = document.getElementById("fallbackBtn");
const accessibilityBtn = document.getElementById("accessibilityBtn");
const voiceBtn = document.getElementById("voiceBtn");
const speakBtn = document.getElementById("speakBtn");
const copyBtn = document.getElementById("copyBtn");
const pinBtn = document.getElementById("pinBtn");
const favoriteBtn = document.getElementById("favoriteBtn");
const imageAnalyzeBtn = document.getElementById("imageAnalyzeBtn");
const imageInput = document.getElementById("imageInput");
const imagePreview = document.getElementById("imagePreview");
const imageHintInput = document.getElementById("imageHint");
const charCount = document.getElementById("charCount");
const statusEl = document.getElementById("status");
const responseGrid = document.getElementById("responseGrid");
const modeBadge = document.getElementById("modeBadge");
const historyList = document.getElementById("historyList");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");
const toastContainer = document.getElementById("toastContainer");
const scrollTopBtn = document.getElementById("scrollTopBtn");
const languageSelect = document.getElementById("languageSelect");
const modeSelect = document.getElementById("modeSelect");
const historyFilter = document.getElementById("historyFilter");
const sessionInfo = document.getElementById("sessionInfo");
const exportJsonBtn = document.getElementById("exportJsonBtn");
const exportCsvBtn = document.getElementById("exportCsvBtn");
const exportMdBtn = document.getElementById("exportMdBtn");

const HISTORY_KEY = "sightlineai-history-v1";
const MAX_HISTORY = 20;

let latestGuidanceResponse = null;
let speechRecognition = null;
let listening = false;
let conversationSessionId = null;

/* ─── Utility ─── */
function debounce(fn, ms = 300) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), ms);
  };
}

/* ─── Toast ─── */
function showToast(message, type = "info") {
  if (!toastContainer) return;
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.setAttribute("role", "status");
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("toast-out");
    toast.addEventListener("animationend", () => toast.remove());
  }, 3000);
}

/* ─── Skeleton loading ─── */
function showSkeletons(count = 3) {
  responseGrid.innerHTML = Array.from({ length: count }, () =>
    `<div class="skeleton-card"><div class="skeleton-line"></div><div class="skeleton-line"></div><div class="skeleton-line"></div><div class="skeleton-line"></div></div>`
  ).join("");
}

/* ─── Status ─── */
function setStatus(text, kind = "") {
  statusEl.textContent = text;
  statusEl.className = `status${kind ? ` ${kind}` : ""}`;
}

/* ─── Geo context ─── */
function buildGeoContext() {
  const knownHazards = hazardsInput.value
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean)
    .slice(0, 8);
  return {
    location_label: locationInput.value.trim() || null,
    route_description: routeInput.value.trim() || null,
    known_hazards: knownHazards,
  };
}

/* ─── Risk bar helper ─── */
function riskLevel(score) {
  if (score == null) return "risk-medium";
  if (score <= 33) return "risk-low";
  if (score <= 66) return "risk-medium";
  return "risk-high";
}

/* ─── Render response ─── */
function renderResponse(data) {
  latestGuidanceResponse = data;

  const mode = data.mode || "unknown";
  modeBadge.textContent = `${mode} · risk ${data.risk_score ?? "--"}/100`;
  modeBadge.className = `badge mode-${mode === "qwen" ? "qwen" : "fallback"}`;

  const blocks = [
    ["Guidance", data.guidance_text],
    ["Safety notes", data.safety_notes],
    ["Confidence notes", data.confidence_notes],
  ];

  const riskScore = data.risk_score ?? 50;
  const riskHtml = `
    <div class="risk-bar-container">
      <span class="risk-bar-label">Risk ${riskScore}/100</span>
      <div class="risk-bar">
        <div class="risk-bar-fill ${riskLevel(riskScore)}" style="width:${riskScore}%"></div>
      </div>
    </div>`;

  responseGrid.innerHTML = blocks
    .map(([title, value]) => `<article class="response-card"><strong>${title}</strong><p>${value || "--"}</p></article>`)
    .join("");

  responseGrid.insertAdjacentHTML("afterbegin", riskHtml);

  if (data.image_summary) {
    responseGrid.insertAdjacentHTML(
      "beforeend",
      `<article class="response-card"><strong>Image summary</strong><p>${data.image_summary}</p></article>`,
    );
  }

  speakBtn.disabled = !("speechSynthesis" in window);
  copyBtn.disabled = false;
  pinBtn.disabled = false;
  favoriteBtn.disabled = false;

  responseGrid.setAttribute("tabindex", "-1");
  responseGrid.focus({ preventScroll: true });

  persistHistory({
    id: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2),
    created_at: new Date().toISOString(),
    scene: sceneInput.value.trim() || imageHintInput.value.trim() || "Image analysis",
    guidance: data,
    pinned: false,
    favorite: false,
  });
}

/* ─── Render accessibility score ─── */
function renderAccessibilityScore(data) {
  const section = document.getElementById("accessibilitySection");
  section.style.display = "block";

  document.getElementById("obstacleDensity").textContent = `${(data.obstacle_density * 100).toFixed(0)}%`;
  document.getElementById("pathClarity").textContent = `${(data.path_clarity * 100).toFixed(0)}%`;
  document.getElementById("overallScore").textContent = `${data.overall_score}/100`;

  const cuesEl = document.getElementById("sensoryCues");
  if (data.sensory_cues.length) {
    cuesEl.innerHTML = `<strong>Sensory cues:</strong> ${data.sensory_cues.map(c => `<span class="cue-tag">${c}</span>`).join(" ")}`;
  }

  const recsEl = document.getElementById("recommendations");
  if (data.recommendations.length) {
    recsEl.innerHTML = `<strong>Recommendations:</strong><ul>${data.recommendations.map(r => `<li>${r}</li>`).join("")}</ul>`;
  }
}

/* ─── Fallback response ─── */
function safeFallbackResponse(message) {
  return {
    guidance_text: "Fallback mode: pause, orient using cane sweep, and move in short controlled steps.",
    safety_notes: message || "Use tactile and audio confirmation before moving.",
    confidence_notes: "Low confidence — live AI unavailable.",
    mode: "fallback",
    fallback_reason: "frontend_error",
    risk_score: 50,
  };
}

/* ─── Fetch helper ─── */
async function postJson(url, body) {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed");
    return data;
  } catch (err) {
    if (err instanceof TypeError && err.message.includes("fetch")) {
      throw new Error("Network error — check your connection.");
    }
    throw err;
  }
}

/* ─── Scene analysis ─── */
async function analyzeScene(forceFallback = false) {
  const scene = sceneInput.value.trim();
  if (!scene) {
    setStatus("Please add a scene description first.", "error");
    sceneInput.focus();
    return;
  }

  analyzeBtn.disabled = true;
  fallbackBtn.disabled = true;
  const msg = forceFallback ? "Running deterministic fallback…" : "Analyzing scene…";
  setStatus(msg);
  showToast(msg, "info");
  showSkeletons(3);

  const language = languageSelect ? languageSelect.value : "en";
  const isConversation = modeSelect && modeSelect.value === "conversation";

  try {
    let data;
    if (isConversation) {
      // Use conversation endpoint
      const convBody = {
        message: scene,
        geospatial_context: buildGeoContext(),
        language: language,
      };
      if (conversationSessionId) convBody.session_id = conversationSessionId;
      const result = await postJson("/api/conversation", convBody);
      conversationSessionId = result.session_id;
      data = result.reply;
      if (sessionInfo) sessionInfo.textContent = `Session: ${conversationSessionId.slice(0, 8)}… (${result.message_count} msgs)`;
    } else if (forceFallback) {
      data = await postJson("/api/fallback-guidance", {
        scene_description: scene,
        geospatial_context: buildGeoContext(),
        language: language,
      });
    } else {
      data = await postJson("/api/guidance", {
        scene_description: scene,
        geospatial_context: buildGeoContext(),
        language: language,
      });
    }
    renderResponse(data);
    setStatus("Guidance ready.", "success");
    showToast("Guidance ready.", "success");
  } catch (err) {
    const message = err instanceof Error ? err.message : "Request failed.";
    renderResponse(safeFallbackResponse(message));
    setStatus(message, "error");
    showToast(message, "error");
  } finally {
    analyzeBtn.disabled = false;
    fallbackBtn.disabled = false;
  }
}

/* ─── Accessibility score ─── */
async function getAccessibilityScore() {
  const scene = sceneInput.value.trim();
  if (!scene) {
    setStatus("Add a scene description for accessibility scoring.", "error");
    return;
  }
  try {
    const data = await postJson("/api/accessibility-score", { scene_description: scene });
    renderAccessibilityScore(data);
    showToast("Accessibility score ready.", "success");
  } catch (err) {
    showToast("Failed to get accessibility score.", "error");
  }
}

/* ─── Image analysis ─── */
async function analyzeImage() {
  const file = imageInput.files?.[0];
  if (!file) {
    setStatus("Please choose an image first.", "error");
    return;
  }

  imageAnalyzeBtn.disabled = true;
  setStatus("Uploading image for analysis…");
  showSkeletons(3);

  const formData = new FormData();
  formData.append("image", file);
  formData.append("text_hint", imageHintInput.value.trim());
  formData.append("location_label", locationInput.value.trim());
  formData.append("route_description", routeInput.value.trim());
  if (languageSelect) formData.append("language", languageSelect.value);

  try {
    const res = await fetch("/api/analyze-image", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Image analysis failed");
    renderResponse(data);
    setStatus("Image guidance ready.", "success");
    showToast("Image guidance ready.", "success");
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Image request failed";
    renderResponse(safeFallbackResponse(msg));
    setStatus(msg, "error");
  } finally {
    imageAnalyzeBtn.disabled = false;
  }
}

/* ─── Speech ─── */
function speakResponse() {
  if (!("speechSynthesis" in window) || !latestGuidanceResponse) return;
  window.speechSynthesis.cancel();
  const text = [latestGuidanceResponse.guidance_text, latestGuidanceResponse.safety_notes, latestGuidanceResponse.confidence_notes].join(". ");
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = languageSelect && languageSelect.value === "bn" ? "bn-BD" : "en-US";
  window.speechSynthesis.speak(utter);
  showToast("Speaking guidance.", "info");
}

async function copyResponse() {
  if (!latestGuidanceResponse) return;
  const text = `Guidance: ${latestGuidanceResponse.guidance_text}\n\nSafety: ${latestGuidanceResponse.safety_notes}\n\nConfidence: ${latestGuidanceResponse.confidence_notes}`;
  try {
    await navigator.clipboard.writeText(text);
    showToast("Copied to clipboard.", "success");
  } catch {
    showToast("Clipboard unavailable.", "error");
  }
}

/* ─── History ─── */
function readHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); } catch { return []; }
}

function writeHistory(items) {
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(items.slice(0, MAX_HISTORY))); } catch (e) {
    if (e.name === "QuotaExceededError" || e.code === 22) {
      const trimmed = items.filter(x => x.pinned || x.favorite).slice(0, MAX_HISTORY);
      try { localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmed)); } catch { localStorage.removeItem(HISTORY_KEY); }
    }
  }
}

function persistHistory(item) {
  const items = [item, ...readHistory()].slice(0, MAX_HISTORY);
  writeHistory(items);
  renderHistory();
}

function pinLatest() {
  if (!latestGuidanceResponse) return;
  const items = readHistory();
  if (!items.length) return;
  items[0].pinned = true;
  writeHistory(items);
  renderHistory();
  showToast("Pinned.", "success");
}

function favoriteLatest() {
  if (!latestGuidanceResponse) return;
  const items = readHistory();
  if (!items.length) return;
  items[0].favorite = !items[0].favorite;
  writeHistory(items);
  renderHistory();
  showToast(items[0].favorite ? "Favorited ⭐" : "Unfavorited", "success");
}

function renderHistory() {
  const filter = historyFilter ? historyFilter.value : "all";
  let items = readHistory();

  if (filter === "favorites") items = items.filter(x => x.favorite);
  else if (filter === "pinned") items = items.filter(x => x.pinned);

  if (!items.length) {
    historyList.innerHTML = `<li class="history-empty"><span class="history-empty-icon" aria-hidden="true">🧠</span><p>No session memory yet.</p></li>`;
    return;
  }

  historyList.innerHTML = items.map((item, idx) => {
    const riskScore = item.guidance?.risk_score;
    const riskHtml = riskScore != null ? `<span class="risk-bar-container"><span class="risk-bar-label">Risk ${riskScore}</span><span class="risk-bar"><span class="risk-bar-fill ${riskLevel(riskScore)}" style="width:${riskScore}%"></span></span></span>` : "";
    return `<li class="history-item">
      <strong>${item.pinned ? "📌 " : ""}${item.favorite ? "⭐ " : ""}${new Date(item.created_at).toLocaleString()}</strong>
      <p>${item.scene}</p>${riskHtml}
      <div class="actions">
        <button class="btn ghost history-restore" data-index="${idx}">Restore</button>
        <button class="btn ghost history-pin" data-index="${idx}">${item.pinned ? "📌 Pinned" : "Pin"}</button>
        <button class="btn ghost history-fav" data-index="${idx}">${item.favorite ? "⭐ Fav" : "Fav"}</button>
      </div></li>`;
  }).join("");
}

function restoreHistory(index) {
  const items = readHistory();
  if (!items[index]) return;
  sceneInput.value = items[index].scene;
  updateCharCount();
  renderResponse(items[index].guidance);
  showToast("History restored.", "success");
  sceneInput.focus();
}

function pinHistory(index) {
  const items = readHistory();
  if (!items[index]) return;
  items[index].pinned = !items[index].pinned;
  writeHistory(items);
  renderHistory();
}

function favHistory(index) {
  const items = readHistory();
  if (!items[index]) return;
  items[index].favorite = !items[index].favorite;
  writeHistory(items);
  renderHistory();
}

function clearHistory() {
  localStorage.removeItem(HISTORY_KEY);
  conversationSessionId = null;
  if (sessionInfo) sessionInfo.textContent = "";
  renderHistory();
  showToast("History cleared.", "info");
}

/* ─── Export ─── */
function exportHistory(format) {
  const urls = { json: "/api/session-history/export", csv: "/api/session-history/export/csv", markdown: "/api/session-history/export/markdown" };
  const url = urls[format];
  if (!url) return;
  window.open(url, "_blank");
  showToast(`Exporting as ${format}…`, "info");
}

/* ─── Voice ─── */
function initVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceBtn.disabled = true;
    voiceBtn.querySelector("span:last-child").textContent = " Voice unavailable";
    return;
  }
  speechRecognition = new SpeechRecognition();
  speechRecognition.lang = languageSelect && languageSelect.value === "bn" ? "bn-BD" : "en-US";
  speechRecognition.continuous = false;
  speechRecognition.interimResults = false;

  speechRecognition.onstart = () => {
    listening = true;
    voiceBtn.setAttribute("aria-pressed", "true");
    voiceBtn.querySelector("span:last-child").textContent = " Stop";
    voiceBtn.querySelector("span:first-child").textContent = "⏹";
    voiceBtn.classList.add("listening");
    setStatus("Listening…");
  };

  speechRecognition.onend = () => {
    listening = false;
    voiceBtn.setAttribute("aria-pressed", "false");
    voiceBtn.querySelector("span:last-child").textContent = " Voice input";
    voiceBtn.querySelector("span:first-child").textContent = "🎙️";
    voiceBtn.classList.remove("listening");
  };

  const debouncedResult = debounce((transcript) => {
    sceneInput.value = sceneInput.value ? `${sceneInput.value} ${transcript}` : transcript;
    updateCharCount();
    setStatus("Voice captured.", "success");
  }, 200);

  speechRecognition.onresult = (event) => {
    const transcript = event.results?.[0]?.[0]?.transcript?.trim() || "";
    if (transcript) debouncedResult(transcript);
  };

  speechRecognition.onerror = () => {
    setStatus("Voice error — use text.", "error");
  };
}

function toggleVoice() {
  if (!speechRecognition) return;
  if (listening) speechRecognition.stop();
  else speechRecognition.start();
}

/* ─── Char count ─── */
function updateCharCount() {
  charCount.textContent = `${sceneInput.value.length} / 2000`;
}

/* ─── Image preview ─── */
function handleImagePreview() {
  const file = imageInput.files?.[0];
  if (!file) { imagePreview.classList.remove("visible"); imagePreview.src = ""; return; }
  const reader = new FileReader();
  reader.onload = (e) => { imagePreview.src = e.target.result; imagePreview.classList.add("visible"); };
  reader.readAsDataURL(file);
}

/* ─── Mode change ─── */
function onModeChange() {
  if (modeSelect.value === "single") {
    conversationSessionId = null;
    if (sessionInfo) sessionInfo.textContent = "";
  }
}

/* ─── Chips ─── */
document.querySelectorAll(".chip").forEach((chip) => {
  chip.setAttribute("tabindex", "0");
  chip.setAttribute("role", "button");
  chip.addEventListener("click", () => { sceneInput.value = chip.dataset.example || ""; updateCharCount(); sceneInput.focus(); });
  chip.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); chip.click(); } });
});

/* ─── Event listeners ─── */
analyzeBtn.addEventListener("click", () => analyzeScene(false));
fallbackBtn.addEventListener("click", () => analyzeScene(true));
accessibilityBtn.addEventListener("click", getAccessibilityScore);
imageAnalyzeBtn.addEventListener("click", analyzeImage);
voiceBtn.addEventListener("click", toggleVoice);
speakBtn.addEventListener("click", speakResponse);
copyBtn.addEventListener("click", copyResponse);
pinBtn.addEventListener("click", pinLatest);
favoriteBtn.addEventListener("click", favoriteLatest);
clearHistoryBtn.addEventListener("click", clearHistory);
sceneInput.addEventListener("input", updateCharCount);
imageInput.addEventListener("change", handleImagePreview);
if (modeSelect) modeSelect.addEventListener("change", onModeChange);
if (historyFilter) historyFilter.addEventListener("change", renderHistory);
if (languageSelect) languageSelect.addEventListener("change", () => { if (speechRecognition) speechRecognition.lang = languageSelect.value === "bn" ? "bn-BD" : "en-US"; });

exportJsonBtn.addEventListener("click", () => exportHistory("json"));
exportCsvBtn.addEventListener("click", () => exportHistory("csv"));
exportMdBtn.addEventListener("click", () => exportHistory("markdown"));

sceneInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") analyzeScene(false);
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && listening && speechRecognition) speechRecognition.stop();
});

document.addEventListener("click", (event) => {
  const restoreBtn = event.target.closest(".history-restore");
  const pinBtnEl = event.target.closest(".history-pin");
  const favBtnEl = event.target.closest(".history-fav");
  if (restoreBtn) restoreHistory(Number(restoreBtn.dataset.index));
  if (pinBtnEl) pinHistory(Number(pinBtnEl.dataset.index));
  if (favBtnEl) favHistory(Number(favBtnEl.dataset.index));
});

/* ─── Scroll to top ─── */
window.addEventListener("scroll", () => {
  scrollTopBtn.classList.toggle("visible", window.scrollY > 400);
}, { passive: true });

scrollTopBtn.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

/* ─── Init ─── */
renderHistory();
initVoice();
updateCharCount();
