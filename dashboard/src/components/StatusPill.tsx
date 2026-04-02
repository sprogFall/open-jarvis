import { formatTaskStatus } from "../lib/format";

type StatusPillProps = {
  status: string;
  active?: boolean;
};

export function StatusPill({ status, active }: StatusPillProps) {
  return (
    <span
      className={`status-pill status-${status.toLowerCase().replace(/_/g, "-")}${active ? " status-active" : ""}`}
    >
      {active ? "在线" : formatTaskStatus(status)}
    </span>
  );
}
