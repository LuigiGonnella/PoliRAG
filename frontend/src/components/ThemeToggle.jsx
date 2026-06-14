export function ThemeToggle({ theme, onChange }) {
  return (
    <div className="icon-toggle-group" role="group" aria-label="Theme">
      <button
        className={`icon-toggle ${theme === "light" ? "active" : ""}`}
        type="button"
        aria-label="Light theme"
        aria-pressed={theme === "light"}
        onClick={() => onChange("light")}
      >
        <SunIcon />
      </button>
      <button
        className={`icon-toggle ${theme === "dark" ? "active" : ""}`}
        type="button"
        aria-label="Dark theme"
        aria-pressed={theme === "dark"}
        onClick={() => onChange("dark")}
      >
        <MoonIcon />
      </button>
    </div>
  );
}

function SunIcon() {
  return (
    <svg className="control-icon" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v3M12 19v3M4.9 4.9 7 7M17 17l2.1 2.1M2 12h3M19 12h3M4.9 19.1 7 17M17 7l2.1-2.1" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg className="control-icon moon-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20.8 14.6A8.9 8.9 0 0 1 9.4 3.2a.8.8 0 0 0-.8-1A10.2 10.2 0 1 0 21.8 15.4a.8.8 0 0 0-1-.8Z" />
    </svg>
  );
}
