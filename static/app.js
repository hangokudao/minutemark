const elements = {
  fileInput: document.querySelector("#audio-file"),
  chooseFile: document.querySelector("#choose-file"),
  budgetStatus: document.querySelector("#budget-status"),
  dropZone: document.querySelector("#drop-zone"),
  dropLabel: document.querySelector("#drop-label"),
  sampleList: document.querySelector("#sample-list"),
  statusPanel: document.querySelector("#status-panel"),
  elapsedTime: document.querySelector("#elapsed-time"),
  errorPanel: document.querySelector("#error-panel"),
  errorMessage: document.querySelector("#error-message"),
  retryButton: document.querySelector("#retry-button"),
  resultPanel: document.querySelector("#result-panel"),
  resultTitle: document.querySelector("#result-title"),
  sourceAttribution: document.querySelector("#source-attribution"),
  resultMetrics: document.querySelector("#result-metrics"),
  audioPlayer: document.querySelector("#audio-player"),
  transcriptList: document.querySelector("#transcript-list"),
  segmentCount: document.querySelector("#segment-count"),
  decisionList: document.querySelector("#decision-list"),
  actionList: document.querySelector("#action-list"),
  decisionCount: document.querySelector("#decision-count"),
  actionCount: document.querySelector("#action-count"),
  groundingStatus: document.querySelector("#grounding-status"),
  modelDetail: document.querySelector("#model-detail"),
};

let elapsedTimer = null;
let lastAction = null;
let uploadObjectUrl = null;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatTimestamp(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.floor(seconds % 60);
  return `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}

function beginLoading(label) {
  clearInterval(elapsedTimer);
  elements.errorPanel.hidden = true;
  elements.resultPanel.hidden = true;
  elements.statusPanel.hidden = false;
  elements.statusPanel.querySelector("#status-title").textContent =
    `${label} 분석 중`;
  const started = Date.now();
  elements.elapsedTime.textContent = "00:00";
  elapsedTimer = setInterval(() => {
    const seconds = Math.floor((Date.now() - started) / 1000);
    elements.elapsedTime.textContent = formatTimestamp(seconds);
  }, 1000);
}

function endLoading() {
  clearInterval(elapsedTimer);
  elapsedTimer = null;
  elements.statusPanel.hidden = true;
}

function showError(message) {
  endLoading();
  elements.errorMessage.textContent = message;
  elements.errorPanel.hidden = false;
  elements.errorPanel.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function readError(response) {
  try {
    const payload = await response.json();
    return payload.detail || "알 수 없는 오류가 발생했습니다.";
  } catch {
    return `서버 오류가 발생했습니다. (${response.status})`;
  }
}

async function analyzeSample(sample) {
  lastAction = () => analyzeSample(sample);
  beginLoading(sample.title);
  try {
    const response = await fetch(`/api/analyze-sample/${sample.id}`, {
      method: "POST",
    });
    if (!response.ok) throw new Error(await readError(response));
    renderResult(await response.json());
  } catch (error) {
    showError(error.message);
  }
}

async function analyzeUpload(file) {
  lastAction = () => analyzeUpload(file);
  beginLoading(file.name);
  const formData = new FormData();
  formData.append("audio", file);
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) throw new Error(await readError(response));
    const result = await response.json();
    if (uploadObjectUrl) URL.revokeObjectURL(uploadObjectUrl);
    uploadObjectUrl = URL.createObjectURL(file);
    result.audio_url = uploadObjectUrl;
    renderResult(result);
  } catch (error) {
    showError(error.message);
  }
}

function renderSamples(samples) {
  elements.sampleList.innerHTML = samples
    .map(
      (sample) => `
        <button
          class="sample-button"
          type="button"
          data-sample-id="${escapeHtml(sample.id)}"
          ${sample.available ? "" : "disabled"}
        >
          <span class="sample-topline">
            <strong>${escapeHtml(sample.title)}</strong>
            <span class="sample-duration">${sample.available ? "약 34초 · 실제 분석" : "파일 없음"}</span>
          </span>
          <p>${escapeHtml(sample.description)}</p>
          <span class="sample-source">${escapeHtml(sample.source_title)}</span>
        </button>
      `,
    )
    .join("");

  elements.sampleList.querySelectorAll("[data-sample-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const sample = samples.find((item) => item.id === button.dataset.sampleId);
      if (sample) analyzeSample(sample);
    });
  });
}

async function loadSamples() {
  try {
    const response = await fetch("/api/samples");
    if (!response.ok) throw new Error(await readError(response));
    renderSamples(await response.json());
  } catch (error) {
    elements.sampleList.innerHTML =
      `<p class="empty-result">샘플 목록을 불러오지 못했습니다: ${escapeHtml(error.message)}</p>`;
  }
}

async function loadBudget() {
  try {
    const response = await fetch("/api/budget");
    if (!response.ok) return;
    const budget = await response.json();
    elements.budgetStatus.textContent = budget.persistence === "persistent"
      ? `실제 AI 추론 · $${budget.remaining_usd.toFixed(4)} 남음`
      : "실제 AI 추론 · A6 토큰 한도 적용";
  } catch {
    elements.budgetStatus.textContent = "실제 AI 추론 · 월 $1 제한";
  }
}

function renderEmpty(message) {
  return `<p class="empty-result">${escapeHtml(message)}</p>`;
}

function renderInsight(item, type) {
  const meta = [];
  if (item.owner) meta.push(`<span>담당 ${escapeHtml(item.owner)}</span>`);
  if (item.due) meta.push(`<span>기한 ${escapeHtml(item.due)}</span>`);
  const evidenceIds = item.segment_ids || [];
  return `
    <article class="insight-card ${type}">
      <p>${escapeHtml(item.text)}</p>
      ${meta.length ? `<div class="item-meta">${meta.join("")}</div>` : ""}
      <button
        type="button"
        class="evidence-button"
        data-evidence="${escapeHtml(evidenceIds.join(","))}"
      >
        근거 듣기 · ${escapeHtml(evidenceIds.join(", "))}
      </button>
    </article>
  `;
}

function focusEvidence(segmentIds) {
  document.querySelectorAll(".segment.is-evidence").forEach((segment) => {
    segment.classList.remove("is-evidence");
  });

  const targets = segmentIds
    .map((id) => document.querySelector(`[data-segment-id="${CSS.escape(id)}"]`))
    .filter(Boolean);
  targets.forEach((target) => target.classList.add("is-evidence"));
  if (!targets.length) return;

  const start = Number(targets[0].dataset.start || 0);
  elements.audioPlayer.currentTime = start;
  elements.audioPlayer.play().catch(() => {});
  targets[0].scrollIntoView({
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto"
      : "smooth",
    block: "center",
  });
}

function bindEvidenceButtons() {
  document.querySelectorAll("[data-evidence]").forEach((button) => {
    button.addEventListener("click", () => {
      focusEvidence(button.dataset.evidence.split(",").filter(Boolean));
    });
  });
}

function renderResult(result) {
  endLoading();
  elements.errorPanel.hidden = true;
  elements.resultTitle.textContent = result.audio;
  elements.audioPlayer.src = result.audio_url || "";

  if (result.sample) {
    elements.sourceAttribution.innerHTML = `
      출처:
      <a href="${escapeHtml(result.sample.source_url)}" target="_blank" rel="noreferrer">
        ${escapeHtml(result.sample.source_title)}
      </a>
      · ${escapeHtml(result.sample.author)}
      ·
      <a href="${escapeHtml(result.sample.license_url)}" target="_blank" rel="noreferrer">
        ${escapeHtml(result.sample.license)}
      </a>
      · ${escapeHtml(result.sample.modification)}
    `;
  } else {
    elements.sourceAttribution.textContent =
      "업로드 파일 · 분석 후 서버에 보관하지 않음";
  }

  const totalTokens =
    (result.usage.prompt_tokens || 0) + (result.usage.completion_tokens || 0);
  const budgetMetric = result.budget.persistence === "persistent"
    ? `<span class="metric"><strong>$${result.budget.remaining_usd.toFixed(4)}</strong> 월 예산 남음</span>`
    : "";
  elements.resultMetrics.innerHTML = `
    <span class="metric"><strong>${result.timing_seconds.total.toFixed(2)}초</strong> 처리</span>
    <span class="metric"><strong>${totalTokens.toLocaleString("ko-KR")}</strong> 토큰</span>
    <span class="metric"><strong>$${result.estimated_cost_usd.toFixed(8)}</strong> 예상</span>
    ${budgetMetric}
  `;
  elements.budgetStatus.textContent =
    result.budget.persistence === "persistent"
      ? `실제 AI 추론 · $${result.budget.remaining_usd.toFixed(4)} 남음`
      : "실제 AI 추론 · A6 토큰 한도 적용";

  elements.transcriptList.innerHTML = result.segments
    .map(
      (segment) => `
        <div
          class="segment"
          data-segment-id="${escapeHtml(segment.id)}"
          data-start="${segment.start}"
        >
          <time datetime="PT${segment.start}S">${formatTimestamp(segment.start)}</time>
          <p>${escapeHtml(segment.text)}</p>
        </div>
      `,
    )
    .join("");
  elements.segmentCount.textContent = `${result.segments.length}개 구간`;

  const decisions = result.extraction.decisions || [];
  const actions = result.extraction.action_items || [];
  elements.decisionList.innerHTML = decisions.length
    ? decisions.map((item) => renderInsight(item, "decision")).join("")
    : renderEmpty("명시적으로 확정된 결정을 찾지 못했습니다.");
  elements.actionList.innerHTML = actions.length
    ? actions.map((item) => renderInsight(item, "action")).join("")
    : renderEmpty("앞으로 수행할 구체적인 일을 찾지 못했습니다.");
  elements.decisionCount.textContent = decisions.length;
  elements.actionCount.textContent = actions.length;

  const groundingValid = result.grounding.valid;
  elements.groundingStatus.className = groundingValid
    ? "valid-badge"
    : "invalid-badge";
  elements.groundingStatus.textContent = groundingValid
    ? "모든 근거 유효"
    : "근거 확인 필요";
  elements.modelDetail.textContent =
    `${result.models.transcription} → ${result.models.extraction}`;

  bindEvidenceButtons();
  elements.resultPanel.hidden = false;
  elements.resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function validateAndAnalyze(file) {
  if (!file) return;
  const suffix = `.${file.name.split(".").pop()?.toLowerCase()}`;
  const allowed = [".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"];
  if (!allowed.includes(suffix)) {
    showError("WAV, MP3, M4A, OGG, FLAC, WEBM 파일만 지원합니다.");
    return;
  }
  if (file.size > 20 * 1024 * 1024) {
    showError("파일은 20MB 이하여야 합니다.");
    return;
  }
  elements.dropLabel.textContent = file.name;
  analyzeUpload(file);
}

elements.chooseFile.addEventListener("click", (event) => {
  event.stopPropagation();
  elements.fileInput.click();
});
elements.dropZone.addEventListener("click", () => elements.fileInput.click());
elements.fileInput.addEventListener("change", () => {
  validateAndAnalyze(elements.fileInput.files[0]);
});
["dragenter", "dragover"].forEach((eventName) => {
  elements.dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    elements.dropZone.classList.add("is-dragging");
  });
});
["dragleave", "drop"].forEach((eventName) => {
  elements.dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    elements.dropZone.classList.remove("is-dragging");
  });
});
elements.dropZone.addEventListener("drop", (event) => {
  validateAndAnalyze(event.dataTransfer.files[0]);
});
elements.retryButton.addEventListener("click", () => {
  if (lastAction) lastAction();
});

loadSamples();
loadBudget();
