import { LANGUAGES, t } from "../lib/i18n.js";

export function LanguageToggle({ language, onChange }) {
  return (
    <div className="language-toggle" role="group" aria-label={t("language", language)}>
      {Object.keys(LANGUAGES).map((code) => (
        <button
          key={code}
          className={`language-option ${language === code ? "active" : ""}`}
          type="button"
          aria-pressed={language === code}
          onClick={() => onChange(code)}
        >
          {code.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
