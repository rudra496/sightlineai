/* global speechSynthesis, SpeechSynthesisUtterance */

const sceneInput     = document.getElementById("scene");
const analyzeBtn     = document.getElementById("analyzeBtn");
const speakBtn       = document.getElementById("speakBtn");
const copyBtn        = document.getElementById("copyBtn");
const statusEl       = document.getElementById("status");
const outputEl       = document.getElementById("output");
const charCountEl    = document.getElementById("charCount");
const skeletonEl     = document.getElementById("loadingSkeleton");
const exampleChips   = document.querySelectorAll(".example-chip");

const MAX_CHARS = 2000;

/** @type {{ guidance_text: string, safety_notes: string, confidence_notes: string } | null} */
let latestData = null;

// ── Utility helpers ──────────────────────────────────────────────────────────

function setStatus(message, type = "") {
  statusEl.textContent = message;
  statusEl.className = "status-bar" + (type ? " " + type : "");

  // Show/hide spinner
  const existing = statusEl.querySelector(".spinner");
  if (type === "loading") {
    if (!existing) {
      const spinner = document.createElement("span");
      spinner.className = "spinner";
      spinner.setAttribute("aria-hidden", "true");
      statusEl.prepend(spinner);
    }
  } else if (existing) {
    existing.remove();
  }
}

function updateCharCount() {
  const len = sceneInput.value.length;
  charCountEl.textContent = `${len} / ${MAX_CHARS}`;
  charCountEl.className = "char-count" +
    (len >= MAX_CHARS ? " at-limit" : len >= MAX_CHARS * 0.85 ? " near-limit" : "");

  // Announce limit milestones accessibly via the status bar
  if (len === MAX_CHARS) {
    setStatus("Character limit reached (2000).", "error");
  } else if (len === Math.floor(MAX_CHARS * 0.9)) {
    setStatus("Approaching character limit.", "");
  }
}

// ── Output rendering ─────────────────────────────────────────────────────────

function renderEmptyState() {
  outputEl.innerHTML = `
    <div class="output-block empty-state">
      <p>Enter a scene description above and click <strong>Analyze Scene</strong> to receive accessibility guidance.</p>
    </div>`;
  latestData = null;
  speakBtn.disabled = true;
  copyBtn.disabled = true;
}

/**
 * @param {{ guidance_text: string, safety_notes: string, confidence_notes: string }} data
 */
function renderOutput(data) {
  latestData = data;
  outputEl.replaceChildren();

  const blocks = [
    {
      cls: "guidance",
      icon: "🧭",
      label: "Guidance",
      value: data.guidance_text ?? "--",
    },
    {
      cls: "safety",
      icon: "⚠️",
      label: "Safety Notes",
      value: data.safety_notes ?? "--",
    },
    {
      cls: "confidence",
      icon: "📊",
      label: "Confidence Notes",
      value: data.confidence_notes ?? "--",
    },
  ];

  blocks.forEach(({ cls, icon, label, value }) => {
    const block = document.createElement("div");
    block.className = `output-block ${cls}`;

    const labelEl = document.createElement("div");
    labelEl.className = "output-block-label";
    labelEl.setAttribute("aria-hidden", "true");
    labelEl.textContent = `${icon} ${label}`;

    const textEl = document.createElement("p");
    textEl.className = "output-block-text";
    textEl.textContent = value;

    block.appendChild(labelEl);
    block.appendChild(textEl);
    outputEl.appendChild(block);
  });

  const hasSpeech = "speechSynthesis" in window;
  speakBtn.disabled = !hasSpeech || !data.guidance_text;
  copyBtn.disabled = false;
}

// ── Error output ─────────────────────────────────────────────────────────────

function renderError() {
  renderOutput({
    guidance_text: "Unable to generate guidance right now.",
    safety_notes: "Stay still, use your cane or support, and try again in a moment.",
    confidence_notes: "No confidence — guidance unavailable due to a request failure.",
  });
}

// ── API call ─────────────────────────────────────────────────────────────────

async function analyzeScene() {
  const sceneDescription = sceneInput.value.trim();
  if (!sceneDescription) {
    setStatus("Please describe your scene first.", "error");
    sceneInput.focus();
    return;
  }

  analyzeBtn.disabled = true;
  speakBtn.disabled   = true;
  copyBtn.disabled    = true;
  skeletonEl.hidden   = false;
  skeletonEl.removeAttribute("aria-hidden");
  setStatus("Analyzing scene…", "loading");

  try {
    const response = await fetch("/api/guidance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scene_description: sceneDescription }),
    });

    const body = await response.json();
    if (!response.ok) {
      const detail = typeof body?.detail === "string" ? body.detail : "Request failed";
      throw new Error(detail);
    }

    renderOutput(body);
    setStatus("Guidance ready.", "success");
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error occurred.";
    renderError();
    setStatus(message, "error");
  } finally {
    analyzeBtn.disabled = false;
    skeletonEl.hidden = true;
    skeletonEl.setAttribute("aria-hidden", "true");
  }
}

// ── Speech synthesis ─────────────────────────────────────────────────────────

function buildSpeechText(data) {
  const parts = [];
  if (data.guidance_text) parts.push(`Guidance: ${data.guidance_text}`);
  if (data.safety_notes)  parts.push(`Safety notes: ${data.safety_notes}`);
  if (data.confidence_notes) parts.push(`Confidence: ${data.confidence_notes}`);
  return parts.join(". ");
}

function speakGuidance() {
  if (!("speechSynthesis" in window) || !latestData) return;

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(buildSpeechText(latestData));
  utterance.rate  = 1.0;
  utterance.pitch = 1.0;
  utterance.lang  = "en-US";
  window.speechSynthesis.speak(utterance);
}

// ── Copy to clipboard ────────────────────────────────────────────────────────

async function copyGuidance() {
  if (!latestData) return;

  const text = [
    `Guidance: ${latestData.guidance_text}`,
    `Safety notes: ${latestData.safety_notes}`,
    `Confidence: ${latestData.confidence_notes}`,
  ].join("\n\n");

  try {
    await navigator.clipboard.writeText(text);
    copyBtn.innerHTML = '<span class="btn-icon" aria-hidden="true">✅</span> Copied!';
    setTimeout(() => {
      copyBtn.innerHTML = '<span class="btn-icon" aria-hidden="true">📋</span> Copy';
    }, 2000);
  } catch {
    setStatus("Copy failed — please copy the text manually.", "error");
  }
}

// ── Example chips ────────────────────────────────────────────────────────────

exampleChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    sceneInput.value = chip.dataset.example || "";
    updateCharCount();
    sceneInput.focus();
  });
});

// ── Event listeners ──────────────────────────────────────────────────────────

analyzeBtn.addEventListener("click", analyzeScene);
speakBtn.addEventListener("click", speakGuidance);
copyBtn.addEventListener("click", copyGuidance);

sceneInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    analyzeScene();
  }
});

sceneInput.addEventListener("input", updateCharCount);

// ── Init ─────────────────────────────────────────────────────────────────────

updateCharCount();
