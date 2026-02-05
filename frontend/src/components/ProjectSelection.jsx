import React, { useState, useEffect } from 'react';
import { Plus, Film, X, Upload } from 'lucide-react';
import { projectApi } from '../lib/api';

const CreateProjectModal = ({ onClose, onSuccess }) => {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [thumbnail, setThumbnail] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const safeName = name.replace(/[^a-zA-Z0-9_-]/g, '_');
            if (!safeName) throw new Error("Invalid project ID");

            // 1. Create Project
            await projectApi.create(safeName, description);

            // 2. Upload Thumbnail if exists
            if (thumbnail) {
                const formData = new FormData();
                formData.append('file', thumbnail);
                await projectApi.uploadThumbnail(safeName, formData);
            }

            onSuccess(safeName);
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-[#1a1b1e] w-full max-w-md rounded-xl border border-white/10 shadow-2xl p-6 relative">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors"
                >
                    <X size={20} />
                </button>

                <h2 className="text-2xl font-bold mb-6 text-white">Create New Project</h2>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Project Name (ID)</label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="w-full bg-black/30 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors"
                            placeholder="my_awesome_project"
                            required
                        />
                        <p className="text-xs text-gray-600 mt-1">Only alphanumeric, underscore, hyphen allowed.</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Description (Optional)</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            className="w-full bg-black/30 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors h-24 resize-none"
                            placeholder="Short description..."
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Thumbnail (Optional)</label>
                        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-white/10 rounded-lg cursor-pointer hover:border-blue-500/50 hover:bg-white/5 transition-all">
                            {thumbnail ? (
                                <div className="text-sm text-green-400 flex items-center gap-2">
                                    <Film size={16} /> {thumbnail.name}
                                </div>
                            ) : (
                                <div className="flex flex-col items-center gap-2 text-gray-500">
                                    <Upload size={24} />
                                    <span className="text-xs">Click to upload image</span>
                                </div>
                            )}
                            <input
                                type="file"
                                className="hidden"
                                accept="image/*"
                                onChange={(e) => setThumbnail(e.target.files[0])}
                            />
                        </label>
                    </div>

                    {error && (
                        <div className="text-red-400 text-sm bg-red-500/10 p-3 rounded border border-red-500/20">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-4"
                    >
                        {loading ? 'Creating...' : 'Create Project'}
                    </button>
                </form>
            </div>
        </div>
    );
};

const ProjectCard = ({ name, onSelect }) => (
    <div className="group relative flex flex-col items-center gap-3 w-48 cursor-pointer">
        <div
            onClick={() => onSelect(name)}
            className="w-48 h-28 bg-[#1a1b1e] rounded-md border-2 border-transparent group-hover:border-white transition-all duration-200 flex items-center justify-center relative overflow-hidden group-hover:scale-105 shadow-lg"
        >
            {/* Thumbnail: Try to load from static path */}
            <img
                src={`http://localhost:8000/projects/${name}/assets/thumbnail.png`}
                onError={(e) => {
                    e.target.onerror = null;
                    e.target.parentElement.classList.add('bg-gradient-to-br', 'from-blue-900/20', 'to-purple-900/20');
                    e.target.style.display = 'none';
                }}
                className="w-full h-full object-cover"
                alt={name}
            />

            {/* Fallback Icon (Visible if img fails and is hidden) */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <Film className="w-10 h-10 text-gray-700 group-hover:text-white/50 transition-colors" />
            </div>

            {/* Hover Overlay */}
            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center z-10">
                <span className="bg-white text-black text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider scale-90 group-hover:scale-100 transition-transform">
                    Open
                </span>
            </div>
        </div>

        <div className="text-center group-hover:text-white text-gray-400 font-medium truncate w-full transition-colors">
            {name}
        </div>
    </div>
);

const AddProjectCard = ({ onCreate }) => (
    <div
        onClick={onCreate}
        className="group flex flex-col items-center gap-3 w-48 cursor-pointer"
    >
        <div className="w-48 h-28 bg-transparent border-2 border-dashed border-gray-700 rounded-md group-hover:border-gray-400 group-hover:bg-white/5 transition-all duration-200 flex items-center justify-center group-hover:scale-105">
            <Plus className="w-10 h-10 text-gray-700 group-hover:text-gray-400 transition-colors" />
        </div>
        <div className="text-center text-gray-600 group-hover:text-gray-400 font-medium transition-colors">
            Add Project
        </div>
    </div>
);

const ProjectSelection = ({ onSelectProject }) => {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showCreateModal, setShowCreateModal] = useState(false);

    const fetchProjects = async () => {
        try {
            setLoading(true);
            const res = await projectApi.list();
            setProjects(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchProjects();
    }, []);

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-[#141414] text-white animate-in fade-in duration-500 font-sans relative">
            <div className="mb-16 text-center space-y-4">
                <h1 className="text-6xl font-black tracking-tighter bg-gradient-to-r from-red-600 to-purple-600 bg-clip-text text-transparent drop-shadow-lg">
                    AICinePipe
                </h1>
                <p className="text-gray-400 text-lg tracking-widest uppercase">AI Video Production Pipeline</p>
            </div>

            <div className="flex flex-wrap items-start justify-center gap-8 max-w-6xl px-8 z-10">
                {projects.map(p => (
                    <ProjectCard
                        key={p}
                        name={p}
                        onSelect={onSelectProject}
                    />
                ))}
                <AddProjectCard onCreate={() => setShowCreateModal(true)} />
            </div>

            {showCreateModal && (
                <CreateProjectModal
                    onClose={() => setShowCreateModal(false)}
                    onSuccess={async (newId) => {
                        setShowCreateModal(false);
                        await fetchProjects();
                    }}
                />
            )}

            <div className="absolute bottom-6 text-center opacity-40 hover:opacity-100 transition-opacity">
                <p className="text-xs text-gray-500 uppercase tracking-widest font-semibold">
                    Joint Research by <span className="text-blue-500">Dongseo University</span> & <span className="text-red-500">Red Cat Gang Corp.</span>
                </p>
            </div>
        </div>
    );
};

export default ProjectSelection;
