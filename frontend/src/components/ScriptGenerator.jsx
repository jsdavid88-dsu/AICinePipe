import React, { useState, useEffect } from 'react';
import { Sparkles, ChevronDown, Loader2, AlertCircle, Check, Wand2, FileText } from 'lucide-react';
import { shotApi } from '../lib/api';

const PROVIDER_MODELS = {
    openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4'],
    anthropic: ['claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307'],
    gemini: ['gemini-2.0-flash', 'gemini-2.5-pro-preview-05-06', 'gemini-1.5-flash'],
    ollama: ['llama3', 'mistral', 'codellama', 'gemma2'],
};

const PROVIDER_LABELS = {
    openai: { label: 'OpenAI', icon: '🟢', env: 'OPENAI_API_KEY' },
    anthropic: { label: 'Anthropic', icon: '🟠', env: 'ANTHROPIC_API_KEY' },
    gemini: { label: 'Google Gemini', icon: '🔵', env: 'GOOGLE_API_KEY' },
    ollama: { label: 'Ollama (Local)', icon: '🟣', env: null },
};

export default function ScriptGenerator({ onGenerated }) {
    const [scriptText, setScriptText] = useState('');
    const [provider, setProvider] = useState('openai');
    const [model, setModel] = useState('gpt-4o');
    const [apiKey, setApiKey] = useState('');
    const [temperature, setTemperature] = useState(0.7);
    const [autoCreate, setAutoCreate] = useState(true);
    const [baseUrl, setBaseUrl] = useState('');

    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [providers, setProviders] = useState([]);
    const [showAdvanced, setShowAdvanced] = useState(false);

    // Fetch available providers on mount
    useEffect(() => {
        shotApi.listProviders()
            .then(res => setProviders(res.data?.providers || []))
            .catch(() => { });
    }, []);

    // Sync model when provider changes
    useEffect(() => {
        const models = PROVIDER_MODELS[provider] || [];
        if (models.length && !models.includes(model)) {
            setModel(models[0]);
        }
    }, [provider]);

    const handleGenerate = async () => {
        if (!scriptText.trim()) return;

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const payload = {
                script_text: scriptText,
                provider,
                model,
                temperature,
                auto_create: autoCreate,
            };
            if (apiKey.trim()) payload.api_key = apiKey;
            if (baseUrl.trim()) payload.base_url = baseUrl;

            const { data } = await shotApi.generateFromScript(payload);
            setResult(data);
            if (onGenerated) onGenerated(data);
        } catch (err) {
            const detail = err.response?.data?.detail || err.message;
            setError(detail);
        } finally {
            setLoading(false);
        }
    };

    const providerInfo = PROVIDER_LABELS[provider] || {};
    const serverProvider = providers.find(p => p.name === provider);
    const hasEnvKey = serverProvider?.env_configured;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="p-2.5 bg-gradient-to-br from-violet-600 to-fuchsia-600 rounded-xl">
                    <Wand2 className="w-5 h-5 text-white" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-white">Script → Shots</h2>
                    <p className="text-xs text-gray-500">LLM 기반 자동 샷 리스트 생성 / AI-powered shot list generation</p>
                </div>
            </div>

            {/* Script Input */}
            <div className="bg-[#1a1b1e] rounded-xl border border-white/5 overflow-hidden">
                <div className="px-4 py-3 border-b border-white/5 flex items-center gap-2">
                    <FileText size={14} className="text-gray-500" />
                    <span className="text-xs font-medium text-gray-400">
                        대본 / 시나리오 입력 — Script / Scenario Input
                    </span>
                </div>
                <textarea
                    value={scriptText}
                    onChange={(e) => setScriptText(e.target.value)}
                    placeholder={"붉은 사막에 외로운 여행자가 걸어간다. 뒤에 두 개의 태양이 지고 있다...\n\nA lone traveler walks across a red desert. Two suns are setting behind them..."}
                    className="w-full bg-transparent text-sm text-white p-4 focus:outline-none resize-none placeholder-gray-600 font-mono leading-relaxed"
                    rows={8}
                    disabled={loading}
                />
                <div className="px-4 py-2 border-t border-white/5 flex items-center justify-between">
                    <span className="text-xs text-gray-600">
                        {scriptText.length} chars · ~{Math.ceil(scriptText.split(/\s+/).filter(Boolean).length / 100)} min read
                    </span>
                </div>
            </div>

            {/* Provider & Model Selection */}
            <div className="grid grid-cols-2 gap-3">
                <div>
                    <label className="block text-xs text-gray-500 mb-1.5">LLM Provider</label>
                    <select
                        value={provider}
                        onChange={(e) => setProvider(e.target.value)}
                        disabled={loading}
                        className="w-full bg-[#1a1b1e] border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white focus:border-violet-500 focus:outline-none transition-colors"
                    >
                        {Object.entries(PROVIDER_LABELS).map(([key, info]) => (
                            <option key={key} value={key}>
                                {info.icon} {info.label}
                            </option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="block text-xs text-gray-500 mb-1.5">Model</label>
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        disabled={loading}
                        className="w-full bg-[#1a1b1e] border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white focus:border-violet-500 focus:outline-none transition-colors"
                    >
                        {(PROVIDER_MODELS[provider] || []).map(m => (
                            <option key={m} value={m}>{m}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Env Key Status */}
            {providerInfo.env && (
                <div className={`flex items-center gap-2 text-xs px-3 py-2 rounded-lg ${hasEnvKey
                        ? 'bg-emerald-900/20 border border-emerald-500/20 text-emerald-400'
                        : 'bg-yellow-900/20 border border-yellow-500/20 text-yellow-400'
                    }`}>
                    {hasEnvKey ? (
                        <><Check size={12} /> {providerInfo.env} 설정됨 — .env에서 API 키 감지</>
                    ) : (
                        <><AlertCircle size={12} /> {providerInfo.env} 미설정 — 아래 API Key를 입력하거나 .env에 추가하세요</>
                    )}
                </div>
            )}

            {/* Advanced Options */}
            <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
                <ChevronDown size={14} className={`transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
                고급 설정 / Advanced Options
            </button>

            {showAdvanced && (
                <div className="space-y-3 bg-[#1a1b1e] rounded-xl border border-white/5 p-4 animate-in fade-in">
                    {/* API Key */}
                    <div>
                        <label className="block text-xs text-gray-500 mb-1.5">
                            API Key (선택 — .env에 설정되어 있으면 불필요)
                        </label>
                        <input
                            type="password"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder="sk-... or leave empty to use .env"
                            className="w-full bg-[#111] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-violet-500 focus:outline-none"
                            disabled={loading}
                        />
                    </div>

                    {/* Base URL (for Ollama) */}
                    {(provider === 'ollama' || provider === 'openai_compatible') && (
                        <div>
                            <label className="block text-xs text-gray-500 mb-1.5">Base URL</label>
                            <input
                                type="text"
                                value={baseUrl}
                                onChange={(e) => setBaseUrl(e.target.value)}
                                placeholder="http://localhost:11434"
                                className="w-full bg-[#111] border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-violet-500 focus:outline-none"
                                disabled={loading}
                            />
                        </div>
                    )}

                    {/* Temperature */}
                    <div>
                        <label className="block text-xs text-gray-500 mb-1.5">
                            Temperature: {temperature.toFixed(1)}
                        </label>
                        <input
                            type="range"
                            min="0" max="1.5" step="0.1"
                            value={temperature}
                            onChange={(e) => setTemperature(parseFloat(e.target.value))}
                            className="w-full accent-violet-500"
                            disabled={loading}
                        />
                        <div className="flex justify-between text-[10px] text-gray-600 mt-0.5">
                            <span>정확 / Precise</span><span>창의적 / Creative</span>
                        </div>
                    </div>

                    {/* Auto Create Toggle */}
                    <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={autoCreate}
                            onChange={(e) => setAutoCreate(e.target.checked)}
                            className="accent-violet-500 w-4 h-4"
                            disabled={loading}
                        />
                        자동으로 샷 생성 / Auto-create shots in project
                    </label>
                </div>
            )}

            {/* Generate Button */}
            <button
                onClick={handleGenerate}
                disabled={loading || !scriptText.trim()}
                className="w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white shadow-lg shadow-violet-500/20 hover:shadow-violet-500/30"
            >
                {loading ? (
                    <><Loader2 size={16} className="animate-spin" /> 분석 중... / Analyzing...</>
                ) : (
                    <><Sparkles size={16} /> 샷 리스트 생성 / Generate Shots</>
                )}
            </button>

            {/* Error */}
            {error && (
                <div className="bg-red-900/20 border border-red-500/20 rounded-xl p-4 text-sm text-red-300 flex items-start gap-2">
                    <AlertCircle size={16} className="mt-0.5 shrink-0" />
                    <div>
                        <p className="font-medium">생성 실패 / Generation Failed</p>
                        <p className="text-xs mt-1 text-red-400">{error}</p>
                    </div>
                </div>
            )}

            {/* Result */}
            {result && (
                <div className="bg-emerald-900/20 border border-emerald-500/20 rounded-xl p-4 text-sm space-y-3 animate-in fade-in">
                    <div className="flex items-center gap-2 text-emerald-300 font-medium">
                        <Check size={16} />
                        {result.shots_count}개 샷 생성 완료!
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-xs">
                        <div className="bg-black/20 rounded-lg p-2.5 text-center">
                            <div className="text-lg font-bold text-white">{result.shots_count}</div>
                            <div className="text-gray-500">Shots</div>
                        </div>
                        <div className="bg-black/20 rounded-lg p-2.5 text-center">
                            <div className="text-lg font-bold text-white">{result.total_duration?.toFixed(0) || '—'}s</div>
                            <div className="text-gray-500">Duration</div>
                        </div>
                        <div className="bg-black/20 rounded-lg p-2.5 text-center">
                            <div className="text-lg font-bold text-white">{result.model}</div>
                            <div className="text-gray-500">Model</div>
                        </div>
                    </div>
                    {result.created_ids?.length > 0 && (
                        <p className="text-xs text-emerald-500">
                            ✅ 프로젝트에 추가됨: {result.created_ids.join(', ')}
                        </p>
                    )}
                </div>
            )}
        </div>
    );
}
