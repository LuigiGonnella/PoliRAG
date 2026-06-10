const apiBase = window.POLIRAG_API_BASE || "";

const state = {
  sessions: [],
  activeSession: null,
  catalog: null,
  coursesByYear: new Map(),
};

const elements = {
  sessionList: document.querySelector("#session-list"),
  sessionCount: document.querySelector("#session-count"),
  messages: document.querySelector("#messages"),
  emptyState: document.querySelector("#empty-state"),
  activeScope: document.querySelector("#active-scope"),
  yearSelect: document.querySelector("#year-select"),
  courseSelect: document.querySelector("#course-select"),
  form: document.querySelector("#chat-form"),
  input: document.querySelector("#message-input"),
  sendButton: document.querySelector("#send-button"),
  newGeneral: document.querySelector("#new-general"),
  newCourse: document.querySelector("#new-course"),
};

function setCatalogLoading(isLoading) {
  elements.yearSelect.disabled = isLoading;
  elements.courseSelect.disabled = isLoading;
  elements.yearSelect.innerHTML = isLoading
    ? '<option value="">Loading years...</option>'
    : '<option value="">All years</option>';
  elements.courseSelect.innerHTML = isLoading
    ? '<option value="">Loading courses...</option>'
    : '<option value="">All courses</option>';
}

async function api(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || payload.error || response.statusText);
  }
  if (response.status === 204) return null;
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) return null;
  return response.json();
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderInlineMarkdown(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

function renderMarkdown(markdown) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const html = [];
  let paragraph = [];
  let list = [];
  let listType = "ul";
  let inCode = false;
  let codeLines = [];

  const flushParagraph = () => {
    if (!paragraph.length) return;
    html.push(`<p>${renderInlineMarkdown(paragraph.join(" "))}</p>`);
    paragraph = [];
  };

  const flushList = () => {
    if (!list.length) return;
    html.push(`<${listType}>${list.map((item) => `<li>${renderInlineMarkdown(item)}</li>`).join("")}</${listType}>`);
    list = [];
    listType = "ul";
  };

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();

    if (line.trim().startsWith("```")) {
      if (inCode) {
        html.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
        codeLines = [];
        inCode = false;
      } else {
        flushParagraph();
        flushList();
        inCode = true;
      }
      continue;
    }

    if (inCode) {
      codeLines.push(rawLine);
      continue;
    }

    if (!line.trim()) {
      flushParagraph();
      flushList();
      continue;
    }

    if (/^---+$/.test(line.trim())) {
      flushParagraph();
      flushList();
      html.push("<hr>");
      continue;
    }

    const heading = /^(#{1,4})\s+(.+)$/.exec(line.trim());
    if (heading) {
      flushParagraph();
      flushList();
      const level = heading[1].length;
      html.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`);
      continue;
    }

    const bullet = /^[-*]\s+(.+)$/.exec(line.trim());
    if (bullet) {
      flushParagraph();
      if (list.length && listType !== "ul") flushList();
      listType = "ul";
      list.push(bullet[1]);
      continue;
    }

    const ordered = /^\d+[.)]\s+(.+)$/.exec(line.trim());
    if (ordered) {
      flushParagraph();
      if (list.length && listType !== "ol") flushList();
      listType = "ol";
      list.push(ordered[1]);
      continue;
    }

    paragraph.push(line.trim());
  }

  flushParagraph();
  flushList();
  if (inCode) {
    html.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
  }
  return html.join("");
}

function dedupeCitations(citations = []) {
  const seen = new Map();
  for (const citation of citations) {
    const source = citation.source || citation.type || "source";
    const key = `${citation.type || "local"}::${source}`;
    if (!seen.has(key)) {
      seen.set(key, { ...citation, source });
    }
  }
  return [...seen.values()];
}

function citationsHtml(citations = []) {
  const unique = dedupeCitations(citations);
  if (!unique.length) return "";
  return `<div class="citations">${unique
    .slice(0, 8)
    .map((item) => {
      const page = item.page && item.page !== "Unknown" ? ` p. ${item.page}` : "";
      return `<span class="citation">${escapeHtml(item.source || item.type || "source")}${escapeHtml(page)}</span>`;
    })
    .join("")}</div>`;
}

function currentCourse() {
  const selected = elements.courseSelect.selectedOptions[0];
  if (!selected || !selected.value) return null;
  return {
    course: selected.value,
    year: selected.dataset.year,
    degree: selected.dataset.degree,
    label: selected.textContent,
  };
}

function sessionLabel(session) {
  if (session.course_filter) return session.course_filter;
  return session.mode === "course" ? "Course chat" : "General";
}

function renderSessions() {
  elements.sessionCount.textContent = String(state.sessions.length);
  elements.sessionList.innerHTML = "";

  for (const session of state.sessions) {
    const item = document.createElement("div");
    item.className = `session-item ${state.activeSession?.thread_id === session.thread_id ? "active" : ""}`;
    item.innerHTML = `
      <button class="session-open" type="button">
        <span class="session-title">${escapeHtml(session.title)}</span>
        <span class="session-meta">${escapeHtml(sessionLabel(session))}</span>
      </button>
      <button class="session-delete" type="button" title="Delete chat" aria-label="Delete chat">x</button>
    `;
    item.querySelector(".session-open").addEventListener("click", () => loadSession(session.thread_id));
    item.querySelector(".session-delete").addEventListener("click", () => deleteSession(session.thread_id));
    elements.sessionList.appendChild(item);
  }
}

function renderMessages(messages) {
  elements.messages.innerHTML = "";
  elements.emptyState.style.display = messages.length ? "none" : "grid";

  for (const message of messages) {
    appendMessage(message.role, message.content, message.metadata?.citations || []);
  }
}

function appendMessage(role, content, citations = [], extraClass = "") {
  elements.emptyState.style.display = "none";
  const wrapper = document.createElement("article");
  wrapper.className = `message ${role} ${extraClass}`.trim();

  wrapper.innerHTML = `<div class="bubble">${role === "assistant" ? renderMarkdown(content) : escapeHtml(content)}</div>${citationsHtml(citations)}`;
  elements.messages.appendChild(wrapper);
  elements.messages.scrollTop = elements.messages.scrollHeight;
  return wrapper;
}

function updateAssistantMessage(wrapper, markdown, citations = null) {
  wrapper.querySelector(".bubble").innerHTML = renderMarkdown(markdown);
  if (citations) {
    wrapper.querySelector(".citations")?.remove();
    wrapper.insertAdjacentHTML("beforeend", citationsHtml(citations));
  }
  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function renderCatalog() {
  state.coursesByYear.clear();
  elements.yearSelect.innerHTML = '<option value="">All years</option>';
  elements.courseSelect.innerHTML = '<option value="">All courses</option>';

  const degrees = state.catalog?.degrees || [];
  for (const degree of degrees) {
    for (const year of degree.years) {
      const yearKey = `${degree.value}::${year.value}`;
      if (!state.coursesByYear.has(yearKey)) {
        state.coursesByYear.set(yearKey, { degree, year, courses: [] });
      }
      state.coursesByYear.get(yearKey).courses.push(...year.courses);
    }
  }

  for (const [key, item] of state.coursesByYear.entries()) {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = `${item.degree.label} / ${item.year.label}`;
    elements.yearSelect.appendChild(option);
  }

  renderCourseOptions();
}

function renderCourseOptions() {
  const yearKey = elements.yearSelect.value;
  elements.courseSelect.innerHTML = '<option value="">All courses</option>';

  const groups = yearKey ? [state.coursesByYear.get(yearKey)].filter(Boolean) : [...state.coursesByYear.values()];
  for (const group of groups) {
    for (const course of group.courses) {
      const option = document.createElement("option");
      option.value = course.value;
      option.textContent = course.label;
      option.dataset.degree = course.degree;
      option.dataset.year = course.year;
      elements.courseSelect.appendChild(option);
    }
  }
}

function updateScope() {
  const course = currentCourse();
  elements.newCourse.disabled = !course;
  if (state.activeSession?.course_filter) {
    elements.activeScope.textContent = state.activeSession.course_filter;
    return;
  }
  elements.activeScope.textContent = course ? course.label : "General knowledge base";
}

async function loadSessions() {
  const payload = await api("/v1/sessions");
  state.sessions = payload.sessions;
  renderSessions();
}

async function loadSession(threadId) {
  const payload = await api(`/v1/sessions/${threadId}`);
  state.activeSession = payload.session;
  renderSessions();
  renderMessages(payload.messages);
  updateScope();
}

async function createSession(mode) {
  const course = mode === "course" ? currentCourse() : null;
  if (mode === "course" && !course) return;
  const payload = await api("/v1/sessions", {
    method: "POST",
    body: JSON.stringify({
      mode,
      title: course ? course.label : "General chat",
      degree_filter: course?.degree || null,
      year_filter: course?.year || null,
      course_filter: course?.course || null,
    }),
  });
  state.activeSession = payload;
  await loadSessions();
  renderMessages([]);
  updateScope();
}

async function deleteSession(threadId) {
  await api(`/v1/sessions/${threadId}`, { method: "DELETE" });
  if (state.activeSession?.thread_id === threadId) {
    state.activeSession = null;
    renderMessages([]);
  }
  await loadSessions();
  if (!state.activeSession && state.sessions.length) {
    await loadSession(state.sessions[0].thread_id);
  }
  if (!state.sessions.length) {
    await createSession("general");
  }
}

async function sendMessage(event) {
  event.preventDefault();
  const text = elements.input.value.trim();
  if (!text) return;

  const course = currentCourse();
  appendMessage("user", text);
  elements.input.value = "";
  elements.sendButton.disabled = true;
  const assistantMessage = appendMessage("assistant", "Retrieving sources...", [], "thinking");
  let assistantText = "";

  try {
    const response = await fetch(`${apiBase}/v1/agent/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        thread_id: state.activeSession?.thread_id || null,
        message: text,
        degree_filter: state.activeSession?.degree_filter || course?.degree || null,
        year_filter: state.activeSession?.year_filter || course?.year || null,
        course_filter: state.activeSession?.course_filter || course?.course || null,
      }),
    });

    if (!response.ok || !response.body) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || payload.error || response.statusText);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let threadId = state.activeSession?.thread_id || null;

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) continue;
        const event = JSON.parse(line);

        if (event.event === "status" && !assistantText) {
          updateAssistantMessage(assistantMessage, event.message || "Working...");
        }
        if (event.event === "metadata") {
          threadId = event.thread_id || threadId;
          assistantMessage.classList.remove("thinking");
        }
        if (event.event === "delta") {
          assistantText += event.text || "";
          updateAssistantMessage(assistantMessage, assistantText);
        }
        if (event.event === "done") {
          threadId = event.thread_id || threadId;
          updateAssistantMessage(assistantMessage, assistantText, event.citations || []);
        }
        if (event.event === "error") {
          throw new Error(event.message || "Streaming failed");
        }
      }
    }

    await loadSessions();
    if (threadId) {
      await loadSession(threadId);
    }
  } catch (error) {
    assistantMessage.remove();
    appendMessage("assistant", error.message, [], "error");
  } finally {
    elements.sendButton.disabled = false;
    elements.input.focus();
  }
}

async function boot() {
  setCatalogLoading(true);
  try {
    state.catalog = await api("/v1/courses");
    renderCatalog();
  } catch (error) {
    state.catalog = { source: "empty", degrees: [] };
    renderCatalog();
  } finally {
    elements.yearSelect.disabled = false;
    elements.courseSelect.disabled = false;
    updateScope();
  }

  await loadSessions();
  if (state.sessions.length) {
    await loadSession(state.sessions[0].thread_id);
  } else {
    await createSession("general");
  }
}

elements.newGeneral.addEventListener("click", () => createSession("general"));
elements.newCourse.addEventListener("click", () => createSession("course"));
elements.yearSelect.addEventListener("change", () => {
  renderCourseOptions();
  updateScope();
});
elements.courseSelect.addEventListener("change", updateScope);
elements.form.addEventListener("submit", sendMessage);

boot().catch((error) => {
  appendMessage("assistant", error.message, [], "error");
});
