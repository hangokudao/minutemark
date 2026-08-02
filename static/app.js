let initializeApp;
let GoogleAuthProvider;
let getAuth;
let onAuthStateChanged;
let reauthenticateWithPopup;
let signInWithPopup;
let signOut;

const elements = {
  fileInput: document.querySelector("#audio-file"),
  chooseFile: document.querySelector("#choose-file"),
  analyzeSave: document.querySelector("#analyze-save-button"),
  signinUpload: document.querySelector("#signin-upload-button"),
  budgetStatus: document.querySelector("#budget-status"),
  dropZone: document.querySelector("#drop-zone"),
  dropLabel: document.querySelector("#drop-label"),
  dropHelp: document.querySelector("#drop-help"),
  meetingTitle: document.querySelector("#meeting-title"),
  participantNotice: document.querySelector("#participant-notice"),
  pageTitle: document.querySelector("#page-title"),
  pageDescription: document.querySelector("#page-description"),
  workspaceIntro: document.querySelector(".workspace-intro"),
  inputPanel: document.querySelector("#input-panel"),
  inputTitle: document.querySelector("#input-title"),
  inputDescription: document.querySelector("#input-description"),
  meetingsPanel: document.querySelector("#meetings-panel"),
  meetingsNew: document.querySelector("#meetings-new-button"),
  sampleList: document.querySelector("#sample-list"),
  statusPanel: document.querySelector("#status-panel"),
  elapsedTime: document.querySelector("#elapsed-time"),
  errorPanel: document.querySelector("#error-panel"),
  errorMessage: document.querySelector("#error-message"),
  retryButton: document.querySelector("#retry-button"),
  resultPanel: document.querySelector("#result-panel"),
  backToInput: document.querySelector("#back-to-input"),
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
  savedStatus: document.querySelector("#saved-status"),
  modelDetail: document.querySelector("#model-detail"),
  meetingList: document.querySelector("#meeting-list"),
  meetingListPage: document.querySelector("#meeting-list-page"),
  meetingLimit: document.querySelector("#meeting-limit"),
  newMeeting: document.querySelector("#new-meeting-button"),
  deleteMeeting: document.querySelector("#delete-meeting-button"),
  accountButton: document.querySelector("#account-button"),
  accountLabel: document.querySelector("#account-label"),
  accountEmail: document.querySelector("#account-email"),
  authDialog: document.querySelector("#auth-dialog"),
  googleSignin: document.querySelector("#google-signin"),
  authError: document.querySelector("#auth-error"),
  accountDialog: document.querySelector("#account-dialog"),
  accountError: document.querySelector("#account-error"),
  signout: document.querySelector("#signout-button"),
  deleteAccount: document.querySelector("#delete-account-button"),
  deleteAccountConfirm: document.querySelector("#delete-account-confirm"),
  deleteMeetingDialog: document.querySelector("#delete-meeting-dialog"),
  deleteMeetingConfirm: document.querySelector("#confirm-delete-meeting"),
  deleteMeetingCancel: document.querySelector("#cancel-delete-meeting"),
  deleteMeetingError: document.querySelector("#delete-meeting-error"),
  privacyDialog: document.querySelector("#privacy-dialog"),
  privacyButton: document.querySelector("#privacy-button"),
  authPrivacyButton: document.querySelector("#auth-privacy-button"),
  accountPrivacyButton: document.querySelector("#account-privacy-button"),
  privacyClose: document.querySelector("#privacy-close"),
  authClose: document.querySelector("#auth-close"),
  accountClose: document.querySelector("#account-close"),
  mobileMenuButton: document.querySelector("#mobile-menu-button"),
  mobileMenuDialog: document.querySelector("#mobile-menu-dialog"),
  mobileMenuClose: document.querySelector("#mobile-menu-close"),
  mobileSignout: document.querySelector("#mobile-signout-button"),
};

let auth = null;
let provider = null;
let currentUser = null;
let currentMeetingId = null;
let selectedFile = null;
let elapsedTimer = null;
let lastAction = null;
let memberFeaturesEnabled = false;
let uploadRequestId = null;
let authReady = false;
let currentPath = location.pathname + location.search;
let isSubmittingMeeting = false;
let privacyReturnPath = "/samples";

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

function formatDate(value) {
  if (!value) return "방금 전";
  return new Intl.DateTimeFormat("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function meetingIdFromPath(pathname) {
  const match = pathname.match(/^\/meetings\/([0-9a-f]{32})$/);
  return match ? match[1] : null;
}

function isMemberPath(pathname) {
  return pathname === "/meetings"
    || pathname === "/meetings/new"
    || pathname === "/account"
    || Boolean(meetingIdFromPath(pathname));
}

function hasMeetingDraft() {
  return Boolean(
    selectedFile
    || elements.meetingTitle.value.trim()
    || elements.participantNotice.checked,
  );
}

function clearMeetingDraft() {
  selectedFile = null;
  uploadRequestId = null;
  elements.fileInput.value = "";
  elements.meetingTitle.value = "";
  elements.participantNotice.checked = false;
  elements.dropLabel.textContent = currentUser
    ? "파일을 끌어놓거나 선택"
    : "Google 로그인 후 파일 선택";
  elements.dropHelp.textContent = currentUser
    ? "분석 완료 시 원본 오디오와 전사·결과를 내 회의 기록에 저장합니다."
    : "공개 샘플은 로그인 없이 확인할 수 있습니다.";
  updateAnalyzeButton();
}

function closeMobileMenu() {
  if (elements.mobileMenuDialog.open) elements.mobileMenuDialog.close();
  elements.mobileMenuButton.setAttribute("aria-expanded", "false");
}

function setActiveRoute(pathname) {
  document.querySelectorAll(".route-link").forEach((link) => {
    const linkPath = new URL(link.href, location.origin).pathname;
    const active = linkPath === pathname
      || (linkPath === "/meetings" && Boolean(meetingIdFromPath(pathname)));
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
}

function resetRouteSurfaces() {
  document.body.classList.remove("result-view");
  elements.workspaceIntro.hidden = true;
  elements.inputPanel.hidden = true;
  elements.meetingsPanel.hidden = true;
  elements.resultPanel.hidden = true;
  elements.errorPanel.hidden = true;
  if (!isSubmittingMeeting) elements.statusPanel.hidden = true;
}

async function renderRoute(rawPath = location.pathname + location.search) {
  const url = new URL(rawPath, location.origin);
  let { pathname } = url;
  if (pathname === "/") {
    await navigate(currentUser ? "/meetings" : "/samples", {
      replace: true,
      skipDraftGuard: true,
    });
    return;
  }
  if (isMemberPath(pathname) && !currentUser) {
    if (!authReady) return;
    if (memberFeaturesEnabled) {
      await navigate(`/auth?next=${encodeURIComponent(pathname)}`, {
        replace: true,
        skipDraftGuard: true,
      });
    } else {
      await navigate("/samples", { replace: true, skipDraftGuard: true });
    }
    return;
  }

  resetRouteSurfaces();
  setActiveRoute(pathname);
  document.body.dataset.route = pathname;

  if (pathname !== "/auth" && elements.authDialog.open) elements.authDialog.close();
  if (pathname !== "/account" && elements.accountDialog.open) elements.accountDialog.close();
  if (pathname !== "/privacy" && elements.privacyDialog.open) elements.privacyDialog.close();

  if (pathname === "/samples") {
    elements.workspaceIntro.hidden = false;
    elements.inputPanel.hidden = false;
    elements.pageTitle.textContent = "실제 회의 분석을 확인하세요";
    elements.pageDescription.textContent = "공개 음성의 실제 분석 결과와 근거 발화를 로그인 없이 확인할 수 있습니다.";
    elements.inputTitle.textContent = "공개 샘플";
    elements.inputDescription.textContent = "로그인 없이 확인 · 내 기록에는 저장하지 않음";
    document.title = "공개 샘플 · MinuteMark";
    return;
  }
  if (pathname === "/meetings/new") {
    elements.workspaceIntro.hidden = false;
    elements.inputPanel.hidden = false;
    elements.pageTitle.textContent = "새 회의를 분석하세요";
    elements.pageDescription.textContent = "회의 제목과 오디오를 선택하면 분석이 끝난 뒤 내 회의 기록에 저장합니다.";
    elements.inputTitle.textContent = "새 회의 분석";
    elements.inputDescription.textContent = "Google 계정에 최대 5개 저장 · 파일당 20MB · 2분";
    document.title = "새 회의 · MinuteMark";
    elements.meetingTitle.focus();
    return;
  }
  if (pathname === "/meetings") {
    elements.meetingsPanel.hidden = false;
    document.title = "회의 기록 · MinuteMark";
    await loadMeetings();
    return;
  }
  const meetingId = meetingIdFromPath(pathname);
  if (meetingId) {
    document.title = "회의 불러오는 중 · MinuteMark";
    await openMeeting(meetingId, false);
    return;
  }
  if (pathname === "/auth") {
    elements.workspaceIntro.hidden = false;
    elements.inputPanel.hidden = false;
    if (!memberFeaturesEnabled) {
      await navigate("/samples", { replace: true, skipDraftGuard: true });
      showError("회원 기능을 준비하고 있습니다. 잠시 후 다시 시도해 주세요.");
      return;
    }
    if (currentUser) {
      await navigate(url.searchParams.get("next") || "/meetings", {
        replace: true,
        skipDraftGuard: true,
      });
      return;
    }
    if (!elements.authDialog.open) elements.authDialog.showModal();
    return;
  }
  if (pathname === "/account") {
    elements.meetingsPanel.hidden = false;
    if (!elements.accountDialog.open) elements.accountDialog.showModal();
    return;
  }
  if (pathname === "/privacy") {
    elements.workspaceIntro.hidden = false;
    elements.inputPanel.hidden = false;
    if (!elements.privacyDialog.open) elements.privacyDialog.showModal();
    document.title = "개인정보처리방침 · MinuteMark";
    return;
  }
  await navigate("/samples", { replace: true, skipDraftGuard: true });
}

async function navigate(path, { replace = false, skipDraftGuard = false } = {}) {
  const target = new URL(path, location.origin);
  const leavingNewMeeting = location.pathname === "/meetings/new"
    && target.pathname !== "/meetings/new";
  if (
    leavingNewMeeting
    && hasMeetingDraft()
    && !skipDraftGuard
    && !window.confirm("선택한 파일과 입력한 내용이 사라집니다. 이동할까요?")
  ) {
    return false;
  }
  if (leavingNewMeeting && target.pathname !== "/meetings/new") clearMeetingDraft();
  const nextPath = target.pathname + target.search;
  history[replace ? "replaceState" : "pushState"]({}, "", nextPath);
  currentPath = nextPath;
  closeMobileMenu();
  await renderRoute(nextPath);
  return true;
}

function updateAnalyzeButton() {
  const ready = Boolean(
    currentUser
    && selectedFile
    && elements.meetingTitle.value.trim()
    && elements.participantNotice.checked
    && !isSubmittingMeeting,
  );
  elements.analyzeSave.disabled = !ready;
}

function setSubmittingMeeting(active) {
  isSubmittingMeeting = active;
  elements.newMeeting.textContent = active ? "분석 중" : "새 회의";
  elements.newMeeting.setAttribute("aria-disabled", String(active));
  elements.meetingsNew.disabled = active;
  updateAnalyzeButton();
}

function beginLoading(label, meetingSubmission = false) {
  clearInterval(elapsedTimer);
  if (meetingSubmission) setSubmittingMeeting(true);
  elements.errorPanel.hidden = true;
  elements.resultPanel.hidden = true;
  elements.statusPanel.hidden = false;
  elements.statusPanel.querySelector("#status-title").textContent = meetingSubmission
    ? `${label} 분석·저장 중`
    : `${label} 분석 중`;
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
  if (isSubmittingMeeting) setSubmittingMeeting(false);
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

async function authFetch(url, options = {}) {
  if (!currentUser) throw new Error("Google 로그인이 필요합니다.");
  const token = await currentUser.getIdToken();
  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${token}`);
  return fetch(url, { ...options, headers });
}

async function analyzeSample(sample) {
  lastAction = () => analyzeSample(sample);
  beginLoading(sample.title);
  try {
    const response = await fetch(`/api/analyze-sample/${sample.id}`, { method: "POST" });
    if (!response.ok) throw new Error(await readError(response));
    renderResult(await response.json());
  } catch (error) {
    showError(error.message);
  }
}

async function analyzeUpload(file) {
  if (!currentUser) {
    openAuthDialog();
    return;
  }
  if (isSubmittingMeeting) return;
  const title = elements.meetingTitle.value.trim();
  if (!title) {
    showError("회의 제목을 입력해 주세요.");
    elements.meetingTitle.focus();
    return;
  }
  if (!elements.participantNotice.checked) {
    showError("회의 참여자에게 녹음과 분석 사실을 알렸는지 확인해 주세요.");
    elements.participantNotice.focus();
    return;
  }
  lastAction = () => analyzeUpload(file);
  beginLoading(title, true);
  const formData = new FormData();
  formData.append("audio", file);
  formData.append("title", title);
  formData.append("participant_notice_confirmed", "true");
  try {
    const response = await authFetch("/api/meetings", {
      method: "POST",
      body: formData,
      headers: { "Idempotency-Key": uploadRequestId },
    });
    if (!response.ok) throw new Error(await readError(response));
    const meeting = await response.json();
    clearMeetingDraft();
    history.replaceState({}, "", `/meetings/${meeting.id}`);
    currentPath = `/meetings/${meeting.id}`;
    renderResult(meeting.analysis, meeting);
    await loadMeetings();
  } catch (error) {
    showError(error.message);
  }
}

function renderSamples(samples) {
  elements.sampleList.innerHTML = samples
    .map(
      (sample) => `
        <button class="sample-button" type="button" data-sample-id="${escapeHtml(sample.id)}" ${sample.available ? "" : "disabled"}>
          <span class="sample-topline">
            <strong>${escapeHtml(sample.title)}</strong>
            <span class="sample-duration">${sample.available ? "약 34초 · 공개 결과" : "파일 없음"}</span>
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
    elements.sampleList.innerHTML = `<p class="empty-result">샘플 목록을 불러오지 못했습니다: ${escapeHtml(error.message)}</p>`;
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

function renderMeetings(meetings) {
  elements.meetingLimit.textContent = `${meetings.length} / 5`;
  if (!meetings.length) {
    elements.meetingList.innerHTML = "<p>아직 저장한 회의가 없습니다.</p>";
    elements.meetingListPage.innerHTML = `
      <div class="meeting-empty">
        <strong>저장된 회의가 없습니다.</strong>
        <p>첫 회의를 분석하면 여기에 표시됩니다.</p>
        <button class="button button-primary" type="button" data-new-meeting>새 회의</button>
      </div>
    `;
    elements.meetingListPage.querySelector("[data-new-meeting]")
      .addEventListener("click", () => navigate("/meetings/new"));
    return;
  }
  const sidebarRows = meetings
    .map(
      (meeting) => `
        <button type="button" class="meeting-item" data-meeting-id="${escapeHtml(meeting.id)}">
          <strong>${escapeHtml(meeting.title)}</strong>
          <span>${escapeHtml(formatDate(meeting.created_at))} · 결정 ${meeting.decision_count} · 할 일 ${meeting.action_count}</span>
        </button>
      `,
    )
    .join("");
  const pageRows = meetings
    .map(
      (meeting) => `
        <button type="button" class="meeting-row" data-meeting-id="${escapeHtml(meeting.id)}">
          <span class="meeting-row-main">
            <strong>${escapeHtml(meeting.title)}</strong>
            <span>${escapeHtml(formatDate(meeting.created_at))}</span>
          </span>
          <span class="meeting-row-meta">
            <span>${Math.round(Number(meeting.audio_duration_seconds || 0))}초</span>
            <span>결정 ${Number(meeting.decision_count || 0)}</span>
            <span>할 일 ${Number(meeting.action_count || 0)}</span>
          </span>
        </button>
      `,
    )
    .join("");
  elements.meetingList.innerHTML = sidebarRows;
  elements.meetingListPage.innerHTML = pageRows;
  [elements.meetingList, elements.meetingListPage].forEach((container) => {
    container.querySelectorAll("[data-meeting-id]").forEach((button) => {
      button.addEventListener("click", () => navigate(`/meetings/${button.dataset.meetingId}`));
    });
  });
}

async function loadMeetings() {
  if (!currentUser) {
    elements.meetingLimit.textContent = "0 / 5";
    elements.meetingList.innerHTML = "<p>로그인하면 저장한 회의가 표시됩니다.</p>";
    elements.meetingListPage.innerHTML = "<p>Google 로그인이 필요합니다.</p>";
    return;
  }
  elements.meetingList.innerHTML = "<p>회의 목록을 불러오는 중…</p>";
  elements.meetingListPage.innerHTML = "<p>회의 목록을 불러오는 중…</p>";
  try {
    const response = await authFetch("/api/meetings");
    if (!response.ok) throw new Error(await readError(response));
    renderMeetings(await response.json());
  } catch (error) {
    elements.meetingList.innerHTML = `<p>${escapeHtml(error.message)}</p>`;
    elements.meetingListPage.innerHTML = `<div class="meeting-empty"><strong>회의 목록을 불러오지 못했습니다.</strong><p>${escapeHtml(error.message)}</p><button class="button button-secondary" type="button" data-retry-meetings>다시 시도</button></div>`;
    elements.meetingListPage.querySelector("[data-retry-meetings]")
      .addEventListener("click", loadMeetings);
  }
}

async function openMeeting(meetingId, updateUrl = true) {
  if (updateUrl) {
    await navigate(`/meetings/${meetingId}`);
    return;
  }
  elements.statusPanel.querySelector("#status-title").textContent = "회의를 불러오는 중";
  elements.statusPanel.querySelector("#status-copy").textContent = "저장한 결과와 오디오 접근 권한을 확인하고 있습니다.";
  elements.statusPanel.hidden = false;
  try {
    const response = await authFetch(`/api/meetings/${encodeURIComponent(meetingId)}`);
    if (!response.ok) throw new Error(await readError(response));
    const meeting = await response.json();
    renderResult(meeting.analysis, meeting);
  } catch (error) {
    showError(error.message);
  }
}

function renderEmpty(message) {
  return `<p class="empty-result">${escapeHtml(message)}</p>`;
}

function renderInsight(item, type, segmentById) {
  const meta = [];
  if (item.owner) meta.push(`<span>담당 ${escapeHtml(item.owner)}</span>`);
  if (item.due) meta.push(`<span>기한 ${escapeHtml(item.due)}</span>`);
  const evidenceIds = item.segment_ids || [];
  const evidenceTimes = evidenceIds
    .map((id) => segmentById.get(id))
    .filter(Boolean)
    .map((segment) => `<span class="evidence-time">${formatTimestamp(segment.start)}</span>`)
    .join("");
  return `
    <article class="insight-card ${type}">
      <p>${escapeHtml(item.text)}</p>
      ${meta.length ? `<div class="item-meta">${meta.join("")}</div>` : ""}
      ${evidenceIds.length ? `
        <button type="button" class="evidence-button" data-evidence="${escapeHtml(evidenceIds.join(","))}" aria-label="근거 듣기: ${escapeHtml(evidenceIds.join(", "))}">
          <span>근거 듣기</span>${evidenceTimes}
        </button>
      ` : ""}
    </article>
  `;
}

function focusEvidence(segmentIds) {
  document.querySelectorAll(".segment.is-evidence").forEach((segment) => {
    segment.classList.remove("is-evidence");
    segment.removeAttribute("aria-current");
  });
  const targets = segmentIds
    .map((id) => document.querySelector(`[data-segment-id="${CSS.escape(id)}"]`))
    .filter(Boolean);
  targets.forEach((target) => {
    target.classList.add("is-evidence");
    target.setAttribute("aria-current", "true");
  });
  if (!targets.length) return;
  elements.audioPlayer.currentTime = Number(targets[0].dataset.start || 0);
  elements.audioPlayer.play().catch(() => {});
  targets[0].scrollIntoView({
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
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

function clearPrivateResult() {
  if (!currentMeetingId) return;
  elements.audioPlayer.pause();
  elements.audioPlayer.removeAttribute("src");
  elements.audioPlayer.load();
  elements.transcriptList.replaceChildren();
  elements.decisionList.replaceChildren();
  elements.actionList.replaceChildren();
  elements.resultMetrics.replaceChildren();
  elements.sourceAttribution.textContent = "";
  elements.resultPanel.hidden = true;
  currentMeetingId = null;
}

function renderResult(result, meeting = null) {
  endLoading();
  elements.errorPanel.hidden = true;
  currentMeetingId = meeting?.id || null;
  elements.resultTitle.textContent = meeting?.title || result.sample?.title || result.audio;
  elements.audioPlayer.src = meeting?.audio_url || result.audio_url || "";
  elements.savedStatus.className = meeting ? "saved-badge" : "";
  elements.savedStatus.textContent = meeting ? "계정에 저장됨" : "";
  elements.deleteMeeting.hidden = !meeting;

  if (result.sample) {
    elements.sourceAttribution.innerHTML = `
      ${escapeHtml(result.audio)} · 출처:
      <a href="${escapeHtml(result.sample.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(result.sample.source_title)}</a>
      · ${escapeHtml(result.sample.author)} ·
      <a href="${escapeHtml(result.sample.license_url)}" target="_blank" rel="noreferrer">${escapeHtml(result.sample.license)}</a>
      · ${escapeHtml(result.sample.modification)}
    `;
  } else {
    elements.sourceAttribution.textContent = meeting
      ? `내 회의 · ${formatDate(meeting.created_at)} · 삭제 전까지 비공개 보관`
      : "업로드 파일";
  }

  const totalTokens = (result.usage?.prompt_tokens || 0) + (result.usage?.completion_tokens || 0);
  const budgetMetric = result.budget?.persistence === "persistent"
    ? `<span class="metric"><strong>$${result.budget.remaining_usd.toFixed(4)}</strong><span>월 예산 남음</span></span>`
    : "";
  elements.resultMetrics.innerHTML = `
    <span class="metric"><strong>${Number(result.timing_seconds.total).toFixed(2)}초</strong><span>처리 시간</span></span>
    <span class="metric"><strong>${totalTokens.toLocaleString("ko-KR")}</strong><span>분석 토큰</span></span>
    <span class="metric"><strong>$${Number(result.estimated_cost_usd).toFixed(8)}</strong><span>예상 비용</span></span>
    ${budgetMetric}
  `;

  elements.transcriptList.innerHTML = result.segments
    .map(
      (segment) => `
        <div class="segment" data-segment-id="${escapeHtml(segment.id)}" data-start="${Number(segment.start)}">
          <time datetime="PT${Number(segment.start)}S">${formatTimestamp(segment.start)}</time>
          <p>${escapeHtml(segment.text)}</p>
        </div>
      `,
    )
    .join("");
  elements.segmentCount.textContent = `${result.segments.length}개 구간`;

  const segmentById = new Map(result.segments.map((segment) => [segment.id, segment]));
  const decisions = result.extraction?.decisions || [];
  const actions = result.extraction?.action_items || [];
  elements.decisionList.innerHTML = decisions.length
    ? decisions.map((item) => renderInsight(item, "decision", segmentById)).join("")
    : renderEmpty("명시적으로 확정된 결정을 찾지 못했습니다.");
  elements.actionList.innerHTML = actions.length
    ? actions.map((item) => renderInsight(item, "action", segmentById)).join("")
    : renderEmpty("앞으로 수행할 구체적인 일을 찾지 못했습니다.");
  elements.decisionCount.textContent = decisions.length;
  elements.actionCount.textContent = actions.length;

  const groundingValid = result.grounding?.valid === true;
  elements.groundingStatus.className = groundingValid ? "valid-badge" : "invalid-badge";
  elements.groundingStatus.textContent = groundingValid ? "모든 근거 유효" : "근거 확인 필요";
  elements.modelDetail.textContent = `${result.models.transcription} → ${result.models.extraction}`;

  bindEvidenceButtons();
  elements.backToInput.href = meeting ? "/meetings" : "/samples";
  elements.backToInput.textContent = meeting ? "회의 기록으로 돌아가기" : "공개 샘플로 돌아가기";
  elements.resultPanel.hidden = false;
  document.body.classList.add("result-view");
  document.title = `${elements.resultTitle.textContent} · MinuteMark`;
  elements.resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function validateFile(file) {
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
  selectedFile = file;
  uploadRequestId = crypto.randomUUID().replaceAll("-", "");
  elements.dropLabel.textContent = file.name;
  elements.dropHelp.textContent = "준비됐습니다. 분석을 시작하면 원본과 결과가 계정에 저장됩니다.";
  if (!elements.meetingTitle.value.trim()) {
    elements.meetingTitle.value = file.name.replace(/\.[^.]+$/, "").slice(0, 80);
  }
  updateAnalyzeButton();
}

async function openAuthDialog(next = "/meetings/new") {
  if (!memberFeaturesEnabled) {
    showError("회원 기능을 준비하고 있습니다. 잠시 후 다시 시도해 주세요.");
    return;
  }
  elements.authError.textContent = "";
  await navigate(`/auth?next=${encodeURIComponent(next)}`);
}

async function openPrivacyDialog() {
  privacyReturnPath = currentPath === "/privacy" ? "/samples" : currentPath;
  await navigate("/privacy", { skipDraftGuard: true });
}

function setAuthState(user) {
  currentUser = user;
  document.body.classList.toggle("is-member", Boolean(user));
  elements.dropZone.classList.toggle("is-locked", !user);
  elements.dropZone.setAttribute("aria-disabled", String(!user));
  elements.chooseFile.hidden = !user;
  elements.signinUpload.hidden = Boolean(user);
  elements.accountLabel.textContent = user ? user.email : "Google로 시작하기";
  elements.accountEmail.textContent = user?.email || "";
  elements.deleteAccountConfirm.value = "";
  elements.deleteAccount.disabled = true;
  elements.dropLabel.textContent = user ? "파일을 끌어놓거나 선택" : "Google 로그인 후 파일 선택";
  elements.dropHelp.textContent = user
    ? "분석하면 원본과 결과가 계정에 저장됩니다."
    : "공개 샘플은 로그인 없이 확인할 수 있습니다.";
  if (!user) {
    clearPrivateResult();
    if (elements.accountDialog.open) elements.accountDialog.close();
  }
  updateAnalyzeButton();
  loadMeetings();
}

elements.chooseFile.addEventListener("click", (event) => {
  event.stopPropagation();
  if (currentUser) elements.fileInput.click();
});
elements.analyzeSave.addEventListener("click", (event) => {
  event.stopPropagation();
  if (selectedFile && !elements.analyzeSave.disabled) analyzeUpload(selectedFile);
});
elements.signinUpload.addEventListener("click", (event) => {
  event.stopPropagation();
  openAuthDialog();
});
elements.dropZone.addEventListener("click", () => {
  if (currentUser) elements.fileInput.click();
  else openAuthDialog();
});
elements.fileInput.addEventListener("change", () => validateFile(elements.fileInput.files[0]));
elements.meetingTitle.addEventListener("input", updateAnalyzeButton);
elements.participantNotice.addEventListener("change", updateAnalyzeButton);
["dragenter", "dragover"].forEach((eventName) => {
  elements.dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    if (currentUser) elements.dropZone.classList.add("is-dragging");
  });
});
["dragleave", "drop"].forEach((eventName) => {
  elements.dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    elements.dropZone.classList.remove("is-dragging");
  });
});
elements.dropZone.addEventListener("drop", (event) => {
  if (currentUser) validateFile(event.dataTransfer.files[0]);
  else openAuthDialog();
});
elements.retryButton.addEventListener("click", () => lastAction && lastAction());
elements.newMeeting.addEventListener("click", () => {
  if (isSubmittingMeeting) return;
  if (currentUser) navigate("/meetings/new");
  else openAuthDialog();
});
elements.meetingsNew.addEventListener("click", () => navigate("/meetings/new"));
document.querySelectorAll(".route-link").forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    navigate(link.pathname + link.search);
  });
});
elements.accountButton.addEventListener("click", () => {
  if (currentUser) {
    elements.accountError.textContent = "";
    navigate("/account");
  } else {
    openAuthDialog("/meetings");
  }
});
elements.privacyButton.addEventListener("click", openPrivacyDialog);
elements.authPrivacyButton.addEventListener("click", openPrivacyDialog);
elements.accountPrivacyButton.addEventListener("click", openPrivacyDialog);
elements.privacyClose.addEventListener("click", () => navigate(privacyReturnPath || "/samples", { skipDraftGuard: true }));
elements.authClose.addEventListener("click", () => navigate("/samples", { replace: true, skipDraftGuard: true }));
elements.accountClose.addEventListener("click", () => navigate("/meetings", { replace: true, skipDraftGuard: true }));
elements.mobileMenuButton.addEventListener("click", () => {
  if (!elements.mobileMenuDialog.open) elements.mobileMenuDialog.showModal();
  elements.mobileMenuButton.setAttribute("aria-expanded", "true");
});
elements.mobileMenuClose.addEventListener("click", closeMobileMenu);

elements.googleSignin.addEventListener("click", async () => {
  elements.authError.textContent = "";
  elements.googleSignin.disabled = true;
  try {
    await signInWithPopup(auth, provider);
  } catch (error) {
    elements.authError.textContent = error.code === "auth/popup-closed-by-user"
      ? "Google 로그인이 취소됐습니다."
      : "Google 로그인을 완료하지 못했습니다. 다시 시도해 주세요.";
  } finally {
    elements.googleSignin.disabled = false;
  }
});

async function handleSignout() {
  await signOut(auth);
  if (elements.accountDialog.open) elements.accountDialog.close();
  closeMobileMenu();
  clearMeetingDraft();
  await navigate("/samples", { replace: true, skipDraftGuard: true });
}

elements.signout.addEventListener("click", handleSignout);
elements.mobileSignout.addEventListener("click", handleSignout);

elements.deleteMeeting.addEventListener("click", () => {
  if (!currentMeetingId) return;
  elements.deleteMeetingError.textContent = "";
  elements.deleteMeetingDialog.showModal();
});
elements.deleteMeetingCancel.addEventListener("click", () => elements.deleteMeetingDialog.close());
elements.deleteMeetingConfirm.addEventListener("click", async () => {
  if (!currentMeetingId) return;
  elements.deleteMeetingConfirm.disabled = true;
  try {
    const response = await authFetch(`/api/meetings/${encodeURIComponent(currentMeetingId)}`, { method: "DELETE" });
    if (!response.ok) throw new Error(await readError(response));
    elements.deleteMeetingDialog.close();
    currentMeetingId = null;
    await navigate("/meetings", { replace: true, skipDraftGuard: true });
  } catch (error) {
    elements.deleteMeetingError.textContent = error.message;
  } finally {
    elements.deleteMeetingConfirm.disabled = false;
  }
});

elements.deleteAccountConfirm.addEventListener("input", () => {
  elements.deleteAccount.disabled = elements.deleteAccountConfirm.value.trim() !== "탈퇴";
});
elements.deleteAccount.addEventListener("click", async () => {
  if (elements.deleteAccountConfirm.value.trim() !== "탈퇴") return;
  elements.accountError.textContent = "";
  elements.deleteAccount.disabled = true;
  try {
    await reauthenticateWithPopup(currentUser, provider);
    await currentUser.getIdToken(true);
    const response = await authFetch("/api/account", { method: "DELETE" });
    if (!response.ok) throw new Error(await readError(response));
    await signOut(auth);
    elements.accountDialog.close();
    clearMeetingDraft();
    await navigate("/samples", { replace: true, skipDraftGuard: true });
  } catch (error) {
    elements.accountError.textContent = error.code === "auth/popup-closed-by-user"
      ? "계정 삭제 확인이 취소됐습니다."
      : error.message || "계정을 삭제하지 못했습니다. 다시 시도해 주세요.";
  } finally {
    elements.deleteAccount.disabled = elements.deleteAccountConfirm.value.trim() !== "탈퇴";
  }
});

async function initialize() {
  await Promise.all([loadSamples(), loadBudget()]);
  try {
    const response = await fetch("/api/config");
    if (!response.ok) throw new Error(await readError(response));
    const config = await response.json();
    memberFeaturesEnabled = config.member_features_enabled === true;
    if (!memberFeaturesEnabled) {
      setAuthState(null);
      authReady = true;
      await renderRoute();
      return;
    }
    const [appModule, authModule] = await Promise.all([
      import("https://www.gstatic.com/firebasejs/12.16.0/firebase-app.js"),
      import("https://www.gstatic.com/firebasejs/12.16.0/firebase-auth.js"),
    ]);
    ({ initializeApp } = appModule);
    ({
      GoogleAuthProvider,
      getAuth,
      onAuthStateChanged,
      reauthenticateWithPopup,
      signInWithPopup,
      signOut,
    } = authModule);
    auth = getAuth(initializeApp(config.firebase));
    auth.languageCode = "ko";
    provider = new GoogleAuthProvider();
    provider.setCustomParameters({ prompt: "select_account" });
    onAuthStateChanged(auth, async (user) => {
      setAuthState(user);
      authReady = true;
      const url = new URL(location.href);
      if (user && url.pathname === "/auth") {
        await navigate(url.searchParams.get("next") || "/meetings", {
          replace: true,
          skipDraftGuard: true,
        });
      } else {
        currentPath = location.pathname + location.search;
        await renderRoute(currentPath);
      }
    });
  } catch (error) {
    memberFeaturesEnabled = false;
    setAuthState(null);
    authReady = true;
    await navigate("/samples", { replace: true, skipDraftGuard: true });
    showError(error.message);
  }
}

window.addEventListener("beforeunload", (event) => {
  if (!hasMeetingDraft() || location.pathname !== "/meetings/new") return;
  event.preventDefault();
  event.returnValue = "";
});

window.addEventListener("popstate", async () => {
  const targetPath = location.pathname + location.search;
  const leavingDraft = new URL(currentPath, location.origin).pathname === "/meetings/new"
    && location.pathname !== "/meetings/new"
    && hasMeetingDraft();
  if (leavingDraft && !window.confirm("선택한 파일과 입력한 내용이 사라집니다. 이동할까요?")) {
    history.pushState({}, "", currentPath);
    return;
  }
  if (leavingDraft) clearMeetingDraft();
  currentPath = targetPath;
  closeMobileMenu();
  await renderRoute(targetPath);
});

elements.mobileMenuDialog.addEventListener("cancel", (event) => {
  event.preventDefault();
  closeMobileMenu();
});
elements.authDialog.addEventListener("cancel", (event) => {
  event.preventDefault();
  navigate("/samples", { replace: true, skipDraftGuard: true });
});
elements.accountDialog.addEventListener("cancel", (event) => {
  event.preventDefault();
  navigate("/meetings", { replace: true, skipDraftGuard: true });
});
elements.privacyDialog.addEventListener("cancel", (event) => {
  event.preventDefault();
  navigate(privacyReturnPath || "/samples", { skipDraftGuard: true });
});

initialize();
