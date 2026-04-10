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
    <div className="overflow-x-auto rounded-2xl border border-white/7 bg-white/3">
      <table className="w-full min-w-[1080px] border-collapse">
        <thead>
          <tr className="border-b border-white/7 bg-black/10 text-left">
            {columns.map((column) => (
              <th
                key={column.key}
                className={cn(
                  "px-4 py-3 text-[length:var(--type-metadata-size)] uppercase tracking-[0.14em] text-slate-500",
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
                className="px-4 py-6 text-sm text-slate-500"
              >
                Loading data…
              </td>
            </tr>
          ) : state?.error ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-6 text-sm text-rose-200"
              >
                {state.error}
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-6 text-sm text-slate-500"
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
                  "border-b border-white/7 last:border-b-0",
                  onRowClick ? "cursor-pointer hover:bg-white/5" : "",
                  selected ? "bg-[color:var(--color-accent-soft)]/30" : "",
                  rowClassName ?? "align-top",
                )}
              >
                {columns.map((column) => (
                  <td key={column.key} className="px-4 py-3.5 text-sm text-slate-200">
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
