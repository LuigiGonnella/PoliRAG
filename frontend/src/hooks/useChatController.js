import { useCallback, useEffect, useMemo, useState } from "react";
import { polyRagApi } from "../api/polyRagApi.js";
import { buildCourseGroups, findGroup, scopeLabel, sessionScopeLabel } from "../lib/catalog.js";

const THEME_KEY = "polyhedric.theme";
const SIDEBAR_KEY = "polyhedric.sidebarCollapsed";
const LANGUAGE_KEY = "polyhedric.language";

const emptyLoading = {
  catalog: false,
  sessions: false,
  creating: false,
  deleting: false,
  streaming: false,
};

function initialTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  if (saved === "dark" || saved === "light") return saved;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function initialLanguage() {
  const saved = localStorage.getItem(LANGUAGE_KEY);
  if (saved === "en" || saved === "it") return saved;
  return navigator.language?.toLowerCase().startsWith("it") ? "it" : "en";
}

function transientMessage(role, content, metadata = {}) {
  return {
    role,
    content,
    metadata,
    created_at: new Date().toISOString(),
    transient: true,
  };
}

function formatSessionDate(value, language = "en") {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat(language === "it" ? "it-IT" : "en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function useChatController() {
  const [theme, setThemeState] = useState(initialTheme);
  const [language, setLanguageState] = useState(initialLanguage);
  const [sidebarCollapsed, setSidebarCollapsedState] = useState(localStorage.getItem(SIDEBAR_KEY) === "true");
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [modal, setModal] = useState(null);
  const [catalog, setCatalog] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [chatMode, setChatMode] = useState("general");
  const [selectedYearKey, setSelectedYearKey] = useState("");
  const [selectedCourse, setSelectedCourse] = useState("");
  const [pendingDelete, setPendingDelete] = useState(null);
  const [loading, setLoading] = useState(emptyLoading);
  const [error, setError] = useState("");

  const courseGroups = useMemo(() => buildCourseGroups(catalog), [catalog]);
  const selectedGroup = useMemo(
    () => findGroup(courseGroups, selectedYearKey),
    [courseGroups, selectedYearKey],
  );

  const setLoadingFlag = useCallback((key, value) => {
    setLoading((current) => ({ ...current, [key]: value }));
  }, []);

  const setTheme = useCallback((nextTheme) => {
    const resolved = nextTheme === "dark" ? "dark" : "light";
    setThemeState(resolved);
    localStorage.setItem(THEME_KEY, resolved);
  }, []);

  const setLanguage = useCallback((nextLanguage) => {
    const resolved = nextLanguage === "it" ? "it" : "en";
    setLanguageState(resolved);
    localStorage.setItem(LANGUAGE_KEY, resolved);
  }, []);

  const setSidebarCollapsed = useCallback((collapsed) => {
    setSidebarCollapsedState(collapsed);
    localStorage.setItem(SIDEBAR_KEY, String(collapsed));
  }, []);

  const closeMobileSidebar = useCallback(() => {
    setMobileSidebarOpen(false);
  }, []);

  const loadSessions = useCallback(async () => {
    setLoadingFlag("sessions", true);
    try {
      const payload = await polyRagApi.listSessions();
      setSessions(payload.sessions || []);
      return payload.sessions || [];
    } finally {
      setLoadingFlag("sessions", false);
    }
  }, [setLoadingFlag]);

  const loadSession = useCallback(
    async (threadId) => {
      try {
        const payload = await polyRagApi.getSession(threadId);
        setActiveSession(payload.session);
        setMessages(payload.messages || []);
        setError("");
        closeMobileSidebar();
        return payload.session;
      } catch (sessionError) {
        setError(sessionError.message || "Unable to open this chat.");
        await loadSessions();
        throw sessionError;
      }
    },
    [closeMobileSidebar, loadSessions],
  );

  const loadCatalog = useCallback(async () => {
    setLoadingFlag("catalog", true);
    try {
      const payload = await polyRagApi.getCourses();
      setCatalog(payload);
    } catch (catalogError) {
      setCatalog({ source: "empty", degrees: [] });
      setError(catalogError.message || "Course catalog is unavailable.");
    } finally {
      setLoadingFlag("catalog", false);
    }
  }, [setLoadingFlag]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    let cancelled = false;

    async function boot() {
      try {
        await loadCatalog();
        const initialSessions = await loadSessions();
        if (!cancelled && initialSessions.length) {
          await loadSession(initialSessions[0].thread_id);
        }
      } catch (bootError) {
        if (!cancelled) {
          setError(bootError.message || "Unable to initialize Polyhedric.");
        }
      }
    }

    boot();
    return () => {
      cancelled = true;
    };
  }, [loadCatalog, loadSession, loadSessions]);

  const openNewChat = useCallback(() => {
    setChatMode("general");
    setSelectedYearKey("");
    setSelectedCourse("");
    setError("");
    setModal("new-chat");
  }, []);

  const createChat = useCallback(async () => {
    setError("");
    setLoadingFlag("creating", true);

    try {
      let payload = {
        mode: "general",
        title: "General chat",
        degree_filter: null,
        year_filter: null,
        course_filter: null,
      };

      if (chatMode === "specific") {
        const group = findGroup(courseGroups, selectedYearKey);
        if (!group) {
          throw new Error("Choose an academic year before starting a specific chat.");
        }
        const course = group.courses.find((item) => item.value === selectedCourse);
        payload = {
          mode: "course",
          title: course ? course.label : `${group.degree.label} / ${group.year.label}`,
          degree_filter: group.degree.value,
          year_filter: group.year.value,
          course_filter: course?.value || null,
        };
      }

      const session = await polyRagApi.createSession(payload);
      setActiveSession(session);
      setMessages([]);
      setModal(null);
      closeMobileSidebar();
      await loadSessions();
    } catch (createError) {
      setError(createError.message || "Unable to create the chat.");
    } finally {
      setLoadingFlag("creating", false);
    }
  }, [
    chatMode,
    closeMobileSidebar,
    courseGroups,
    loadSessions,
    selectedCourse,
    selectedYearKey,
    setLoadingFlag,
  ]);

  const askToDelete = useCallback((session) => {
    setPendingDelete(session);
    setModal("delete-chat");
  }, []);

  const confirmDelete = useCallback(async () => {
    if (!pendingDelete) return;
    const deletedThreadId = pendingDelete.thread_id;
    const wasActive = activeSession?.thread_id === deletedThreadId;

    setLoadingFlag("deleting", true);
    setError("");

    try {
      await polyRagApi.deleteSession(deletedThreadId);
      setModal(null);
      setPendingDelete(null);
      const updatedSessions = await loadSessions();

      if (wasActive) {
        if (updatedSessions.length) {
          await loadSession(updatedSessions[0].thread_id);
        } else {
          setActiveSession(null);
          setMessages([]);
        }
      }
    } catch (deleteError) {
      setError(deleteError.message || "Unable to delete this chat.");
    } finally {
      setLoadingFlag("deleting", false);
    }
  }, [activeSession, loadSession, loadSessions, pendingDelete, setLoadingFlag]);

  const updateAssistantDraft = useCallback((content, metadata = {}) => {
    setMessages((current) => {
      const next = [...current];
      const lastIndex = next.length - 1;
      next[lastIndex] = {
        ...next[lastIndex],
        content,
        metadata: { ...(next[lastIndex]?.metadata || {}), ...metadata },
      };
      return next;
    });
  }, []);

  const sendMessage = useCallback(
    async (text) => {
      const message = text.trim();
      if (!message || loading.streaming) return;

      const filters = {
        degree_filter: activeSession?.degree_filter || null,
        year_filter: activeSession?.year_filter || null,
        course_filter: activeSession?.course_filter || null,
      };

      setError("");
      setLoadingFlag("streaming", true);
      setMessages((current) => [
        ...current,
        transientMessage("user", message),
        transientMessage("assistant", "Retrieving sources...", {}, true),
      ]);

      let assistantText = "";
      let threadId = activeSession?.thread_id || null;

      try {
        await polyRagApi.streamChat(
          {
            thread_id: threadId,
            message,
            ...filters,
          },
          {
            status: (event) => {
              if (!assistantText) updateAssistantDraft(event.message || "Working...");
            },
            metadata: (event) => {
              threadId = event.thread_id || threadId;
            },
            delta: (event) => {
              assistantText += event.text || "";
              updateAssistantDraft(assistantText || " ");
            },
            done: (event) => {
              threadId = event.thread_id || threadId;
              updateAssistantDraft(assistantText || "No answer generated.", {
                citations: event.citations || [],
              });
            },
          },
        );

        await loadSessions();
        if (threadId) await loadSession(threadId);
      } catch (streamError) {
        setMessages((current) => [
          ...current.slice(0, -1),
          transientMessage("assistant", streamError.message || "Unable to generate a response.", {
            error: true,
          }),
        ]);
      } finally {
        setLoadingFlag("streaming", false);
      }
    },
    [
      activeSession,
      loadSession,
      loadSessions,
      loading.streaming,
      setLoadingFlag,
      updateAssistantDraft,
    ],
  );

  const selectYear = useCallback((key) => {
    setSelectedYearKey(key);
    setSelectedCourse("");
  }, []);

  return {
    state: {
      activeSession,
      catalog,
      chatMode,
      courseGroups,
      error,
      loading,
      language,
      messages,
      mobileSidebarOpen,
      modal,
      pendingDelete,
      scopeLabel: scopeLabel(activeSession, courseGroups, language),
      selectedCourse,
      selectedGroup,
      selectedYearKey,
      sessions,
      sidebarCollapsed,
      theme,
    },
    actions: {
      askToDelete,
      closeMobileSidebar,
      confirmDelete,
      createChat,
      formatSessionDate: (value) => formatSessionDate(value, language),
      loadSession,
      openAbout: () => setModal("about"),
      openNewChat,
      sessionScopeLabel: (session) => sessionScopeLabel(session, courseGroups, language),
      setChatMode,
      setModal,
      setMobileSidebarOpen,
      setSelectedCourse,
      setSelectedYearKey: selectYear,
      setLanguage,
      setSidebarCollapsed,
      setTheme,
      sendMessage,
    },
  };
}
