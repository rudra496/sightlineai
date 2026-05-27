/* global speechSynthesis, SpeechSynthesisUtterance, webkitSpeechRecognition */

const sceneInput = document.getElementById("scene");
const locationInput = document.getElementById("locationLabel");
const routeInput = document.getElementById("routeDescription");
const hazardsInput = document.getElementById("knownHazards");
const analyzeBtn = document.getElementById("analyzeBtn");
const fallbackBtn = document.getElementById("fallbackBtn");
const voiceBtn = document.getElementById("voiceBtn");
const speakBtn = document.getElementById("speakBtn");
const copyBtn = document.getElementById("copyBtn");
const pinBtn = document.getElementById("pinBtn");
const imageAnalyzeBtn = document.getElementById("imageAnalyzeBtn");
const imageInput = document.getElementById("imageInput");
const imageHintInput = document.getElementById("imageHint");
const charCount = document.getElementById("charCount");
const statusEl = document.getElementById("status");
const responseGrid = document.getElementById("responseGrid");
const modeBadge = document.getElementById("modeBadge");
const historyList = document.getElementById("historyList");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");

const HISTORY_KEY = "sightlineai-history-v1";
const MAX_HISTORY = 20;

let latestData = null;
let recognition = null;
let listening = false;

function setStatus(text, kind = "") {
  statusEl.textContent = text;
  statusEl.className = `status${kind ? ` ${kind}` : ""}`;
}

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

function renderResponse(data) {
  latestData = data;
  modeBadge.textContent = `${data.mode || "unknown"} · risk ${data.risk_score ?? "--"}/100`;

  const blocks = [
    ["Guidance", data.guidance_text],
    ["Safety notes", data.safety_notes],
    ["Confidence notes", data.confidence_notes],
  ];

  responseGrid.innerHTML = blocks
    .map(([title, value]) => `<article class="response-card"><strong>${title}</strong><p>${value || "--"}</p></article>`)
    .join("");

  if (data.image_summary) {
    responseGrid.insertAdjacentHTML(
      "beforeend",
      `<article class="response-card"><strong>Image summary</strong><p>${data.image_summary}</p></article>`,
    );
  }

  speakBtn.disabled = !("speechSynthesis" in window);
  copyBtn.disabled = false;
  pinBtn.disabled = false;

  persistHistory({
    id: crypto.randomUUID(),
    created_at: new Date().toISOString(),
    scene: sceneInput.value.trim() || imageHintInput.value.trim() || "Image analysis",
    guidance: data,
    pinned: false,
  });
}

function safeFallbackResponse(message) {
  return {
    guidance_text: "Fallback mode: pause, orient using cane sweep, and move in short controlled steps.",
    safety_notes: message || "Use tactile and audio confirmation before moving into uncertain space.",
    confidence_notes: "Low confidence because live AI response was unavailable.",
    mode: "fallback",
    fallback_reason: "frontend_error",
    risk_score: 50,
  };
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

async function analyzeScene(forceFallback = false) {
  const scene = sceneInput.value.trim();
  if (!scene) {
    setStatus("Please add a scene description first.", "error");
    sceneInput.focus();
    return;
  }

  analyzeBtn.disabled = true;
  fallbackBtn.disabled = true;
  setStatus(forceFallback ? "Running deterministic fallback…" : "Analyzing scene…");

  try {
    const url = forceFallback ? "/api/fallback-guidance" : "/api/guidance";
    const data = await postJson(url, {
      scene_description: scene,
      geospatial_context: buildGeoContext(),
    });
    renderResponse(data);
    setStatus("Guidance ready.", "success");
  } catch (err) {
    const message = err instanceof Error ? err.message : "Request failed.";
    const fallback = safeFallbackResponse(message);
    renderResponse(fallback);
    setStatus(message, "error");
  } finally {
    analyzeBtn.disabled = false;
    fallbackBtn.disabled = false;
  }
}

async function analyzeImage() {
  const file = imageInput.files?.[0];
  if (!file) {
    setStatus("Please choose an image first.", "error");
    return;
  }

  imageAnalyzeBtn.disabled = true;
  setStatus("Uploading image for analysis…");

  const formData = new FormData();
  formData.append("image", file);
  formData.append("text_hint", imageHintInput.value.trim());
  formData.append("location_label", locationInput.value.trim());
  formData.append("route_description", routeInput.value.trim());

  try {
    const res = await fetch("/api/analyze-image", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Image analysis failed");
    renderResponse(data);
    setStatus("Image guidance ready.", "success");
  } catch (err) {
    setStatus(err instanceof Error ? err.message : "Image request failed", "error");
  } finally {
    imageAnalyzeBtn.disabled = false;
  }
}

function speakResponse() {
  if (!("speechSynthesis" in window) || !latestData) return;
  window.speechSynthesis.cancel();
  const text = [latestData.guidance_text, latestData.safety_notes, latestData.confidence_notes].join(". ");
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = "en-US";
  window.speechSynthesis.speak(utter);
}

async function copyResponse() {
  if (!latestData) return;
  const text = `Guidance: ${latestData.guidance_text}\n\nSafety: ${latestData.safety_notes}\n\nConfidence: ${latestData.confidence_notes}`;
  try {
    await navigator.clipboard.writeText(text);
    setStatus("Response copied.", "success");
  } catch {
    setStatus("Clipboard unavailable.", "error");
  }
}

function readHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  } catch {
    return [];
  }
}

function writeHistory(items) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(items.slice(0, MAX_HISTORY)));
}

function persistHistory(item) {
  const items = [item, ...readHistory()].slice(0, MAX_HISTORY);
  writeHistory(items);
  renderHistory();
}

function pinLatest() {
  if (!latestData) return;
  const items = readHistory();
  if (!items.length) return;
  items[0].pinned = true;
  writeHistory(items);
  renderHistory();
  setStatus("Pinned latest guidance.", "success");
}

function renderHistory() {
  const items = readHistory();
  if (!items.length) {
    historyList.innerHTML = '<li class="history-item">No session memory yet.</li>';
    return;
  }

  historyList.innerHTML = items
    .map((item, idx) => {
      const pinLabel = item.pinned ? "📌 Pinned" : "Pin";
      return `
        <li class="history-item">
          <strong>${item.pinned ? "📌 " : ""}${new Date(item.created_at).toLocaleString()}</strong>
          <p>${item.scene}</p>
          <button class="btn ghost history-restore" data-index="${idx}">Restore</button>
          <button class="btn ghost history-pin" data-index="${idx}">${pinLabel}</button>
        </li>`;
    })
    .join("");
}

function restoreHistory(index) {
  const item = readHistory()[index];
  if (!item) return;
  sceneInput.value = item.scene;
  renderResponse(item.guidance);
  setStatus("History item restored.", "success");
}

function pinHistory(index) {
  const items = readHistory();
  if (!items[index]) return;
  items[index].pinned = !items[index].pinned;
  writeHistory(items);
  renderHistory();
}

function clearHistory() {
  localStorage.removeItem(HISTORY_KEY);
  renderHistory();
  setStatus("Local history cleared.", "success");
}

function initVoice() {
  const SpeechRecognition = window.SpeechRecognition || webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceBtn.disabled = true;
    voiceBtn.textContent = "🎙️ Voice unavailable";
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    listening = true;
    voiceBtn.setAttribute("aria-pressed", "true");
    voiceBtn.textContent = "⏹ Stop listening";
    setStatus("Listening… speak now.");
  };

  recognition.onend = () => {
    listening = false;
    voiceBtn.setAttribute("aria-pressed", "false");
    voiceBtn.textContent = "🎙️ Voice input";
  };

  recognition.onresult = (event) => {
    const transcript = event.results?.[0]?.[0]?.transcript?.trim();
    if (!transcript) return;
    sceneInput.value = sceneInput.value ? `${sceneInput.value} ${transcript}` : transcript;
    updateCharCount();
    setStatus("Voice captured.", "success");
  };

  recognition.onerror = () => setStatus("Voice recognition error. You can continue with text input.", "error");
}

function toggleVoice() {
  if (!recognition) return;
  if (listening) recognition.stop();
  else recognition.start();
}

function updateCharCount() {
  charCount.textContent = `${sceneInput.value.length} / 2000`;
}

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    sceneInput.value = chip.dataset.example || "";
    updateCharCount();
    sceneInput.focus();
  });
});

analyzeBtn.addEventListener("click", () => analyzeScene(false));
fallbackBtn.addEventListener("click", () => analyzeScene(true));
imageAnalyzeBtn.addEventListener("click", analyzeImage);
voiceBtn.addEventListener("click", toggleVoice);
speakBtn.addEventListener("click", speakResponse);
copyBtn.addEventListener("click", copyResponse);
pinBtn.addEventListener("click", pinLatest);
clearHistoryBtn.addEventListener("click", clearHistory);
sceneInput.addEventListener("input", updateCharCount);
sceneInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") analyzeScene(false);
});

document.addEventListener("click", (event) => {
  const restoreBtn = event.target.closest(".history-restore");
  const pinBtnEl = event.target.closest(".history-pin");
  if (restoreBtn) restoreHistory(Number(restoreBtn.dataset.index));
  if (pinBtnEl) pinHistory(Number(pinBtnEl.dataset.index));
});

renderHistory();
initVoice();
updateCharCount();
