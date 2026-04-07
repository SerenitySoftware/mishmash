"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

interface FileUploaderProps {
  onUpload: (file: File) => Promise<void>;
  accept?: Record<string, string[]>;
}

export function FileUploader({ onUpload, accept }: FileUploaderProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      setUploading(true);
      setError(null);
      try {
        await onUpload(acceptedFiles[0]);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: accept || {
      "text/csv": [".csv"],
      "application/json": [".json"],
      "application/octet-stream": [".parquet"],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div
      {...getRootProps()}
      className={`rounded-lg border-2 border-dashed p-8 text-center cursor-pointer transition
        ${isDragActive ? "border-brand-500 bg-brand-50" : "border-gray-300 hover:border-gray-400"}
        ${uploading ? "opacity-50 cursor-not-allowed" : ""}`}
    >
      <input {...getInputProps()} />
      {uploading ? (
        <p className="text-gray-600">Uploading...</p>
      ) : isDragActive ? (
        <p className="text-brand-700">Drop the file here</p>
      ) : (
        <div>
          <p className="text-gray-600">
            Drag & drop a file here, or click to select
          </p>
          <p className="mt-1 text-sm text-gray-400">
            Supports CSV, JSON, and Parquet files
          </p>
        </div>
      )}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
