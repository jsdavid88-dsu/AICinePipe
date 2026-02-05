import React, { useState, useEffect } from 'react';
import { characterApi } from '../lib/api';
import { X, User, Shield } from 'lucide-react';

const SubjectSelector = ({ shotId, currentSubjects, onSave, onClose }) => {
    const [characters, setCharacters] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedCharId, setSelectedCharId] = useState(null);
    const [action, setAction] = useState("");
    const [costume, setCostume] = useState("");

    // Design Direction: "Cinematic Casting" - Dark, Glassmorphism, Premium feel
    // DFII Score: 10 (Strong)

    useEffect(() => {
        loadCharacters();
    }, []);

    const loadCharacters = async () => {
        try {
            const res = await characterApi.list();
            setCharacters(res.data);
            setLoading(false);
        } catch (err) {
            console.error(err);
            setLoading(false);
        }
    };

    const handleAdd = () => {
        if (!selectedCharId) return;

        const subject = {
            character_id: selectedCharId,
            action: action,
            costume_override: costume || null,
            lora_weight: 1.0
        };

        // In a real app we might append, but for V1 let's just add one
        onSave([subject]);
        onClose();
    };

    if (loading) return <div className="p-4 text-white">Loading Casting Database...</div>;

    const selectedChar = characters.find(c => c.id === selectedCharId);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div
                className="w-[800px] h-[600px] bg-[#1a1b26] border border-white/10 rounded-xl shadow-2xl flex overflow-hidden ring-1 ring-white/5"
                style={{ boxShadow: '0 0 50px -12px rgba(0, 0, 0, 0.7)' }}
            >
                {/* Left: Character List */}
                <div className="w-1/2 border-r border-white/5 p-4 flex flex-col">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-light tracking-wide text-white/90">CASTING</h2>
                        <span className="text-xs font-mono text-white/40">{characters.length} AVAILABLE</span>
                    </div>

                    <div className="flex-1 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                        {characters.map(char => (
                            <div
                                key={char.id}
                                onClick={() => setSelectedCharId(char.id)}
                                className={`
                                    p-3 rounded-lg cursor-pointer transition-all duration-200 border
                                    flex items-center gap-3
                                    ${selectedCharId === char.id
                                        ? 'bg-blue-500/10 border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.1)]'
                                        : 'bg-white/5 border-transparent hover:bg-white/10'}
                                `}
                            >
                                <div className="w-10 h-10 rounded bg-black/40 flex items-center justify-center overflow-hidden">
                                    {/* Thumbnail placeholder */}
                                    <User size={20} className="text-white/40" />
                                </div>
                                <div>
                                    <div className={`font-medium ${selectedCharId === char.id ? 'text-blue-400' : 'text-white/80'}`}>
                                        {char.name}
                                    </div>
                                    <div className="text-xs text-white/40 truncate max-w-[150px]">
                                        {char.description || "No description"}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right: Action & Details */}
                <div className="w-1/2 p-6 bg-[#13141c] flex flex-col relative">
                    <button onClick={onClose} className="absolute top-4 right-4 text-white/40 hover:text-white">
                        <X size={20} />
                    </button>

                    {selectedChar ? (
                        <>
                            <div className="mb-6 text-center">
                                <div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-blue-900/20 to-purple-900/20 ring-1 ring-white/10 flex items-center justify-center mb-3">
                                    <User size={40} className="text-white/60" />
                                </div>
                                <h3 className="text-2xl font-light text-white">{selectedChar.name}</h3>
                                <p className="text-sm text-white/40 font-mono mt-1">{selectedChar.id}</p>
                            </div>

                            <div className="space-y-4 flex-1">
                                <div>
                                    <label className="block text-xs font-mono text-blue-400/80 mb-1.5 ml-1">ACTION PROMPT</label>
                                    <textarea
                                        className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 h-24 resize-none transition-all placeholder:text-white/20"
                                        placeholder="e.g. Running through the rain, looking back in fear..."
                                        value={action}
                                        onChange={(e) => setAction(e.target.value)}
                                        autoFocus
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs font-mono text-purple-400/80 mb-1.5 ml-1 flex items-center gap-1">
                                        COSTUME OVERRIDE <Shield size={10} />
                                    </label>
                                    <input
                                        type="text"
                                        className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/20 transition-all placeholder:text-white/20"
                                        placeholder="Optional (e.g. Wearing a tuxedo)"
                                        value={costume}
                                        onChange={(e) => setCostume(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div className="mt-6">
                                <button
                                    onClick={handleAdd}
                                    className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white p-3 rounded-lg font-medium shadow-lg shadow-blue-900/20 transition-all active:scale-[0.98]"
                                >
                                    Confirm Casting
                                </button>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-white/20">
                            <User size={48} className="mb-4 opacity-20" />
                            <p className="text-sm font-light">Select a character to assign</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SubjectSelector;
