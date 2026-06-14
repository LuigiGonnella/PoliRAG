const configuredBase =
  import.meta.env.VITE_POLYRAG_API_BASE ||
  import.meta.env.VITE_POLIRAG_API_BASE ||
  window.POLIRAG_API_BASE ||
  "";

export const apiBase = configuredBase.replace(/\/$/, "");

async function request(path, options = {}) {
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
  return contentType.includes("application/json") ? response.json() : null;
}

export const polyRagApi = {
  getCourses: () => request("/v1/courses"),
  listSessions: () => request("/v1/sessions"),
  getSession: (threadId) => request(`/v1/sessions/${threadId}`),
  createSession: (payload) =>
    request("/v1/sessions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  deleteSession: (threadId) => request(`/v1/sessions/${threadId}`, { method: "DELETE" }),
  streamChat,
};

async function streamChat(payload, handlers, timeoutMs = 240000) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${apiBase}/v1/agent/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!response.ok || !response.body) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new Error(errorPayload.detail || errorPayload.error || response.statusText);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.trim()) handleStreamEvent(JSON.parse(line), handlers);
      }
    }

    if (buffer.trim()) {
      handleStreamEvent(JSON.parse(buffer), handlers);
    }
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The answer took too long. Please try again or narrow the chat scope.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

function handleStreamEvent(event, handlers) {
  if (event.event === "error") {
    throw new Error(event.message || "Streaming failed");
  }
  handlers[event.event]?.(event);
}
