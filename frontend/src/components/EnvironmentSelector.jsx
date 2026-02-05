import React, { useState } from 'react';
import { Cloud, Sun, MapPin, Image as ImageIcon, X } from 'lucide-react';

const EnvironmentSelector = ({ shotId, initialEnv, onSave, onClose }) => {
    const [env, setEnv] = useState(initialEnv || { location: "", weather: "", time_of_day: "" });

    const handleChange = (field, value) => {
        setEnv(prev => ({ ...prev, [field]: value }));
    };

    const handleSave = () => {
        onSave({ environment: env });
        onClose();
    };

    const weatherOptions = ["Sunny", "Cloudy", "Overcast", "Rain", "Storm", "Snow", "Fog", "Haze"];
    const timeOptions = ["Day", "Night", "Golden Hour", "Blue Hour", "Dawn", "Dusk", "Midnight"];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div
                className="w-[500px] bg-[#1a1b26] border border-white/10 rounded-xl shadow-2xl overflow-hidden ring-1 ring-white/5"
            >
                {/* Header */}
                <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-[#1f202e]">
                    <div className="flex items-center gap-2 text-white/90">
                        <MapPin size={18} className="text-green-400" />
                        <span className="font-light tracking-wide">ENVIRONMENT</span>
                    </div>
                    <button onClick={onClose} className="text-white/40 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-6">
                    {/* Location */}
                    <div className="space-y-2">
                        <label className="text-xs font-mono text-white/50 ml-1">LOCATION / SET</label>
                        <input
                            type="text"
                            value={env.location}
                            onChange={(e) => handleChange('location', e.target.value)}
                            placeholder="e.g. Cyberpunk City Street, Interior Spaceship..."
                            className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-green-500/50 focus:ring-1 focus:ring-green-500/20 transition-all placeholder:text-white/20"
                            autoFocus
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        {/* Weather */}
                        <div className="space-y-2">
                            <label className="text-xs font-mono text-white/50 ml-1 flex items-center gap-1">
                                <Cloud size={10} /> WEATHER
                            </label>
                            <div className="relative">
                                <select
                                    value={env.weather || ""}
                                    onChange={(e) => handleChange('weather', e.target.value)}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm text-white appearance-none focus:outline-none focus:border-blue-500/50 hover:bg-white/5 transition-colors cursor-pointer"
                                >
                                    <option value="" className="bg-[#1a1b26]">Select Weather...</option>
                                    {weatherOptions.map(opt => (
                                        <option key={opt} value={opt} className="bg-[#1a1b26]">{opt}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* Time of Day */}
                        <div className="space-y-2">
                            <label className="text-xs font-mono text-white/50 ml-1 flex items-center gap-1">
                                <Sun size={10} /> TIME
                            </label>
                            <div className="relative">
                                <select
                                    value={env.time_of_day || ""}
                                    onChange={(e) => handleChange('time_of_day', e.target.value)}
                                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm text-white appearance-none focus:outline-none focus:border-amber-500/50 hover:bg-white/5 transition-colors cursor-pointer"
                                >
                                    <option value="" className="bg-[#1a1b26]">Select Time...</option>
                                    {timeOptions.map(opt => (
                                        <option key={opt} value={opt} className="bg-[#1a1b26]">{opt}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 pt-0">
                    <button
                        onClick={handleSave}
                        className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 text-white p-3 rounded-lg font-medium shadow-lg shadow-green-900/20 transition-all active:scale-[0.98]"
                    >
                        Update Environment
                    </button>
                </div>
            </div>
        </div>
    );
};

export default EnvironmentSelector;
