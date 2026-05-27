const sceneInput = document.getElementById("scene");
const analyzeBtn = document.getElementById("analyzeBtn");
const speakBtn = document.getElementById("speakBtn");
const statusEl = document.getElementById("status");
const outputEl = document.getElementById("output");

let latestGuidanceText = "";

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function renderOutput(data) {
  latestGuidanceText = data.guidance_text || "";
  outputEl.replaceChildren();

  const rows = [
    ["Guidance text", data.guidance_text ?? "--"],
    ["Safety notes", data.safety_notes ?? "--"],
    ["Confidence notes", data.confidence_notes ?? "--"],
  ];

  rows.forEach(([label, value]) => {
    const p = document.createElement("p");
    const strong = document.createElement("strong");
    strong.textContent = `${label}:`;
    p.appendChild(strong);
    p.append(` ${value}`);
    outputEl.appendChild(p);
  });

  speakBtn.disabled = !("speechSynthesis" in window) || !latestGuidanceText;
}

async function analyzeScene() {
  const sceneDescription = sceneInput.value.trim();
  if (!sceneDescription) {
    setStatus("Please describe your scene first.", true);
    return;
  }

  analyzeBtn.disabled = true;
  speakBtn.disabled = true;
  setStatus("Analyzing scene...");

  try {
    const response = await fetch("/api/guidance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scene_description: sceneDescription }),
    });

    const body = await response.json();
    if (!response.ok) {
      const detail = body?.detail?.detail || body?.detail || "Request failed";
      throw new Error(detail);
    }

    renderOutput(body);
    setStatus("Guidance ready.");
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    renderOutput({
      guidance_text: "Unable to generate guidance right now.",
      safety_notes: "Please stay still, assess with cane or support, and retry.",
      confidence_notes: "No confidence due to request failure.",
    });
    setStatus(message, true);
  } finally {
    analyzeBtn.disabled = false;
  }
}

function speakGuidance() {
  if (!("speechSynthesis" in window) || !latestGuidanceText) {
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(latestGuidanceText);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  utterance.lang = "en-US";
  window.speechSynthesis.speak(utterance);
}

analyzeBtn.addEventListener("click", analyzeScene);
speakBtn.addEventListener("click", speakGuidance);
sceneInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    analyzeScene();
  }
});
