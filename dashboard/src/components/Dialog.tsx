import { useEffect, useId, useRef } from "react";
import type { ReactNode } from "react";

type DialogProps = {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  size?: "default" | "wide";
  onClose: () => void;
  children: ReactNode;
};

export function Dialog({
  title,
  subtitle,
  eyebrow = "Detail",
  size = "default",
  onClose,
  children,
}: DialogProps) {
  const titleId = useId();
  const panelRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    panelRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <section
        aria-labelledby={titleId}
        aria-modal="true"
        className={`dialog-panel${size === "wide" ? " dialog-panel-wide" : ""}`}
        onClick={(event) => event.stopPropagation()}
        ref={panelRef}
        role="dialog"
        tabIndex={-1}
      >
        <div className="dialog-header">
          <div>
            <p className="eyebrow">{eyebrow}</p>
            <h2 id={titleId}>{title}</h2>
            {subtitle ? <p className="muted">{subtitle}</p> : null}
          </div>
          <button className="ghost-button" onClick={onClose} type="button">
            关闭
          </button>
        </div>
        <div className="dialog-body">{children}</div>
      </section>
    </div>
  );
}
