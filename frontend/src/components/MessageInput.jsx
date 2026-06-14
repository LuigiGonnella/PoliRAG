import { useEffect, useRef, useState } from "react";
import { t } from "../lib/i18n.js";

export function MessageInput({ language, loading, onSend }) {
  const [value, setValue] = useState("");
  const textareaRef = useRef(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 170)}px`;
  }, [value]);

  const submit = (event) => {
    event.preventDefault();
    const message = value.trim();
    if (!message || loading) return;
    setValue("");
    onSend(message);
  };

  return (
    <form className="composer" aria-label="Message composer" onSubmit={submit}>
      <div className="composer-box">
        <textarea
          ref={textareaRef}
          rows="1"
          value={value}
          placeholder={t("textareaPlaceholder", language)}
          aria-label="Message"
          disabled={loading}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              event.currentTarget.form.requestSubmit();
            }
          }}
        />
        <button className="send-button" type="submit" disabled={loading || !value.trim()}>
          {loading ? t("sending", language) : t("send", language)}
        </button>
      </div>
    </form>
  );
}
