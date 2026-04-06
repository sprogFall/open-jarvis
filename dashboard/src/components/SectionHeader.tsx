import type { ReactNode } from "react";

type SectionHeaderProps = {
  eyebrow: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  compact?: boolean;
  className?: string;
  titleAs?: "h2" | "h3" | "h4";
};

export function SectionHeader({
  eyebrow,
  title,
  description,
  actions,
  compact = false,
  className,
  titleAs = "h3",
}: SectionHeaderProps) {
  const Title = titleAs;
  const classes = ["panel-head", compact ? "compact" : "", className ?? ""]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes}>
      <div className="section-copy">
        <p className="eyebrow">{eyebrow}</p>
        <Title>{title}</Title>
        {description ? <p className="section-description muted">{description}</p> : null}
      </div>
      {actions ? <div className="section-actions">{actions}</div> : null}
    </div>
  );
}
