import { useEffect, useRef } from "react";
import { dedupeCitations } from "../lib/citations.js";
import { t } from "../lib/i18n.js";
import { escapeHtml, renderMarkdown } from "../lib/markdown.js";

export function MessageList({ messages, emptyState, language = "en" }) {
  const listRef = useRef(null);

  useEffect(() => {
    const list = listRef.current;
    if (!list || !messages.length) return;
    list.scrollTop = list.scrollHeight;
  }, [messages]);

  if (!messages.length) return emptyState;

  return (
    <div ref={listRef} className="messages" aria-live="polite" aria-label="Conversation">
      {messages.map((message, index) => (
        <Message key={`${message.created_at || index}-${index}`} message={message} language={language} />
      ))}
    </div>
  );
}

function Message({ message, language }) {
  const isAssistant = message.role === "assistant";
  const isError = Boolean(message.metadata?.error);
  const label = message.role === "user" ? t("userLabel", language) : isAssistant ? "Polyhedric" : message.role;

  return (
    <article className={`message ${message.role} ${isError ? "error" : ""}`}>
      <div className="message-label">{label}</div>
      <div
        className="bubble"
        dangerouslySetInnerHTML={{
          __html: isAssistant ? renderMarkdown(message.content) : escapeHtml(message.content),
        }}
      />
      {isAssistant ? <Citations citations={message.metadata?.citations || []} /> : null}
    </article>
  );
}

function Citations({ citations }) {
  const unique = dedupeCitations(citations).slice(0, 8);
  if (!unique.length) return null;

  return (
    <div className="citations" aria-label="Sources">
      {unique.map((citation) => {
        const page = citation.page ? ` p. ${citation.page}` : "";
        const label = `${citation.source || citation.type || "source"}${page}`;
        return (
          <span key={`${citation.type || "local"}-${label}`} className="citation" title={label}>
            {label}
          </span>
        );
      })}
    </div>
  );
}
