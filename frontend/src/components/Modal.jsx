import { useEffect, useRef } from "react";

export function Modal({ open, title, eyebrow, compact = false, children, onClose }) {
  const modalRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const modal = modalRef.current;
    const previousFocus = document.activeElement;
    const focusable = modal?.querySelector(
      'button:not([disabled]), a[href], select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    );
    focusable?.focus();

    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose();
    };

    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      previousFocus?.focus?.();
    };
  }, [onClose, open]);

  if (!open) return null;

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section
        ref={modalRef}
        className={`modal ${compact ? "compact" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${title.replace(/\s+/g, "-").toLowerCase()}-title`}
      >
        <button className="modal-close" type="button" aria-label="Close dialog" onClick={onClose}>
          x
        </button>
        <div className="modal-heading">
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h2 id={`${title.replace(/\s+/g, "-").toLowerCase()}-title`}>{title}</h2>
        </div>
        {children}
      </section>
    </div>
  );
}
