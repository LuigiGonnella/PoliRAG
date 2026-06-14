import { Modal } from "./Modal.jsx";
import { courseLabel, groupLabel, t } from "../lib/i18n.js";

export function NewChatModal({ state, actions }) {
  const open = state.modal === "new-chat";
  const specific = state.chatMode === "specific";
  const canCreate = !state.loading.creating && (!specific || Boolean(state.selectedYearKey));

  return (
    <Modal
      open={open}
      title={t("chooseSearch", state.language)}
      eyebrow={t("newChat", state.language)}
      onClose={() => actions.setModal(null)}
    >
      <div className="mode-selector" role="group" aria-label="Chat mode">
        <button
          className={`mode-card ${!specific ? "active" : ""}`}
          type="button"
          aria-pressed={!specific}
          onClick={() => actions.setChatMode("general")}
        >
          <strong>{t("general", state.language)}</strong>
          <span>{t("generalDescription", state.language)}</span>
        </button>
        <button
          className={`mode-card ${specific ? "active" : ""}`}
          type="button"
          aria-pressed={specific}
          onClick={() => actions.setChatMode("specific")}
        >
          <strong>{t("specific", state.language)}</strong>
          <span>{t("specificDescription", state.language)}</span>
        </button>
      </div>

      {specific ? (
        <div className="specific-fields">
          <label>
            <span>{t("year", state.language)}</span>
            <select
              value={state.selectedYearKey}
              disabled={state.loading.catalog || !state.courseGroups.length}
              onChange={(event) => actions.setSelectedYearKey(event.target.value)}
            >
              <option value="">{state.loading.catalog ? t("loadingYears", state.language) : t("selectYear", state.language)}</option>
              {state.courseGroups.map((group) => (
                <option key={group.key} value={group.key}>
                  {groupLabel(group, state.language)}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>
              {t("course", state.language)} <small>{t("optional", state.language)}</small>
            </span>
            <select
              value={state.selectedCourse}
              disabled={!state.selectedGroup}
              onChange={(event) => actions.setSelectedCourse(event.target.value)}
            >
              <option value="">
                {state.selectedGroup ? t("allCoursesInYear", state.language) : t("chooseYearFirst", state.language)}
              </option>
              {state.selectedGroup?.courses.map((course) => (
                <option key={course.value} value={course.value}>
                  {courseLabel(course, state.language)}
                </option>
              ))}
            </select>
          </label>

          <p className="field-help">
            {t("specificHelp", state.language)}
          </p>
        </div>
      ) : null}

      {state.error ? (
        <p className="form-error" role="alert">
          {state.error}
        </p>
      ) : null}

      <div className="modal-actions">
        <button className="button secondary" type="button" onClick={() => actions.setModal(null)}>
          {t("cancel", state.language)}
        </button>
        <button className="button primary" type="button" disabled={!canCreate} onClick={actions.createChat}>
          {state.loading.creating ? t("starting", state.language) : t("startChat", state.language)}
        </button>
      </div>
    </Modal>
  );
}
