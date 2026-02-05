import React, { useState, useRef } from 'react';
import { shotApi } from '../lib/api';
import { Upload, FileSpreadsheet, X, Check, AlertTriangle, ArrowRight } from 'lucide-react';

const ExcelImportModal = ({ projectId, onClose, onImportComplete }) => {
    const [file, setFile] = useState(null);
    const [previewData, setPreviewData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [step, setStep] = useState('upload'); // 'upload' | 'preview' | 'importing'
    const fileInputRef = useRef(null);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setFile(selectedFile);
            setStep('preview');
            // In a real Kitsu-like app, we might parse the Excel here client-side to show a diff
            // For now, we'll just show file info and ready state
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        const selectedFile = e.dataTransfer.files[0];
        if (selectedFile && (selectedFile.name.endsWith('.xlsx') || selectedFile.name.endsWith('.csv'))) {
            setFile(selectedFile);
            setStep('preview');
        }
    };

    const handleImport = async () => {
        if (!file) return;
        setLoading(true);
        setStep('importing');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('project_id', projectId);

        try {
            const res = await shotApi.import(formData);
            // res.data = { message, updated, created }

            // Show Success Result
            // Delay slightly for effect or just close
            onImportComplete(res.data);
            onClose();
        } catch (err) {
            console.error("Import failed", err);
            alert("Import failed: " + (err.response?.data?.detail || err.message));
            setLoading(false);
            setStep('preview');
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-[500px] bg-[#1a1a1e] border border-white/10 rounded-xl shadow-2xl overflow-hidden">

                {/* Header */}
                <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-[#202025]">
                    <div className="flex items-center gap-3">
                        <FileSpreadsheet className="text-green-500" size={20} />
                        <h2 className="text-sm font-bold text-white tracking-wide">IMPORT SHOT DATA</h2>
                    </div>
                    <button onClick={onClose} className="text-white/30 hover:text-white transition">
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-8">
                    {step === 'upload' && (
                        <div
                            className="border-2 border-dashed border-white/10 rounded-xl h-64 flex flex-col items-center justify-center gap-4 hover:border-white/20 hover:bg-white/5 transition-all cursor-pointer"
                            onDragOver={(e) => e.preventDefault()}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileChange}
                                accept=".xlsx, .csv"
                                className="hidden"
                            />
                            <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mb-2">
                                <Upload className="text-green-500" size={32} />
                            </div>
                            <div className="text-center">
                                <p className="text-white font-medium mb-1">Click to upload or drag & drop</p>
                                <p className="text-white/40 text-xs">Excel (.xlsx) or CSV files</p>
                            </div>
                        </div>
                    )}

                    {(step === 'preview' || step === 'importing') && (
                        <div className="flex flex-col gap-6">
                            <div className="flex items-center gap-4 p-4 bg-white/5 rounded-lg border border-white/10">
                                <div className="w-10 h-10 rounded bg-green-500/20 flex items-center justify-center text-green-400 font-bold text-xs">
                                    XLSX
                                </div>
                                <div className="flex-1 overflow-hidden">
                                    <h4 className="text-white text-sm font-medium truncate">{file?.name}</h4>
                                    <p className="text-white/40 text-xs">{(file?.size / 1024).toFixed(1)} KB</p>
                                </div>
                                <button onClick={() => { setFile(null); setStep('upload'); }} className="text-white/30 hover:text-white/80">
                                    <X size={16} />
                                </button>
                            </div>

                            <div className="space-y-3">
                                <div className="flex items-start gap-3 p-3 bg-amber-500/10 rounded border border-amber-500/20 text-xs">
                                    <AlertTriangle size={16} className="text-amber-500 shrink-0 mt-0.5" />
                                    <div className="text-amber-200/80">
                                        <strong className="text-amber-400 block mb-1">Important:</strong>
                                        Existing shots with matching IDs will be updated. New IDs will create new shots.
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="h-16 border-t border-white/5 flex items-center justify-between px-6 bg-[#202025]">
                    <button onClick={onClose} className="px-4 py-2 rounded text-xs font-medium text-white/50 hover:text-white hover:bg-white/5 transition">
                        CANCEL
                    </button>
                    {step === 'preview' && (
                        <button
                            onClick={handleImport}
                            className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-500 text-white text-xs font-bold rounded shadow-lg shadow-green-900/20 transition-all"
                        >
                            <span>IMPORT DATA</span>
                            <ArrowRight size={14} />
                        </button>
                    )}
                    {step === 'importing' && (
                        <div className="flex items-center gap-3 text-white/50 text-xs">
                            <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                            <span>Processing...</span>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
};

export default ExcelImportModal;
