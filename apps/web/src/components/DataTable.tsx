import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type DataTableColumn<TRow> = {
  key: string;
  header: string;
  className?: string;
  render: (row: TRow) => ReactNode;
};

type DataTableState = {
  loading?: boolean;
  error?: string | null;
  emptyMessage?: string;
};

type DataTableProps<TRow> = {
  columns: DataTableColumn<TRow>[];
  rows: TRow[];
  rowKey: (row: TRow) => string;
  rowClassName?: string;
  onRowClick?: (row: TRow) => void;
  selectedRowKey?: string | null;
  state?: DataTableState;
};

export function DataTable<TRow>({
  columns,
  rows,
  rowKey,
  rowClassName,
  onRowClick,
  selectedRowKey,
  state,
}: DataTableProps<TRow>) {
  return (
    <div className="min-w-0 overflow-x-auto rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)]">
      <table className="w-full min-w-full border-collapse">
        <thead>
          <tr className="border-b border-[color:var(--border)] bg-[color:var(--surface-2)] text-left">
            {columns.map((column) => (
              <th
                key={column.key}
                className={cn(
                  "px-4 py-3 text-xs font-medium text-[color:var(--text-muted)]",
                  column.className,
                )}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {state?.loading ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-6 text-sm text-[color:var(--text-muted)]"
              >
                Loading data…
              </td>
            </tr>
          ) : state?.error ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-6 text-sm text-rose-600"
              >
                {state.error}
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-6 text-sm text-[color:var(--text-muted)]"
              >
                {state?.emptyMessage ?? "No records found."}
              </td>
            </tr>
          ) : (
            rows.map((row) => {
              const key = rowKey(row);
              const selected = selectedRowKey === key;
              return (
              <tr
                key={key}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={cn(
                  "border-b border-[color:var(--border)] last:border-b-0",
                  onRowClick ? "cursor-pointer hover:bg-[color:var(--surface-2)]" : "",
                  selected ? "bg-[rgba(37,99,235,0.08)]" : "",
                  rowClassName ?? "align-top",
                )}
              >
                {columns.map((column) => (
                  <td key={column.key} className="px-4 py-3.5 text-sm text-[color:var(--text)]">
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

export type { DataTableColumn };
