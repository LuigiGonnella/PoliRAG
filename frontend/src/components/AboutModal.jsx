import { Modal } from "./Modal.jsx";
import { t } from "../lib/i18n.js";

export function AboutModal({ language = "en", open, onClose }) {
  return (
    <Modal open={open} title="Polyhedric" eyebrow={t("about", language)} onClose={onClose}>
      <p>
        {language === "it"
          ? "Polyhedric e un assistente basato su RAG progettato per rispondere usando appunti e documenti universitari. Aiuta a studiare, cercare negli appunti e capire il materiale dei corsi piu rapidamente."
          : "Polyhedric is a RAG-based assistant built to answer questions using university notes and documents. It helps make studying, searching notes, and understanding course material faster and easier."}
      </p>
      <p>
        {language === "it"
          ? "Puoi fare domande generali sulla base di conoscenza, limitare la ricerca a un anno accademico o concentrarti su un corso specifico quando serve una risposta piu precisa."
          : "You can ask broad questions across the knowledge base, scope retrieval to an academic year, or focus on a specific course when you need a more precise answer."}
      </p>
      <div className="about-links" aria-label="Contact links">
        <a href="https://luigigonnella.dev" target="_blank" rel="noreferrer">
          {t("portfolio", language)}
        </a>
        <a href="https://github.com/LuigiGonnella" target="_blank" rel="noreferrer">
          {t("github", language)}
        </a>
        <a href="mailto:luigigonnella02@gmail.com">{t("email", language)}</a>
      </div>
    </Modal>
  );
}
