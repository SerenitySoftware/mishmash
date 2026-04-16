"use client";

import dynamic from "next/dynamic";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => (
    <div className="h-64 bg-gray-900 rounded-lg flex items-center justify-center text-gray-400">
      Loading editor...
    </div>
  ),
});

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  height?: string;
  readOnly?: boolean;
}

const languageMap: Record<string, string> = {
  python: "python",
  r: "r",
  sql: "sql",
};

export function CodeEditor({
  value,
  onChange,
  language = "python",
  height = "300px",
  readOnly = false,
}: CodeEditorProps) {
  return (
    <div className="rounded-lg overflow-hidden border border-gray-700">
      <MonacoEditor
        height={height}
        language={languageMap[language] || language}
        value={value}
        onChange={(v) => onChange(v || "")}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: "on",
          readOnly,
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 4,
          wordWrap: "on",
        }}
      />
    </div>
  );
}
