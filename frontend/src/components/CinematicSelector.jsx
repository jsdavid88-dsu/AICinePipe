import React, { useState, useEffect } from 'react';
import { cinematicApi } from '../lib/api';
import { X, Camera, Film, Sun } from 'lucide-react';

const CinematicSelector = ({ shotId, onSave, onClose }) => {
    const [presets, setPresets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedPresetId, setSelectedPresetId] = useState(null);
    const [activeTab, setActiveTab] = useState('styles'); // 'styles' | 'cameras'

    useEffect(() => {
        loadPresets();
    }, []);

    const loadPresets = async () => {
        setLoading(true);
        try {
            const res = await cinematicApi.listPresets();
            setPresets(res.data);
        } catch (err) {
            console.error("Failed to load presets", err);
        } finally {
            setLoading(false);
        }
    };

    const handleScan = async () => {
        setLoading(true);
        try {
            const res = await cinematicApi.scan();
            await loadPresets();
            alert(`Scan complete. Found ${res.data.count || 'files'}.`);
        } catch (err) {
            console.error("Scan failed", err);
            alert("Scan failed. Check console for details.");
            setLoading(false);
        }
    };

    const handleApply = () => {
        if (!selectedPresetId) return;
        const preset = presets.find(p => p.id === selectedPresetId);
        // Note: For Camera tab, we might need different logic if items aren't in 'presets'
        // For now, assuming presets covers both or we only show presets in 'styles'
        if (!preset) return;

        onSave({ technical: preset.technical }); // Just tech update for now
        onClose();
    };

    const filteredItems = activeTab === 'styles'
        ? presets // Show all presets in Styles for now
        : []; // TODO: Populate Cameras specifically if separate API exists or filter presets

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md animate-in fade-in duration-300">
            <div className="w-[1000px] h-[800px] bg-[#0f0f12] border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden">

                {/* Header & Tabs */}
                <div className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-[#141418]">
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2 text-white/80">
                            <Camera size={20} className="text-amber-500" />
                            <span className="font-bold tracking-wide">CINEMATICS</span>
                        </div>

                        {/* Tabs */}
                        <div className="flex bg-black/40 rounded-lg p-1 border border-white/5">
                            <button
                                onClick={() => setActiveTab('styles')}
                                className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${activeTab === 'styles' ? 'bg-white/10 text-white shadow-sm' : 'text-white/40 hover:text-white/70'}`}
                            >
                                STYLES
                            </button>
                            <button
                                onClick={() => setActiveTab('cameras')}
                                className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${activeTab === 'cameras' ? 'bg-white/10 text-white shadow-sm' : 'text-white/40 hover:text-white/70'}`}
                            >
                                CAMERAS
                            </button>
                        </div>
                    </div>

                    <div className="flex gap-2">
                        <button onClick={handleScan} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-xs text-white/60 rounded border border-white/5 transition-colors">
                            Scan Presets
                        </button>
                        <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full text-white/40 hover:text-white transition">
                            <X size={20} />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 bg-[#0f0f12]">
                    {loading ? (
                        <div className="h-full flex flex-col items-center justify-center text-white/30 gap-3">
                            <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
                            <span className="text-xs tracking-wider">LOADING ASSETS...</span>
                        </div>
                    ) : activeTab === 'cameras' && filteredItems.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-white/30">
                            <Camera size={48} className="mb-4 opacity-20" />
                            <p>Camera specific options coming soon...</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {filteredItems.map(preset => (
                                <div
                                    key={preset.id}
                                    onClick={() => setSelectedPresetId(preset.id)}
                                    // Remove aspect-video forcing to avoid collapse? No, aspect-video is fine if container has width.
                                    // The issue was absolute positioning of children without proper context.
                                    className={`
                                        group relative w-full aspect-video bg-black rounded-lg overflow-hidden cursor-pointer 
                                        border transition-all duration-200
                                        ${selectedPresetId === preset.id
                                            ? 'border-amber-500 ring-1 ring-amber-500/50 shadow-2xl scale-[1.02] z-10'
                                            : 'border-white/10 hover:border-white/30 hover:scale-[1.01] hover:z-10'}
                                    `}
                                >
                                    {/* Background Image */}
                                    <div className="absolute inset-0">
                                        {preset.images?.camera ? (
                                            <img
                                                src={`http://localhost:8002${preset.images.camera}`}
                                                alt={preset.name}
                                                className="w-full h-full object-cover opacity-60 group-hover:opacity-80 transition-opacity duration-500"
                                                onError={(e) => {
                                                    e.target.style.display = 'none';
                                                    // Show fallback via sibling text or icon?
                                                    // This setup relies on parent div background color if img hidden
                                                }}
                                            />
                                        ) : (
                                            <div className="w-full h-full bg-gradient-to-br from-[#1a1a20] to-[#0a0a0c]" />
                                        )}
                                    </div>

                                    {/* Fallback Icon if no image */}
                                    {!preset.images?.camera && (
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <Film className="text-white/10 group-hover:text-white/20" size={32} />
                                        </div>
                                    )}

                                    {/* Overlay Content */}
                                    <div className="absolute inset-0 p-4 flex flex-col justify-end bg-gradient-to-t from-black/90 via-black/20 to-transparent">
                                        <h3 className={`font-bold text-lg leading-tight mb-1 ${selectedPresetId === preset.id ? 'text-amber-400' : 'text-gray-200'}`}>
                                            {preset.name}
                                        </h3>
                                        <div className="flex flex-wrap gap-1.5">
                                            {preset.technical?.camera && (
                                                <span className="px-1.5 py-0.5 bg-white/10 rounded text-[10px] font-mono text-white/70 backdrop-blur-md border border-white/5">
                                                    {preset.technical.camera}
                                                </span>
                                            )}
                                            {preset.technical?.aspect_ratio && (
                                                <span className="px-1.5 py-0.5 bg-white/10 rounded text-[10px] font-mono text-white/70 backdrop-blur-md border border-white/5">
                                                    {preset.technical.aspect_ratio}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="h-20 border-t border-white/5 flex items-center justify-between px-8 bg-[#141418]">
                    <div className="flex items-center gap-4">
                        {selectedPresetId && (
                            <div className="text-xs text-amber-400 font-mono">
                                SELECTED: <span className="text-white">{presets.find(p => p.id === selectedPresetId)?.name}</span>
                            </div>
                        )}
                    </div>
                    <button
                        onClick={handleApply}
                        disabled={!selectedPresetId}
                        className={`
                            px-6 py-2.5 rounded-lg font-bold text-xs tracking-wider transition-all
                            ${selectedPresetId
                                ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-lg shadow-amber-900/20'
                                : 'bg-white/5 text-white/20 cursor-not-allowed'}
                        `}
                    >
                        APPLY PRESET
                    </button>
                </div>

            </div>
        </div>
    );
};

export default CinematicSelector;
