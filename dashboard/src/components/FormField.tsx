import type { ReactNode } from "react";

type FormFieldProps = {
  label: string;
  htmlFor: string;
  children: ReactNode;
  className?: string;
  note?: string;
};

export function FormField({
  label,
  htmlFor,
  children,
  className,
  note,
}: FormFieldProps) {
  const classes = ["field", className ?? ""].filter(Boolean).join(" ");

  return (
    <div className={classes}>
      <label className="field-label" htmlFor={htmlFor}>
        {label}
      </label>
      {children}
      {note ? <small className="field-note">{note}</small> : null}
    </div>
  );
}
