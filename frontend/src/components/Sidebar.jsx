import { sessionTitle, t } from "../lib/i18n.js";

export function Sidebar({ state, actions }) {
  const sidebarImage = state.theme === "dark" ? "/assets/knowledge-dark.png" : "/assets/knowledge-light.png";

  return (
    <aside className="sidebar" aria-label="Chat history">
      <div className="sidebar-top">
        <div className="brand">
          <div className="brand-copy">
            <h1>Polyhedric</h1>
            <p>{t("studyAssistant", state.language)}</p>
          </div>
        </div>
        <button
          className="icon-button sidebar-close"
          type="button"
          aria-label={t("closeChatHistory", state.language)}
          onClick={actions.closeMobileSidebar}
        >
          <span aria-hidden="true">x</span>
        </button>
      </div>

      <button className="new-chat-button" type="button" onClick={actions.openNewChat}>
        <span aria-hidden="true">+</span>
        <span className="sidebar-label">{t("newChat", state.language)}</span>
      </button>

      <div className="session-list-header">
        <span className="sidebar-label">{t("previousChats", state.language)}</span>
        <span aria-label={t("chatCount", state.language)}>{state.sessions.length}</span>
      </div>

      <div className="session-list" aria-live="polite">
        {state.loading.sessions ? (
          <div className="history-empty">{t("loadingChats", state.language)}</div>
        ) : state.sessions.length ? (
          state.sessions.map((session) => (
            <SessionItem
              key={session.thread_id}
              session={session}
              title={sessionTitle(session, state.language)}
              active={state.activeSession?.thread_id === session.thread_id}
              label={actions.sessionScopeLabel(session)}
              date={actions.formatSessionDate(session.updated_at)}
              onOpen={() => actions.loadSession(session.thread_id).catch(() => {})}
              onDelete={() => actions.askToDelete(session)}
            />
          ))
        ) : (
          <div className="history-empty">{t("noRecentChats", state.language)}</div>
        )}
      </div>

      <div className="sidebar-note sidebar-label">
        <strong>{t("scopedRetrieval", state.language)}</strong>
        <span>{t("scopedRetrievalDescription", state.language)}</span>
      </div>

      <img
        className="sidebar-asset sidebar-label"
        src={sidebarImage}
        alt="Structured university document map"
      />
    </aside>
  );
}

function SessionItem({ session, title, active, label, date, onOpen, onDelete }) {
  return (
    <div className={`session-item ${active ? "active" : ""}`}>
      <button className="session-open" type="button" aria-current={active || undefined} onClick={onOpen}>
        <span className="session-title">{title}</span>
        <span className="session-meta">
          {label}
          {date ? ` - ${date}` : ""}
        </span>
      </button>
      <button className="session-delete" type="button" aria-label={`Delete ${session.title || "chat"}`} onClick={onDelete}>
        x
      </button>
    </div>
  );
}
