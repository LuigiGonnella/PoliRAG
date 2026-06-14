import { Modal } from "./Modal.jsx";
import { sessionTitle, t } from "../lib/i18n.js";

export function DeleteChatModal({ state, actions }) {
  return (
    <Modal
      open={state.modal === "delete-chat"}
      title={t("removeConversation", state.language)}
      eyebrow={t("deleteChat", state.language)}
      compact
      onClose={() => actions.setModal(null)}
    >
      <p>
        {t("deletePrompt", state.language)}{" "}
        <strong>{state.pendingDelete ? sessionTitle(state.pendingDelete, state.language) : t("thisChat", state.language)}</strong>{" "}
        {t("deletePromptEnd", state.language)}
      </p>
      {state.error ? (
        <p className="form-error" role="alert">
          {state.error}
        </p>
      ) : null}
      <div className="modal-actions">
        <button className="button secondary" type="button" onClick={() => actions.setModal(null)}>
          {t("cancel", state.language)}
        </button>
        <button className="button danger" type="button" disabled={state.loading.deleting} onClick={actions.confirmDelete}>
          {state.loading.deleting ? t("deleting", state.language) : t("delete", state.language)}
        </button>
      </div>
    </Modal>
  );
}
