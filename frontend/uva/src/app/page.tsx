import "use client";
import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";

type FileKind = "image" | "pdf";

const MAX_SIZE_MB = 15;
const ACCEPT_MIME = ["image/*", ".pdf"]; // used for accept attribute

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [fileKind, setFileKind] = useState<FileKind | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [serverUrl, setServerUrl] = useState<string | null>(null);
  const [serverLabels, setServerLabels] = useState<Array<{ Name?: string; Confidence?: number }>>([]);

  const inputRef = useRef<HTMLInputElement | null>(null);
  const acceptAttr = useMemo(() => ACCEPT_MIME.join(","), []);

  const resetStatus = () => {
    setMessage("");
    setError("");
    setProgress(0);
    setServerUrl(null);
    setServerLabels([]);
  };

  const validateFile = (f: File): string | null => {
    const isImage = f.type.startsWith("image/");
    const isPdf = f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf");
    if (!isImage && !isPdf) return "Only images and PDFs are allowed.";
    const sizeMb = f.size / (1024 * 1024);
    if (sizeMb > MAX_SIZE_MB) return `File is too large. Max ${MAX_SIZE_MB}MB.`;
    return null;
  };

  const prepareFile = (f: File) => {
    resetStatus();
    const validation = validateFile(f);
    if (validation) {
      setError(validation);
      clearSelectedFile();
      return;
    }

    // revoke previous object URL if any to avoid leaks
    if (previewUrl) {
      try {
        URL.revokeObjectURL(previewUrl);
      } catch {
        // ignore
      }
    }

    setFile(f);
    const kind: FileKind = f.type.startsWith("image/") ? "image" : "pdf";
    setFileKind(kind);

    if (kind === "image") {
      const url = URL.createObjectURL(f);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  };

  const clearSelectedFile = () => {
    setFile(null);
    setFileKind(null);
    if (previewUrl) {
      try {
        URL.revokeObjectURL(previewUrl);
      } catch {
        // ignore
      }
      setPreviewUrl(null);
    }
    // clear native input so user can re-select same file if needed
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) prepareFile(f);
  };

  const handleDrop = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const f = e.dataTransfer.files?.[0];
    if (f) prepareFile(f);
  };

  const handleDragOver = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    resetStatus();
    if (!file) {
      setError("Please choose a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploading(true);
      setProgress(0);

      const res = await axios.post("http://localhost:5000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (pe) => {
          // pe.total can be undefined for chunked requests; protect against that
          if (!pe.total || pe.total === 0) return;
          const pct = Math.round((pe.loaded * 100) / pe.total);
          setProgress(pct);
        },
        timeout: 120_000,
      });

      // show server feedback
      const data = res.data || {};
      setMessage(data.message || "Upload successful!");
      if (data.url) setServerUrl(data.url);
      if (Array.isArray(data.labels)) setServerLabels(data.labels);

      // clear selected file on success (optional - adjust to preference)
      clearSelectedFile();
    } catch (err: any) {
      const detail =
        err?.response?.data?.message ||
        err?.response?.data?.error ||
        err?.message ||
        "Upload failed. Please try again.";
      setError(detail);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  useEffect(() => {
    // cleanup on unmount
    return () => {
      if (previewUrl) {
        try {
          URL.revokeObjectURL(previewUrl);
        } catch {
          // ignore
        }
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white text-gray-900">
      <div className="mx-auto max-w-2xl px-4 py-10">
        <h1 className="text-3xl font-semibold tracking-tight">Universal Visual Assistant</h1>
        <p className="mt-2 text-gray-600">Upload an image or PDF. We’ll handle it and show you the result.</p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div>
            <label
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={[
                "group relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition",
                dragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400 bg-white",
              ].join(" ")}
            >
              <input
                ref={inputRef}
                type="file"
                accept={acceptAttr}
                onChange={handleFileChange}
                className="pointer-events-none absolute inset-0 h-full w-full opacity-0"
                aria-label="File upload"
              />
              <div className="flex flex-col items-center text-center">
                <div className="mb-3 inline-flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-gray-600">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 15v4a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-4M7 10l5-5 5 5M12 5v11" />
                  </svg>
                </div>
                <p className="text-sm">
                  <span className="font-medium text-blue-600">Click to choose</span> or drag & drop
                </p>
                <p className="mt-1 text-xs text-gray-500">Images or PDF, up to {MAX_SIZE_MB}MB</p>
              </div>
            </label>

            {file && (
              <div className="mt-4 flex items-center gap-4 rounded-lg border border-gray-200 bg-white p-4">
                {fileKind === "image" && previewUrl ? (
                  <img src={previewUrl} alt="Preview" className="h-16 w-16 rounded object-cover ring-1 ring-gray-200" />
                ) : (
                  <div className="inline-flex h-12 w-12 items-center justify-center rounded bg-gray-100 text-gray-600">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <path d="M14 2v6h6" />
                    </svg>
                  </div>
                )}

                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{file.name}</p>
                  <p className="text-xs text-gray-500">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    clearSelectedFile();
                    resetStatus();
                  }}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Remove
                </button>
              </div>
            )}
          </div>

          {uploading && (
            <div className="rounded-lg border border-gray-200 bg-white p-3">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-sm text-gray-600">Uploading…</span>
                <span className="text-sm font-medium">{progress}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded bg-gray-100">
                <div className="h-full bg-blue-600 transition-[width]" style={{ width: `${progress}%` }} />
              </div>
            </div>
          )}

          {message && (
            <div className="rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">{message}</div>
          )}
          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
          )}

          {serverUrl && (
            <div className="mt-2 text-sm">
              <a href={serverUrl} target="_blank" rel="noreferrer" className="text-blue-600 underline break-words">
                Open uploaded file
              </a>
            </div>
          )}

          {serverLabels.length > 0 && (
            <div className="mt-2 rounded border border-gray-100 bg-white p-3 text-sm">
              <strong className="block mb-1">Detected labels:</strong>
              <ul className="list-disc list-inside">
                {serverLabels.map((l, i) => (
                  <li key={i}>
                    {l.Name} {l.Confidence ? `- ${l.Confidence.toFixed(1)}%` : ""}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={!file || uploading}
              className={[
                "inline-flex items-center rounded-lg px-4 py-2 text-sm font-medium text-white transition focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
                !file || uploading ? "bg-blue-300 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700",
              ].join(" ")}
            >
              {uploading ? "Uploading..." : "Upload File"}
            </button>
            <p className="text-xs text-gray-500">Allowed: images or PDFs</p>
          </div>
        </form>
      </div>
    </main>
  );
}