import { MessageInput } from "./MessageInput.jsx";
import { MessageList } from "./MessageList.jsx";
import { sessionTitle, t } from "../lib/i18n.js";

export function ChatWindow({ state, actions }) {
  return (
    <section className="chat-region" aria-label="Chat">
      <MessageList
        language={state.language}
        messages={state.messages}
        emptyState={<EmptyState state={state} actions={actions} />}
      />
      <MessageInput language={state.language} loading={state.loading.streaming} onSend={actions.sendMessage} />
    </section>
  );
}

function EmptyState({ state, actions }) {
  const recentSessions = state.sessions.slice(0, 4);

  return (
    <div className="empty-state">
      <div className="empty-kicker">{t("studyAssistant", state.language)}</div>
      <h2>Polyhedric</h2>
      <p>{t("assistantDescription", state.language)}</p>

      {recentSessions.length ? (
        <div className="quick-chat-list" aria-label={t("recentChats", state.language)}>
          {recentSessions.map((session) => (
            <button
              key={session.thread_id}
              type="button"
              className="quick-chat-button"
              onClick={() => actions.loadSession(session.thread_id).catch(() => {})}
            >
              {sessionTitle(session, state.language)}
            </button>
          ))}
        </div>
      ) : (
        <p className="empty-note">{t("noRecentChats", state.language)}</p>
      )}

      {!state.courseGroups.length && !state.loading.catalog ? (
        <p className="empty-note">{t("courseCatalogMissing", state.language)}</p>
      ) : null}

      {state.error ? <p className="empty-note error-note">{state.error}</p> : null}
    </div>
  );
}
