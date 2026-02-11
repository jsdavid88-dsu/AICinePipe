import React, { useState, useEffect, useCallback } from 'react';
import { cpeApi } from '../lib/api';
import { X, Camera, Film, Sun, Sliders, ShieldCheck, AlertTriangle, Info, Zap, Eye, ChevronDown } from 'lucide-react';

/**
 * CinematicSelector — 3-tab modal for CPE configuration.
 * 
 * Tab 1: PRESETS — Film-reference presets (Blade Runner, Parasite, etc.)
 * Tab 2: CONFIGURE — Camera/Lens/Lighting/Mood dropdowns
 * Tab 3: VALIDATE — Real-time rule engine validation
 */

// Severity badge component
const SeverityBadge = ({ severity }) => {
    const styles = {
        error: 'bg-red-500/20 text-red-400 border-red-500/30',
        warning: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
        info: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    };
    const icons = {
        error: <AlertTriangle size={12} />,
        warning: <AlertTriangle size={12} />,
        info: <Info size={12} />,
    };
    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold border ${styles[severity] || styles.info}`}>
            {icons[severity]} {severity.toUpperCase()}
        </span>
    );
};

// Dropdown component for enum selection
const EnumDropdown = ({ label, icon, value, options, onChange }) => (
    <div className="space-y-1.5">
        <label className="text-[10px] text-gray-500 font-bold tracking-wider uppercase flex items-center gap-1.5">
            {icon} {label}
        </label>
        <div className="relative">
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="w-full appearance-none bg-[#1a1b1e] border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-amber-500/50 transition-colors cursor-pointer pr-8"
            >
                {options.map(opt => (
                    <option key={opt.value} value={opt.value} className="bg-[#1a1b1e]">
                        {opt.name.replace(/_/g, ' ')}
                    </option>
                ))}
            </select>
            <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
        </div>
    </div>
);

const CinematicSelector = ({ shotId, onSave, onClose }) => {
    const [activeTab, setActiveTab] = useState('presets'); // 'presets' | 'configure' | 'validate'

    // Presets state
    const [presets, setPresets] = useState({ live_action: {}, animation: {} });
    const [selectedPresetId, setSelectedPresetId] = useState(null);
    const [presetType, setPresetType] = useState('live_action');

    // Configure state — enum options
    const [enumCache, setEnumCache] = useState({});
    const [config, setConfig] = useState({
        camera_body: 'Alexa_35',
        sensor_size: 'Super35',
        lens_family: 'Zeiss_Supreme_Prime',
        focal_length: 50,
        is_anamorphic: false,
        time_of_day: 'Golden_Hour',
        lighting_source: 'Natural_Sun',
        lighting_style: 'Rembrandt',
        shot_size: 'MS',
        composition: 'Rule_of_Thirds',
        mood: 'Dramatic',
        color_tone: 'Warm_Saturated',
    });

    // Validation state
    const [validation, setValidation] = useState(null);
    const [promptPreview, setPromptPreview] = useState('');

    // Loading
    const [loading, setLoading] = useState(true);

    // ─── Data Loading ───────────────────────────────────────────────
    useEffect(() => {
        loadInitialData();
    }, []);

    const loadInitialData = async () => {
        setLoading(true);
        try {
            const [presetsRes, ...enumResults] = await Promise.all([
                cpeApi.listPresets(),
                fetchEnum('camera_body'),
                fetchEnum('sensor_size'),
                fetchEnum('lens_family'),
                fetchEnum('time_of_day'),
                fetchEnum('lighting_source'),
                fetchEnum('lighting_style'),
                fetchEnum('shot_size'),
                fetchEnum('composition'),
                fetchEnum('mood'),
                fetchEnum('color_tone'),
            ]);
            setPresets(presetsRes.data);
        } catch (err) {
            console.error("Failed to load CPE data", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchEnum = async (enumName) => {
        try {
            const res = await cpeApi.getEnum(enumName);
            setEnumCache(prev => ({ ...prev, [enumName]: res.data.values }));
            return res.data.values;
        } catch (err) {
            console.error(`Failed to load enum ${enumName}`, err);
            return [];
        }
    };

    // ─── Auto-validate on config change ─────────────────────────────
    const runValidation = useCallback(async () => {
        try {
            const payload = {
                project_type: "live_action",
                live_action: {
                    camera: {
                        body: config.camera_body,
                        sensor_size: config.sensor_size,
                    },
                    lens: {
                        family: config.lens_family,
                        focal_length_mm: config.focal_length,
                        is_anamorphic: config.is_anamorphic,
                    },
                    lighting: {
                        time_of_day: config.time_of_day,
                        source: config.lighting_source,
                        style: config.lighting_style,
                    },
                    visual_grammar: {
                        shot_size: config.shot_size,
                        composition: config.composition,
                        mood: config.mood,
                        color_tone: config.color_tone,
                    },
                },
            };
            const res = await cpeApi.validate(payload);
            setValidation(res.data);
        } catch (err) {
            console.error("Validation failed", err);
        }
    }, [config]);

    useEffect(() => {
        if (activeTab === 'validate' || activeTab === 'configure') {
            const debounce = setTimeout(runValidation, 300);
            return () => clearTimeout(debounce);
        }
    }, [config, activeTab, runValidation]);

    // ─── Generate prompt preview ────────────────────────────────────
    useEffect(() => {
        const parts = [
            `shot on ${config.camera_body.replace(/_/g, ' ')}`,
            `${config.lens_family.replace(/_/g, ' ')} ${config.focal_length}mm`,
            `${config.time_of_day.replace(/_/g, ' ').toLowerCase()} lighting`,
            `${config.mood.replace(/_/g, ' ').toLowerCase()} mood`,
            config.shot_size,
            config.composition.replace(/_/g, ' ').toLowerCase(),
        ];
        setPromptPreview(parts.join(', '));
    }, [config]);

    // ─── Apply Handlers ─────────────────────────────────────────────
    const handleApplyPreset = () => {
        if (!selectedPresetId) return;
        const allPresets = { ...presets.live_action, ...presets.animation };
        const preset = allPresets[selectedPresetId];
        if (!preset) return;

        onSave({
            technical: {
                camera: preset.camera?.body || preset.camera_body || '',
                lens: preset.lens?.family || preset.lens_family || '',
                preset_name: preset.name,
                preset_id: selectedPresetId,
            }
        });
        onClose();
    };

    const handleApplyConfig = () => {
        onSave({
            technical: {
                camera: config.camera_body.replace(/_/g, ' '),
                lens: `${config.lens_family.replace(/_/g, ' ')} ${config.focal_length}mm`,
                lighting: config.lighting_style.replace(/_/g, ' '),
                mood: config.mood,
                shot_size: config.shot_size,
            }
        });
        onClose();
    };

    const updateConfig = (key, value) => {
        setConfig(prev => ({ ...prev, [key]: value }));
    };

    // ─── Preset List ────────────────────────────────────────────────
    const presetEntries = Object.entries(
        presetType === 'live_action' ? (presets.live_action || {}) : (presets.animation || {})
    );

    // ─── Tab Content Renderers ──────────────────────────────────────

    const renderPresetsTab = () => (
        <div className="space-y-4">
            {/* Type Toggle */}
            <div className="flex bg-black/30 rounded-lg p-1 border border-white/5 w-fit">
                <button
                    onClick={() => setPresetType('live_action')}
                    className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${presetType === 'live_action' ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white/70'}`}
                >
                    LIVE ACTION ({Object.keys(presets.live_action || {}).length})
                </button>
                <button
                    onClick={() => setPresetType('animation')}
                    className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${presetType === 'animation' ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white/70'}`}
                >
                    ANIMATION ({Object.keys(presets.animation || {}).length})
                </button>
            </div>

            {/* Preset Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {presetEntries.map(([id, preset]) => (
                    <div
                        key={id}
                        onClick={() => setSelectedPresetId(id)}
                        className={`
                            group relative bg-[#1a1b1e] rounded-xl overflow-hidden cursor-pointer
                            border transition-all duration-200
                            ${selectedPresetId === id
                                ? 'border-amber-500 ring-1 ring-amber-500/50 scale-[1.02] z-10'
                                : 'border-white/10 hover:border-white/30 hover:scale-[1.01]'}
                        `}
                    >
                        {/* Gradient Header */}
                        <div className="h-20 bg-gradient-to-br from-amber-900/30 via-[#1a1b1e] to-purple-900/20 flex items-end p-4">
                            <div>
                                <h3 className={`font-bold text-sm ${selectedPresetId === id ? 'text-amber-400' : 'text-gray-200'}`}>
                                    {preset.name}
                                </h3>
                                {preset.reference && (
                                    <span className="text-[10px] text-gray-500 italic">
                                        Inspired by: {preset.reference}
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Tags */}
                        <div className="p-3 space-y-2">
                            <div className="flex flex-wrap gap-1">
                                {preset.camera?.body && (
                                    <span className="px-1.5 py-0.5 bg-blue-500/10 text-blue-300 rounded text-[10px] border border-blue-500/20">
                                        📷 {String(preset.camera.body).replace(/_/g, ' ')}
                                    </span>
                                )}
                                {preset.lens?.family && (
                                    <span className="px-1.5 py-0.5 bg-cyan-500/10 text-cyan-300 rounded text-[10px] border border-cyan-500/20">
                                        🔭 {String(preset.lens.family).replace(/_/g, ' ')}
                                    </span>
                                )}
                                {preset.lighting?.style && (
                                    <span className="px-1.5 py-0.5 bg-yellow-500/10 text-yellow-300 rounded text-[10px] border border-yellow-500/20">
                                        ☀️ {String(preset.lighting.style).replace(/_/g, ' ')}
                                    </span>
                                )}
                                {preset.visual_grammar?.mood && (
                                    <span className="px-1.5 py-0.5 bg-purple-500/10 text-purple-300 rounded text-[10px] border border-purple-500/20">
                                        🎭 {String(preset.visual_grammar.mood).replace(/_/g, ' ')}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {presetEntries.length === 0 && (
                <div className="h-48 flex flex-col items-center justify-center text-white/20">
                    <Film size={40} className="mb-3 opacity-30" />
                    <p className="text-sm">No presets available</p>
                    <p className="text-xs mt-1">Check backend CPE endpoints</p>
                </div>
            )}
        </div>
    );

    const renderConfigureTab = () => (
        <div className="space-y-6">
            {/* Camera & Lens Group */}
            <div className="bg-[#1a1b1e] rounded-xl p-5 border border-white/5">
                <h3 className="text-xs font-bold text-gray-400 tracking-wider mb-4 flex items-center gap-2">
                    <Camera size={14} className="text-blue-400" /> CAMERA & LENS
                </h3>
                <div className="grid grid-cols-2 gap-4">
                    <EnumDropdown
                        label="Camera Body" icon={<Camera size={10} />}
                        value={config.camera_body}
                        options={enumCache.camera_body || []}
                        onChange={(v) => updateConfig('camera_body', v)}
                    />
                    <EnumDropdown
                        label="Sensor Size" icon={<Zap size={10} />}
                        value={config.sensor_size}
                        options={enumCache.sensor_size || []}
                        onChange={(v) => updateConfig('sensor_size', v)}
                    />
                    <EnumDropdown
                        label="Lens Family" icon={<Eye size={10} />}
                        value={config.lens_family}
                        options={enumCache.lens_family || []}
                        onChange={(v) => updateConfig('lens_family', v)}
                    />
                    <div className="space-y-1.5">
                        <label className="text-[10px] text-gray-500 font-bold tracking-wider uppercase">
                            Focal Length (mm)
                        </label>
                        <input
                            type="number" min={8} max={600}
                            value={config.focal_length}
                            onChange={(e) => updateConfig('focal_length', parseInt(e.target.value) || 50)}
                            className="w-full bg-[#0f0f12] border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-amber-500/50 transition-colors"
                        />
                    </div>
                </div>
            </div>

            {/* Lighting Group */}
            <div className="bg-[#1a1b1e] rounded-xl p-5 border border-white/5">
                <h3 className="text-xs font-bold text-gray-400 tracking-wider mb-4 flex items-center gap-2">
                    <Sun size={14} className="text-yellow-400" /> LIGHTING
                </h3>
                <div className="grid grid-cols-3 gap-4">
                    <EnumDropdown
                        label="Time of Day" icon={<Sun size={10} />}
                        value={config.time_of_day}
                        options={enumCache.time_of_day || []}
                        onChange={(v) => updateConfig('time_of_day', v)}
                    />
                    <EnumDropdown
                        label="Source" icon={<Zap size={10} />}
                        value={config.lighting_source}
                        options={enumCache.lighting_source || []}
                        onChange={(v) => updateConfig('lighting_source', v)}
                    />
                    <EnumDropdown
                        label="Style" icon={<Sliders size={10} />}
                        value={config.lighting_style}
                        options={enumCache.lighting_style || []}
                        onChange={(v) => updateConfig('lighting_style', v)}
                    />
                </div>
            </div>

            {/* Visual Grammar Group */}
            <div className="bg-[#1a1b1e] rounded-xl p-5 border border-white/5">
                <h3 className="text-xs font-bold text-gray-400 tracking-wider mb-4 flex items-center gap-2">
                    <Film size={14} className="text-purple-400" /> VISUAL GRAMMAR
                </h3>
                <div className="grid grid-cols-2 gap-4">
                    <EnumDropdown
                        label="Shot Size" icon={<Camera size={10} />}
                        value={config.shot_size}
                        options={enumCache.shot_size || []}
                        onChange={(v) => updateConfig('shot_size', v)}
                    />
                    <EnumDropdown
                        label="Composition" icon={<Sliders size={10} />}
                        value={config.composition}
                        options={enumCache.composition || []}
                        onChange={(v) => updateConfig('composition', v)}
                    />
                    <EnumDropdown
                        label="Mood" icon={<Film size={10} />}
                        value={config.mood}
                        options={enumCache.mood || []}
                        onChange={(v) => updateConfig('mood', v)}
                    />
                    <EnumDropdown
                        label="Color Tone" icon={<Sun size={10} />}
                        value={config.color_tone}
                        options={enumCache.color_tone || []}
                        onChange={(v) => updateConfig('color_tone', v)}
                    />
                </div>
            </div>

            {/* Live Prompt Preview */}
            <div className="bg-black/40 rounded-xl p-4 border border-amber-500/20">
                <div className="flex items-center gap-2 mb-2">
                    <Zap size={12} className="text-amber-500" />
                    <span className="text-[10px] text-amber-400 font-bold tracking-wider">PROMPT PREVIEW</span>
                </div>
                <p className="text-xs text-gray-300 leading-relaxed font-mono">
                    {promptPreview}
                </p>
            </div>
        </div>
    );

    const renderValidateTab = () => (
        <div className="space-y-4">
            {/* Summary */}
            {validation && (
                <>
                    <div className={`p-4 rounded-xl border ${validation.status === 'valid'
                            ? 'bg-green-500/5 border-green-500/20'
                            : validation.status === 'warning'
                                ? 'bg-yellow-500/5 border-yellow-500/20'
                                : 'bg-red-500/5 border-red-500/20'
                        }`}>
                        <div className="flex items-center gap-3">
                            <ShieldCheck size={24} className={
                                validation.status === 'valid' ? 'text-green-400'
                                    : validation.status === 'warning' ? 'text-yellow-400'
                                        : 'text-red-400'
                            } />
                            <div>
                                <span className={`text-lg font-bold ${validation.status === 'valid' ? 'text-green-400'
                                        : validation.status === 'warning' ? 'text-yellow-400'
                                            : 'text-red-400'
                                    }`}>
                                    {validation.status === 'valid' ? 'Configuration Valid ✓'
                                        : validation.status === 'warning' ? 'Configuration has Warnings'
                                            : 'Configuration has Errors'}
                                </span>
                                <p className="text-xs text-gray-500 mt-0.5">
                                    {validation.messages?.length || 0} messages from {validation.rules_checked || 0} rules
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="space-y-2">
                        {(validation.messages || []).map((msg, i) => (
                            <div
                                key={i}
                                className={`p-3 rounded-lg border flex items-start gap-3 ${msg.severity === 'error' ? 'bg-red-500/5 border-red-500/10'
                                        : msg.severity === 'warning' ? 'bg-yellow-500/5 border-yellow-500/10'
                                            : 'bg-blue-500/5 border-blue-500/10'
                                    }`}
                            >
                                <SeverityBadge severity={msg.severity} />
                                <div className="flex-1">
                                    <p className="text-sm text-gray-200">{msg.rule}</p>
                                    <p className="text-xs text-gray-500 mt-1">{msg.message}</p>
                                </div>
                            </div>
                        ))}
                    </div>

                    {(!validation.messages || validation.messages.length === 0) && (
                        <div className="h-32 flex flex-col items-center justify-center text-green-400/50">
                            <ShieldCheck size={40} className="mb-2 opacity-50" />
                            <p className="text-sm">All rules passed!</p>
                        </div>
                    )}
                </>
            )}

            {!validation && (
                <div className="h-48 flex flex-col items-center justify-center text-white/20">
                    <ShieldCheck size={40} className="mb-3 opacity-30" />
                    <p className="text-sm">Switch to Configure tab to set options, then validate here</p>
                </div>
            )}
        </div>
    );

    // ─── Main Render ────────────────────────────────────────────────
    const tabs = [
        { id: 'presets', label: 'PRESETS', icon: <Film size={14} /> },
        { id: 'configure', label: 'CONFIGURE', icon: <Sliders size={14} /> },
        { id: 'validate', label: 'VALIDATE', icon: <ShieldCheck size={14} /> },
    ];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md animate-in fade-in duration-300">
            <div className="w-[1100px] h-[800px] bg-[#0f0f12] border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden">

                {/* Header & Tabs */}
                <div className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-[#141418]">
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2 text-white/80">
                            <Camera size={20} className="text-amber-500" />
                            <span className="font-bold tracking-wide">CINEMATICS</span>
                        </div>

                        {/* Tabs */}
                        <div className="flex bg-black/40 rounded-lg p-1 border border-white/5">
                            {tabs.map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`flex items-center gap-1.5 px-4 py-1.5 rounded-md text-xs font-medium transition-all ${activeTab === tab.id
                                            ? 'bg-white/10 text-white shadow-sm'
                                            : 'text-white/40 hover:text-white/70'
                                        }`}
                                >
                                    {tab.icon} {tab.label}
                                </button>
                            ))}
                        </div>

                        {/* Validation badge in header */}
                        {validation && activeTab !== 'validate' && (
                            <div className={`flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-bold ${validation.status === 'valid' ? 'bg-green-500/10 text-green-400'
                                    : validation.status === 'warning' ? 'bg-yellow-500/10 text-yellow-400'
                                        : 'bg-red-500/10 text-red-400'
                                }`}>
                                <ShieldCheck size={12} />
                                {validation.messages?.length || 0} issues
                            </div>
                        )}
                    </div>

                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full text-white/40 hover:text-white transition">
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 bg-[#0f0f12] custom-scrollbar">
                    {loading ? (
                        <div className="h-full flex flex-col items-center justify-center text-white/30 gap-3">
                            <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
                            <span className="text-xs tracking-wider">LOADING CPE ENGINE...</span>
                        </div>
                    ) : (
                        <>
                            {activeTab === 'presets' && renderPresetsTab()}
                            {activeTab === 'configure' && renderConfigureTab()}
                            {activeTab === 'validate' && renderValidateTab()}
                        </>
                    )}
                </div>

                {/* Footer */}
                <div className="h-16 border-t border-white/5 flex items-center justify-between px-8 bg-[#141418]">
                    <div className="flex items-center gap-4">
                        {activeTab === 'presets' && selectedPresetId && (
                            <div className="text-xs text-amber-400 font-mono">
                                SELECTED: <span className="text-white">
                                    {(presets.live_action?.[selectedPresetId] || presets.animation?.[selectedPresetId])?.name || selectedPresetId}
                                </span>
                            </div>
                        )}
                        {activeTab === 'configure' && (
                            <div className="text-xs text-gray-500 font-mono truncate max-w-[500px]">
                                {promptPreview}
                            </div>
                        )}
                    </div>
                    <button
                        onClick={activeTab === 'presets' ? handleApplyPreset : handleApplyConfig}
                        disabled={activeTab === 'presets' && !selectedPresetId}
                        className={`
                            px-6 py-2.5 rounded-lg font-bold text-xs tracking-wider transition-all
                            ${(activeTab === 'configure') || (activeTab === 'presets' && selectedPresetId)
                                ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-lg shadow-amber-900/20'
                                : activeTab === 'validate'
                                    ? 'bg-white/5 text-white/20 cursor-not-allowed'
                                    : 'bg-white/5 text-white/20 cursor-not-allowed'}
                        `}
                    >
                        {activeTab === 'presets' ? 'APPLY PRESET' : activeTab === 'configure' ? 'APPLY CONFIG' : 'CLOSE'}
                    </button>
                </div>

            </div>
        </div>
    );
};

export default CinematicSelector;
