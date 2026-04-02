import type { ReactNode } from "react";

type SideSheetProps = {
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
};

export function SideSheet({
  title,
  subtitle,
  onClose,
  children,
}: SideSheetProps) {
  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <aside className="sheet-panel" onClick={(event) => event.stopPropagation()}>
        <div className="sheet-header">
          <div>
            <p className="eyebrow">Operation</p>
            <h2>{title}</h2>
            {subtitle ? <p className="muted">{subtitle}</p> : null}
          </div>
          <button className="ghost-button" onClick={onClose} type="button">
            关闭
          </button>
        </div>
        <div className="sheet-body">{children}</div>
      </aside>
    </div>
  );
}
