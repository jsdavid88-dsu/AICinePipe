import React, { useState, useEffect } from 'react';
import { characterApi } from '../lib/api';
import { Users, Plus, Search } from 'lucide-react';
import CharacterCard from './CharacterCard';
import CharacterModal from './CharacterModal';

const CharacterBible = ({ projectId }) => {
    const [characters, setCharacters] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');

    // Modal State
    const [showModal, setShowModal] = useState(false);
    const [selectedChar, setSelectedChar] = useState(null);

    const fetchData = async () => {
        if (!projectId) return;
        setLoading(true);
        try {
            const res = await characterApi.list();
            setCharacters(res.data);
        } catch (error) {
            console.error("Failed to fetch characters:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [projectId]);

    const handleCreate = () => {
        setSelectedChar(null);
        setShowModal(true);
    };

    const handleEdit = (char) => {
        setSelectedChar(char);
        setShowModal(true);
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to delete this character?")) return;
        try {
            await characterApi.delete(id);
            fetchData();
        } catch (err) {
            alert("Delete failed: " + err.message);
        }
    };

    const filteredCharacters = characters.filter(c =>
        c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (c.description && c.description.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    return (
        <div className="h-full flex flex-col animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Users className="w-8 h-8 text-blue-500" /> Character Bible
                    </h2>
                    <p className="text-gray-400 mt-1">Manage cast, visual references, and consistent LoRA prompts.</p>
                </div>
                <div className="flex gap-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                        <input
                            type="text"
                            placeholder="Search characters..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="bg-black/30 border border-white/10 rounded-full pl-10 pr-4 py-2 text-white focus:outline-none focus:border-blue-500 w-64 transition-all"
                        />
                    </div>
                    <button
                        onClick={handleCreate}
                        className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-full font-bold flex items-center gap-2 shadow-lg hover:shadow-blue-500/20 transition-all"
                    >
                        <Plus size={20} /> Add Character
                    </button>
                </div>
            </div>

            {/* Grid Content */}
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                {loading ? (
                    <div className="h-64 flex items-center justify-center text-gray-500">Loading cast...</div>
                ) : filteredCharacters.length === 0 ? (
                    <div className="h-64 flex flex-col items-center justify-center text-gray-500 border-2 border-dashed border-white/5 rounded-xl">
                        <Users size={48} className="mb-4 opacity-50" />
                        <p>No characters found.</p>
                        <button onClick={handleCreate} className="text-blue-400 hover:underline mt-2">Create the first character</button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-10">
                        {filteredCharacters.map(char => (
                            <CharacterCard
                                key={char.id}
                                character={char}
                                onEdit={handleEdit}
                                onDelete={handleDelete}
                                onImageClick={handleEdit} // Open modal on image click
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* Modal */}
            {showModal && (
                <CharacterModal
                    character={selectedChar}
                    onClose={() => setShowModal(false)}
                    onSave={fetchData}
                />
            )}
        </div>
    );
};

export default CharacterBible;
