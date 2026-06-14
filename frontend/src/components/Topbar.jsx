import { t } from "../lib/i18n.js";
import { LanguageToggle } from "./LanguageToggle.jsx";
import { ThemeToggle } from "./ThemeToggle.jsx";

export function Topbar({ state, actions }) {
  const toggleSidebar = () => {
    if (window.matchMedia("(max-width: 900px)").matches) {
      actions.setMobileSidebarOpen(!state.mobileSidebarOpen);
      return;
    }
    actions.setSidebarCollapsed(!state.sidebarCollapsed);
  };
  const sidebarOpen = window.matchMedia("(max-width: 900px)").matches
    ? state.mobileSidebarOpen
    : !state.sidebarCollapsed;

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          className="toolbar-button icon-only"
          type="button"
          aria-label={sidebarOpen ? t("menuCollapse", state.language) : t("menuOpen", state.language)}
          aria-expanded={sidebarOpen}
          onClick={toggleSidebar}
        >
          <span aria-hidden="true">{sidebarOpen ? "<" : ">"}</span>
        </button>
        <div className="context-block">
          <div className="eyebrow">{t("currentScope", state.language)}</div>
          <div className="scope-title">{state.scopeLabel}</div>
        </div>
      </div>

      <div className="topbar-actions" aria-label="Application actions">
        <ThemeToggle theme={state.theme} onChange={actions.setTheme} />
        <LanguageToggle language={state.language} onChange={actions.setLanguage} />
        <button className="toolbar-button" type="button" onClick={actions.openAbout}>
          {t("about", state.language)}
        </button>
      </div>
    </header>
  );
}
