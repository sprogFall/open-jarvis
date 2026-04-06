import type { ReactNode } from "react";

type KeyValueItem = {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
};

type KeyValueGridProps = {
  items: KeyValueItem[];
  className?: string;
};

export function KeyValueGrid({ items, className }: KeyValueGridProps) {
  const classes = ["key-value-grid", className ?? ""].filter(Boolean).join(" ");

  return (
    <div className={classes}>
      {items.map((item, index) => (
        <div className="key-value-card" key={`${item.label}-${index}`}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
          {item.hint ? <small>{item.hint}</small> : null}
        </div>
      ))}
    </div>
  );
}
