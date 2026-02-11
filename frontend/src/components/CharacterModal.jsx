import React, { useState, useEffect } from 'react';
import { X, Upload, Save, Loader2 } from 'lucide-react';
import { characterApi, API_BASE_URL } from '../lib/api';

const CharacterModal = ({ character, onClose, onSave }) => {
    // If character is null, it's create mode
    const isEdit = !!character;

    const [formData, setFormData] = useState({
        name: '',
        age: '',
        gender: '',
        description: '',
        lora_trigger: '',
        negative_prompt: '',
        ...character // Override with props if edit
    });

    const [thumbnail, setThumbnail] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(character?.thumbnail ? `${API_BASE_URL}${character.thumbnail}` : null);
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setThumbnail(file);
            setPreviewUrl(URL.createObjectURL(file));
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            let savedChar;
            if (isEdit) {
                // Update
                const { id, ...updates } = formData; // Exclude ID from body if API doesn't want it, but wait, ID is needed for update url
                // Our API implementation: PUT /characters/{id} takes Character object.
                // Assuming update_character merges or replaces.
                // Safest to just send everything.
                await characterApi.update(character.id, formData);
                savedChar = { ...character, ...formData };
            } else {
                // Create
                // ID generation needed? Backend creates ID?
                // Frontend CharacterBible logic was generating ID.
                // Let's defer to onSave prop if it handles creation logic, OR handle it here.
                // Currently backend create_character takes Character model.
                // Let's generate ID here for simplicity or let parent handle 'save' logic completely.
                // Actually, logic is better inside this modal to handle image upload sequentially.

                // We need a unique ID for image upload.
                const newId = `CHR-${Date.now().toString().slice(-6)}`;
                const newCharData = { ...formData, id: newId };
                await characterApi.create(newCharData);
                savedChar = newCharData;
            }

            // Upload Image
            if (thumbnail) {
                const formData = new FormData();
                formData.append('file', thumbnail);
                await characterApi.uploadThumbnail(savedChar.id, formData);
            }

            onSave(); // Refresh parent
            onClose();
        } catch (err) {
            console.error(err);
            alert("Failed to save character: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-[#1a1b1e] w-full max-w-4xl h-[90vh] rounded-xl border border-white/10 shadow-2xl overflow-hidden flex flex-col md:flex-row">

                {/* Left: Image & Main Info */}
                <div className="w-full md:w-1/3 bg-black/50 p-6 flex flex-col gap-6 border-r border-white/10">
                    <div className="relative aspect-[3/4] w-full bg-black/50 rounded-lg overflow-hidden border-2 border-dashed border-white/10 hover:border-blue-500/50 transition-colors group">
                        {previewUrl ? (
                            <img src={previewUrl} className="w-full h-full object-cover" alt="Preview" />
                        ) : (
                            <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500">
                                <Upload size={32} />
                                <span className="text-xs mt-2">Upload Portrait</span>
                            </div>
                        )}

                        <label className="absolute inset-0 flex items-center justify-center bg-black/60 opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity">
                            <span className="text-white font-bold flex items-center gap-2">
                                <Upload size={16} /> Change Image
                            </span>
                            <input type="file" className="hidden" accept="image/*" onChange={handleFileChange} />
                        </label>
                    </div>

                    <div className="space-y-4">
                        <div>
                            <label className="text-xs text-gray-400 uppercase tracking-widest">Name</label>
                            <input
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                className="w-full bg-transparent border-b border-white/20 py-2 text-xl font-bold text-white focus:outline-none focus:border-blue-500 transition-colors"
                                placeholder="Character Name"
                            />
                        </div>
                        <div className="flex gap-4">
                            <div className="flex-1">
                                <label className="text-xs text-gray-400 uppercase tracking-widest">Age</label>
                                <input
                                    name="age"
                                    value={formData.age}
                                    onChange={handleChange}
                                    className="w-full bg-transparent border-b border-white/20 py-1 text-white focus:outline-none focus:border-blue-500"
                                    placeholder="25"
                                />
                            </div>
                            <div className="flex-1">
                                <label className="text-xs text-gray-400 uppercase tracking-widest">Gender</label>
                                <input
                                    name="gender"
                                    value={formData.gender}
                                    onChange={handleChange}
                                    className="w-full bg-transparent border-b border-white/20 py-1 text-white focus:outline-none focus:border-blue-500"
                                    placeholder="Female"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right: Details & Config */}
                <div className="flex-1 p-6 flex flex-col bg-[#141414]">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-2xl font-bold text-white">{isEdit ? 'Edit Character' : 'Create Character'}</h2>
                        <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors text-gray-400 hover:text-white">
                            <X size={24} />
                        </button>
                    </div>

                    <div className="flex-1 space-y-6 overflow-y-auto pr-2 custom-scrollbar">
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-2">Description / Backstory</label>
                            <textarea
                                name="description"
                                value={formData.description}
                                onChange={handleChange}
                                className="w-full bg-black/30 border border-white/10 rounded-lg p-4 text-gray-300 focus:outline-none focus:border-blue-500 min-h-[120px] resize-y"
                                placeholder="Write the character's personality, backstory, and visual traits..."
                            />
                        </div>

                        <div className="bg-blue-900/10 border border-blue-500/20 rounded-lg p-4">
                            <h3 className="text-sm font-bold text-blue-400 mb-3 flex items-center gap-2">
                                AI Generation Settings
                            </h3>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs text-gray-400 mb-1">LoRA Trigger Word(s)</label>
                                    <input
                                        name="lora_trigger"
                                        value={formData.lora_trigger}
                                        onChange={handleChange}
                                        className="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm text-white focus:border-blue-500"
                                        placeholder="e.g. ohwx woman, cks suit"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-400 mb-1">Default Negative Prompt</label>
                                    <textarea
                                        name="negative_prompt"
                                        value={formData.negative_prompt}
                                        onChange={handleChange}
                                        className="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm text-white focus:border-blue-500 h-20"
                                        placeholder="low quality, bad anatomy..."
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="pt-6 border-t border-white/10 flex justify-end gap-3 mt-4">
                        <button
                            onClick={onClose}
                            className="px-6 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSubmit}
                            disabled={loading}
                            className="px-8 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
                        >
                            {loading ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
                            Save Character
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CharacterModal;
