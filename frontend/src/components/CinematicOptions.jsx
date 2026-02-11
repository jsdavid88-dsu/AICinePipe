import React, { useState, useEffect } from 'react';
import { Camera, RefreshCw, Clapperboard, Search, Film, Sun, Eye, ShieldCheck } from 'lucide-react';
import { cpeApi } from '../lib/api';

/**
 * CinematicCard — displays a CPE preset in a compact card.
 */
const CinematicCard = ({ presetId, preset, isSelected, onClick }) => (
    <div
        onClick={onClick}
        className={`
            bg-[#1a1b1e] border rounded-xl overflow-hidden
            hover:border-amber-500/50 hover:bg-white/[0.02] transition-all
            group cursor-pointer relative
            ${isSelected ? 'border-amber-500 ring-1 ring-amber-500/30' : 'border-white/10'}
        `}
    >
        {/* Header gradient */}
        <div className="h-16 bg-gradient-to-br from-amber-900/20 via-[#1a1b1e] to-blue-900/10 flex items-end p-3">
            <div>
                <h3 className="font-bold text-white text-sm truncate pr-8">{preset.name}</h3>
                {preset.reference && (
                    <span className="text-[10px] text-gray-600 italic">{preset.reference}</span>
                )}
            </div>
            {isSelected && (
                <div className="absolute top-2 right-2 bg-amber-600 text-[10px] px-2 py-0.5 rounded text-white font-bold">
                    SELECTED
                </div>
            )}
        </div>

        {/* Technical details */}
        <div className="p-3 space-y-1.5">
            <div className="text-xs text-gray-400 space-y-1">
                {preset.camera?.body && (
                    <div className="flex justify-between">
                        <span className="text-gray-600 flex items-center gap-1"><Camera size={10} /> Camera</span>
                        <span className="text-gray-300 truncate ml-2">{String(preset.camera.body).replace(/_/g, ' ')}</span>
                    </div>
                )}
                {preset.lens?.family && (
                    <div className="flex justify-between">
                        <span className="text-gray-600 flex items-center gap-1"><Eye size={10} /> Lens</span>
                        <span className="text-gray-300 truncate ml-2">{String(preset.lens.family).replace(/_/g, ' ')}</span>
                    </div>
                )}
                {preset.lighting?.style && (
                    <div className="flex justify-between">
                        <span className="text-gray-600 flex items-center gap-1"><Sun size={10} /> Lighting</span>
                        <span className="text-gray-300 truncate ml-2">{String(preset.lighting.style).replace(/_/g, ' ')}</span>
                    </div>
                )}
            </div>

            {/* Tags */}
            <div className="flex flex-wrap gap-1 pt-2 border-t border-white/5">
                {preset.visual_grammar?.mood && (
                    <span className="px-1.5 py-0.5 bg-purple-500/10 text-purple-300 rounded border border-purple-500/20 text-[10px]">
                        {String(preset.visual_grammar.mood).replace(/_/g, ' ')}
                    </span>
                )}
                {preset.visual_grammar?.shot_size && (
                    <span className="px-1.5 py-0.5 bg-blue-500/10 text-blue-300 rounded border border-blue-500/20 text-[10px]">
                        {preset.visual_grammar.shot_size}
                    </span>
                )}
                {preset.visual_grammar?.color_tone && (
                    <span className="px-1.5 py-0.5 bg-amber-500/10 text-amber-300 rounded border border-amber-500/20 text-[10px]">
                        {String(preset.visual_grammar.color_tone).replace(/_/g, ' ')}
                    </span>
                )}
            </div>
        </div>
    </div>
);

/**
 * CinematicOptions — full-page CPE preset browser.
 * Shown on sidebar "Cinematic Options" tab.
 */
const CinematicOptions = ({ projectId }) => {
    const [presets, setPresets] = useState({ live_action: {}, animation: {} });
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [activeType, setActiveType] = useState('live_action');
    const [selectedId, setSelectedId] = useState(null);
    const [ruleCount, setRuleCount] = useState(null);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [presetsRes, rulesRes] = await Promise.all([
                cpeApi.listPresets(),
                cpeApi.ruleCount(),
            ]);
            setPresets(presetsRes.data);
            setRuleCount(rulesRes.data);
        } catch (err) {
            console.error("Failed to load CPE data", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [projectId]);

    // Filter presets by search
    const currentPresets = activeType === 'live_action' ? (presets.live_action || {}) : (presets.animation || {});
    const filteredEntries = Object.entries(currentPresets).filter(([id, preset]) =>
        preset.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="h-full flex flex-col animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Clapperboard className="w-8 h-8 text-amber-500" /> Cinema Prompt Engine
                    </h2>
                    <p className="text-gray-400 mt-1 flex items-center gap-3">
                        Professional cinematography presets and validation rules
                        {ruleCount && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-500/10 text-green-400 rounded text-[10px] font-bold border border-green-500/20">
                                <ShieldCheck size={10} /> {ruleCount.total} rules active
                            </span>
                        )}
                    </p>
                </div>
                <div className="flex gap-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                        <input
                            type="text"
                            placeholder="Search presets..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="bg-black/30 border border-white/10 rounded-full pl-10 pr-4 py-2 text-white focus:outline-none focus:border-amber-500 w-64 transition-all"
                        />
                    </div>
                    <button
                        onClick={fetchData}
                        disabled={loading}
                        className="bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-2 rounded-full font-bold flex items-center gap-2 border border-white/10 transition-all disabled:opacity-50"
                    >
                        <RefreshCw className={loading ? 'animate-spin' : ''} size={18} />
                        Refresh
                    </button>
                </div>
            </div>

            {/* Type Toggle */}
            <div className="flex bg-black/20 rounded-lg p-1 border border-white/5 w-fit mb-6">
                <button
                    onClick={() => setActiveType('live_action')}
                    className={`flex items-center gap-2 px-5 py-2 rounded-md text-sm font-medium transition-all ${activeType === 'live_action'
                            ? 'bg-white/10 text-white shadow-sm'
                            : 'text-white/40 hover:text-white/70'
                        }`}
                >
                    <Camera size={16} /> Live Action ({Object.keys(presets.live_action || {}).length})
                </button>
                <button
                    onClick={() => setActiveType('animation')}
                    className={`flex items-center gap-2 px-5 py-2 rounded-md text-sm font-medium transition-all ${activeType === 'animation'
                            ? 'bg-white/10 text-white shadow-sm'
                            : 'text-white/40 hover:text-white/70'
                        }`}
                >
                    <Film size={16} /> Animation ({Object.keys(presets.animation || {}).length})
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                {loading ? (
                    <div className="h-64 flex items-center justify-center text-gray-500 gap-3">
                        <div className="w-5 h-5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
                        Loading CPE presets...
                    </div>
                ) : filteredEntries.length === 0 ? (
                    <div className="h-64 flex flex-col items-center justify-center text-gray-500 border-2 border-dashed border-white/5 rounded-xl">
                        <Clapperboard size={48} className="mb-4 opacity-50" />
                        <p>No presets found{searchTerm ? ` matching "${searchTerm}"` : ''}.</p>
                        <p className="text-sm mt-2">Check that the CPE backend is running.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-10">
                        {filteredEntries.map(([id, preset]) => (
                            <CinematicCard
                                key={id}
                                presetId={id}
                                preset={preset}
                                isSelected={selectedId === id}
                                onClick={() => setSelectedId(selectedId === id ? null : id)}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default CinematicOptions;
