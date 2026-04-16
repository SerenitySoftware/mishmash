"use client";

interface DataTableProps {
  columns: string[];
  rows: Record<string, unknown>[];
  dtypes?: Record<string, string>;
}

export function DataTable({ columns, rows, dtypes }: DataTableProps) {
  if (rows.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">No data to display</div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                <div>{col}</div>
                {dtypes?.[col] && (
                  <div className="font-normal text-gray-400 normal-case">
                    {dtypes[col]}
                  </div>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-gray-50">
              {columns.map((col) => (
                <td
                  key={col}
                  className="px-4 py-2 text-sm text-gray-700 whitespace-nowrap max-w-xs truncate"
                >
                  {formatValue(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "null";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
