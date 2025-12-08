"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";

// 1. SETUP & CONFIG
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/upload";
type FileKind = "image" | "pdf";
const MAX_SIZE_MB = 15;
const ACCEPT_MIME = ["image/*", ".pdf"];

// 2. ICONS (No external libraries needed)
const IconSun = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>;
const IconMoon = () => <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>;
const IconCloud = () => <svg className="w-12 h-12 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>;
const IconCheck = () => <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"/></svg>;

// 3. MAIN COMPONENT
export default function Home() {
    // Prevent Hydration Mismatch
    const [mounted, setMounted] = useState(false);
    const [isDark, setIsDark] = useState(true);

    // App State
    const [file, setFile] = useState<File | null>(null);
    const [fileKind, setFileKind] = useState<FileKind | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);

    // Results State
    const [serverLabels, setServerLabels] = useState<Array<{ Name?: string; Confidence?: number }>>([]);
    const [serverText, setServerText] = useState<string[]>([]);

    const inputRef = useRef<HTMLInputElement>(null);
    const acceptAttr = useMemo(() => ACCEPT_MIME.join(","), []);

    // Handle Mounting (Fixes "Text content does not match server-rendered HTML")
    useEffect(() => {
        setMounted(true);
        const savedTheme = localStorage.getItem("theme");
        if (savedTheme) {
            setIsDark(savedTheme === "dark");
        } else {
            setIsDark(window.matchMedia("(prefers-color-scheme: dark)").matches);
        }
    }, []);

    const toggleTheme = () => {
        const next = !isDark;
        setIsDark(next);
        localStorage.setItem("theme", next ? "dark" : "light");
    };

    // --- LOGIC ---
    const reset = () => { setMessage(""); setError(""); setProgress(0); setServerLabels([]); setServerText([]); };

    const prepareFile = (f: File) => {
        reset();
        const isImage = f.type.startsWith("image/");
        const isPdf = f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf");

        if (!isImage && !isPdf) return setError("Invalid file type. Only Images & PDFs.");
        if (f.size > MAX_SIZE_MB * 1024 * 1024) return setError(`File too large. Max ${MAX_SIZE_MB}MB.`);

        if (previewUrl) URL.revokeObjectURL(previewUrl);
        setFile(f);
        setFileKind(isImage ? "image" : "pdf");
        if (isImage) setPreviewUrl(URL.createObjectURL(f));
        else setPreviewUrl(null);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        try {
            setUploading(true);
            setProgress(0);
            const { data } = await axios.post(API_URL, formData, {
                headers: { "Content-Type": "multipart/form-data" },
                onUploadProgress: (pe) => pe.total && setProgress(Math.round((pe.loaded * 100) / pe.total)),
                timeout: 120000 // 2 mins
            });

            setMessage(data.message || "Success!");
            if (data.labels) setServerLabels(data.labels);
            if (data.text) setServerText(data.text);
        } catch (err: any) { // eslint-disable-line
            setError(err.response?.data?.message || "Connection Failed. Is the backend running?");
        } finally {
            setUploading(false);
            setProgress(0);
        }
    };

    // Avoid rendering until client is ready (Prevents flickering)
    if (!mounted) return <div className="min-h-screen bg-black" />;

    // --- STYLES ---
    const theme = {
        bg: isDark ? "bg-[#0A0A0A]" : "bg-[#F8FAFC]",
        text: isDark ? "text-white" : "text-slate-900",
        card: isDark ? "bg-[#171717] border-white/10" : "bg-white border-slate-200 shadow-xl shadow-slate-200/50",
        zone: isDark ? "bg-white/5 border-white/10 hover:bg-white/10" : "bg-slate-50 border-slate-200 hover:bg-white hover:border-blue-400",
        btn: isDark ? "bg-white text-black hover:bg-gray-200" : "bg-blue-600 text-white hover:bg-blue-700",
        sub: isDark ? "text-gray-400" : "text-gray-500"
    };

    return (
        <main className={`min-h-screen transition-colors duration-300 ${theme.bg} ${theme.text} font-sans selection:bg-blue-500/30`}>

            {/* TOP BAR */}
            <nav className="flex justify-between items-center px-6 py-4 border-b border-transparent">
                <div className="font-bold text-lg tracking-tight flex items-center gap-2">
                    <span className="bg-blue-600 w-2 h-2 rounded-full animate-pulse"/>
                    VECTOR AI
                    <span className="text-[10px] bg-red-500 text-white px-1.5 py-0.5 rounded ml-2 font-mono">BETA v3.0</span>
                </div>
                <button onClick={toggleTheme} className="p-2 rounded-full hover:bg-gray-500/10 transition-colors">
                    {isDark ? <IconSun /> : <IconMoon />}
                </button>
            </nav>

            <div className="max-w-3xl mx-auto px-6 py-12">

                {/* HEADLINE */}
                <div className="text-center mb-10">
                    <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4">
                        Upload. <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">Detect.</span> Extract.
                    </h1>
                    <p className={`text-lg ${theme.sub}`}>Next-Gen Computer Vision Interface</p>
                </div>

                {/* MAIN CARD */}
                <div className={`rounded-3xl p-1 border transition-all ${theme.card}`}>
                    <form onSubmit={handleSubmit} className="p-6 md:p-8 space-y-8">

                        {/* DRAG ZONE */}
                        <div className="relative group">
                            <label
                                className={`
                                    flex flex-col items-center justify-center h-52 rounded-2xl border-2 border-dashed transition-all cursor-pointer
                                    ${dragActive ? "border-blue-500 bg-blue-500/10" : theme.zone}
                                `}
                                onDrop={(e) => {
                                    e.preventDefault(); setDragActive(false);
                                    if(e.dataTransfer.files?.[0]) prepareFile(e.dataTransfer.files[0]);
                                }}
                                onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                                onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
                            >
                                <input ref={inputRef} type="file" accept={acceptAttr} onChange={(e) => e.target.files?.[0] && prepareFile(e.target.files[0])} className="hidden" />
                                <div className={`${theme.sub} group-hover:scale-110 transition-transform duration-300`}><IconCloud /></div>
                                <p className="font-medium">Drag & drop or click to upload</p>
                                <p className={`text-xs mt-2 ${theme.sub}`}>Supported: PDF, JPG, PNG</p>
                            </label>
                        </div>

                        {/* FILE PREVIEW */}
                        {file && (
                            <div className={`flex items-center gap-4 p-4 rounded-xl border ${isDark ? "bg-black/20 border-white/10" : "bg-slate-50 border-slate-200"}`}>
                                <div className="h-14 w-14 rounded-lg overflow-hidden bg-gray-500/10 flex items-center justify-center shrink-0">
                                    {fileKind === "image" && previewUrl ? <img src={previewUrl} alt="Preview" className="h-full w-full object-cover"/> : <span className="text-2xl">📄</span>}
                                </div>
                                <div className="min-w-0 flex-1">
                                    <p className="font-semibold truncate">{file.name}</p>
                                    <p className={`text-xs ${theme.sub}`}>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                                <button type="button" onClick={reset} className="text-sm text-red-400 hover:text-red-500 font-medium px-2">Remove</button>
                            </div>
                        )}

                        {/* PROGRESS BAR */}
                        {uploading && (
                            <div className="h-1 w-full bg-gray-200/20 rounded-full overflow-hidden">
                                <div className="h-full bg-blue-500 transition-all duration-300" style={{width: `${progress}%`}}/>
                            </div>
                        )}

                        {/* ALERTS */}
                        {error && <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-500 text-sm rounded-lg text-center font-medium">{error}</div>}
                        {message && !uploading && <div className="p-3 bg-green-500/10 border border-green-500/20 text-green-500 text-sm rounded-lg text-center font-medium flex items-center justify-center gap-2"><IconCheck /> {message}</div>}

                        {/* ACTION BUTTON */}
                        <button
                            type="submit"
                            disabled={!file || uploading}
                            className={`w-full py-4 rounded-xl font-bold tracking-wide transition-transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed ${theme.btn}`}
                        >
                            {uploading ? "PROCESSING..." : "RUN ANALYSIS"}
                        </button>
                    </form>
                </div>

                {/* RESULTS GRID */}
                {(serverLabels.length > 0 || serverText.length > 0) && (
                    <div className="grid md:grid-cols-2 gap-6 mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">

                        {/* LABELS */}
                        {serverLabels.length > 0 && (
                            <div className={`p-6 rounded-2xl border ${theme.card}`}>
                                <h3 className="font-bold mb-4 text-sm uppercase tracking-wider opacity-70">Detected Objects</h3>
                                <div className="flex flex-wrap gap-2">
                                    {serverLabels.map((l, i) => (
                                        <span key={i} className={`text-xs font-semibold px-2.5 py-1 rounded-md border ${isDark ? "bg-white/5 border-white/10" : "bg-slate-100 border-slate-200 text-slate-700"}`}>
                                            {l.Name} <span className="opacity-50 ml-1">{Math.round(l.Confidence || 0)}%</span>
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* OCR */}
                        {serverText.length > 0 && (
                            <div className={`p-6 rounded-2xl border ${theme.card}`}>
                                <h3 className="font-bold mb-4 text-sm uppercase tracking-wider opacity-70">Extracted Text</h3>
                                <div className={`h-48 overflow-y-auto text-sm font-mono p-3 rounded-lg border ${isDark ? "bg-black/30 border-white/5 text-gray-300" : "bg-slate-50 border-slate-200 text-slate-600"}`}>
                                    {serverText.map((line, i) => <div key={i} className="mb-2 border-b border-gray-500/10 pb-1">{line}</div>)}
                                </div>
                            </div>
                        )}
                    </div>
                )}

            </div>
        </main>
    );
}