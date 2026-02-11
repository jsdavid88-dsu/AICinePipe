import React, { useState, useEffect } from 'react';
import { MoreHorizontal, Plus, Camera, MapPin, Users, Settings, Play, Upload, Download, LayoutGrid, List as ListIcon, ChevronDown, MessageSquare, X, Send, FolderOpen, Lock } from 'lucide-react';
import { shotApi, characterApi, cinematicApi, jobApi } from '../lib/api';
import SubjectSelector from './SubjectSelector';
import CinematicSelector from './CinematicSelector';
import EnvironmentSelector from './EnvironmentSelector';
import ExcelImportModal from './ExcelImportModal';

const ShotTable = ({ projectId, onShotSelect }) => {
    const [shots, setShots] = useState([]);
    const [selectedIds, setSelectedIds] = useState(new Set());
    const [loading, setLoading] = useState(false);

    // Subject Selector State
    const [showSubjectSelector, setShowSubjectSelector] = useState(false);
    const [showCinematicSelector, setShowCinematicSelector] = useState(false);
    const [showEnvironmentSelector, setShowEnvironmentSelector] = useState(false);
    const [showImportModal, setShowImportModal] = useState(false);
    const [viewMode, setViewMode] = useState('list'); // 'list' | 'gallery'
    const [activeShotId, setActiveShotId] = useState(null);

    // Comments/History Panel
    const [showCommentsPanel, setShowCommentsPanel] = useState(false);
    const [activeShotForComments, setActiveShotForComments] = useState(null);

    // Drag & Drop State
    const [dragOverId, setDragOverId] = useState(null);

    const handleCommentsClick = (shotId) => {
        setActiveShotForComments(shots.find(s => s.id === shotId));
        setShowCommentsPanel(true);
    };

    // Data Loading
    const fetchData = async () => {
        if (!projectId) return;
        setLoading(true);
        try {
            const res = await shotApi.list();
            setShots(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData() }, [projectId]);

    // Selection Logic
    const toggleSelect = (id) => {
        const newSet = new Set(selectedIds);
        if (newSet.has(id)) newSet.delete(id);
        else newSet.add(id);
        setSelectedIds(newSet);
    };

    const toggleSelectAll = () => {
        if (selectedIds.size === shots.length) setSelectedIds(new Set());
        else setSelectedIds(new Set(shots.map(s => s.id)));
    };

    // Drag & Drop Handlers
    const handleDragStart = (e, shot) => {
        e.dataTransfer.setData("text/plain", shot.id);
        e.dataTransfer.effectAllowed = "move";
    };

    const handleDragOver = (e, overId) => {
        e.preventDefault();
        setDragOverId(overId);
    };

    const handleDrop = async (e, targetShot) => {
        e.preventDefault();
        setDragOverId(null);

        const draggedId = e.dataTransfer.getData("text/plain");
        if (draggedId === targetShot.id) return;

        // Reorder locally
        const newShots = [...shots];
        const draggedIdx = newShots.findIndex(s => s.id === draggedId);
        const targetIdx = newShots.findIndex(s => s.id === targetShot.id);

        const [movedShot] = newShots.splice(draggedIdx, 1);
        newShots.splice(targetIdx, 0, movedShot);

        setShots(newShots);

        // Save new order to backend
        try {
            await shotApi.reorder(newShots.map(s => s.id));
        } catch (err) {
            console.error("Reorder failed", err);
            fetchData(); // Revert on fail
        }
    };

    const handleDragEnd = () => {
        setDragOverId(null);
    };

    // Inline Edit Logic
    const handleCellUpdate = async (id, field, value) => {
        const idsToUpdate = (selectedIds.has(id) && selectedIds.size > 1)
            ? Array.from(selectedIds)
            : [id];

        // Optimistic update
        setShots(prev => prev.map(s => idsToUpdate.includes(s.id) ? { ...s, [field]: value } : s));

        try {
            if (idsToUpdate.length > 1) {
                await shotApi.bulkUpdate(idsToUpdate, { [field]: value });
            } else {
                await shotApi.update(id, { [field]: value });
            }
        } catch (err) {
            console.error("Update failed", err);
            fetchData(); // Revert
        }
    };

    const handleBulkUpdate = () => {
        if (selectedIds.size === 0) return;
        alert("Select multiple rows and edit any cell to update all selected items!");
    };

    // Create Logic with Server-Side ID
    const handleCreateShot = async () => {
        const tempId = `SHT-TEMP-${Date.now()}`;
        const newShot = {
            id: tempId,
            scene_description: "",
            subjects: [],
            environment: { location: "" },
            technical: { camera: "Arri Alexa", aspect_ratio: "16:9" },
            status: "pending"
        };

        setShots(prev => [...prev, newShot]);

        try {
            const res = await shotApi.createWithServerId({
                scene_description: "",
                status: "pending"
            });
            // Replace temp shot with real one from server
            setShots(prev => prev.map(s => s.id === tempId ? res.data : s));
        } catch (err) {
            console.error("Create failed", err);
            setShots(prev => prev.filter(s => s.id !== tempId));
            alert("Failed to create shot");
        }
    };

    // Confirm Shot Logic
    const handleConfirmShot = async (shot) => {
        if (!confirm(`Confirm shot ${shot.id}?\nThis will create folder structures and lock the shot.`)) {
            return;
        }

        handleCellUpdate(shot.id, "status", "confirmed");

        try {
            await shotApi.confirm(shot.id);
            alert(`Shot ${shot.id.split('-').pop()} Confirmed!\nFolders created.`);
        } catch (err) {
            console.error("Confirm failed", err);
            handleCellUpdate(shot.id, "status", "pending");
            alert("Failed to confirm shot: " + (err.response?.data?.detail || err.message));
        }
    };

    const handleSubjectClick = (shotId) => {
        setActiveShotId(shotId);
        setShowSubjectSelector(true);
    };

    const handleSubjectSave = async (newSubjects) => {
        if (!activeShotId) return;
        setShots(prev => prev.map(s => {
            if (s.id === activeShotId) {
                const updatedSubjects = [...(s.subjects || []), ...newSubjects];
                return { ...s, subjects: updatedSubjects };
            }
            return s;
        }));
        try {
            const shot = shots.find(s => s.id === activeShotId);
            if (shot) {
                const updatedSubjects = [...(shot.subjects || []), ...newSubjects];
                await shotApi.update(activeShotId, { subjects: updatedSubjects });
            }
        } catch (err) {
            console.error("Subject update failed", err);
        }
    };

    const handleCinematicClick = (shotId) => {
        setActiveShotId(shotId);
        setShowCinematicSelector(true);
    };

    const handleCinematicSave = async (updates) => {
        if (!activeShotId) return;
        setShots(prev => prev.map(s => {
            if (s.id === activeShotId) {
                return { ...s, ...updates };
            }
            return s;
        }));
        try {
            await shotApi.update(activeShotId, updates);
        } catch (err) {
            console.error("Cinematic update failed", err);
        }
    };

    const handleEnvironmentClick = (shotId) => {
        setActiveShotId(shotId);
        setShowEnvironmentSelector(true);
    };

    const handleEnvironmentSave = async (updates) => {
        if (!activeShotId) return;
        setShots(prev => prev.map(s => {
            if (s.id === activeShotId) {
                return { ...s, environment: { ...s.environment, ...updates.environment } };
            }
            return s;
        }));
        try {
            await shotApi.update(activeShotId, updates);
        } catch (err) {
            console.error("Environment update failed", err);
        }
    };

    const handleGenerate = async (shot) => {
        if (!projectId) return;

        // Optimistic UI update
        handleCellUpdate(shot.id, 'status', 'queued');

        try {
            // Construct Job Payload
            const jobData = {
                project_id: projectId,
                shot_id: shot.id,
                workflow_type: shot.workflow_type || "text_to_image",
                params: {
                    // Core Prompt
                    scene_description: shot.scene_description,
                    action: shot.action,
                    dialogue: shot.dialogue,

                    // Technical / Cinematic
                    camera: shot.technical?.camera,
                    film_stock: shot.technical?.film_stock,
                    lens: shot.technical?.lens,
                    lighting: shot.technical?.lighting,
                    aspect_ratio: shot.technical?.aspect_ratio,

                    // Environment
                    location: shot.environment?.location,
                    time_of_day: shot.environment?.time_of_day,
                    weather: shot.environment?.weather,

                    // Generation Control
                    seed: shot.seed,
                    duration: shot.duration_seconds || 2.0,
                    frame_count: shot.frame_count || 48
                }
            };

            console.log("Submitting Job:", jobData);
            await jobApi.create(jobData);

            // Note: Use a global toast or status indicator in real app
        } catch (err) {
            console.error("Job creation failed", err);
            handleCellUpdate(shot.id, 'status', 'failed');
            alert("Failed to start job: " + (err.response?.data?.detail || err.message));
        }
    };

    const handleExport = async () => {
        if (!projectId) return;
        try {
            const response = await shotApi.export();
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${projectId}_shots.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error("Export failed", err);
            alert("Failed to export Excel file.");
        }
    };

    const handleImportComplete = (result) => {
        alert(`Import Successful!\nCreated: ${result.created}\nUpdated: ${result.updated}`);
        fetchData();
    };

    return (
        <div className="flex flex-col h-full bg-[#141414] text-white">
            {/* Header Toolbar */}
            <div className="h-14 border-b border-white/10 flex items-center justify-between px-4 bg-[#141414]">
                <div className="flex items-center gap-4">
                    <h2 className="text-sm font-bold tracking-wide text-gray-200">SHOT LIST</h2>
                    <div className="h-4 w-px bg-white/10"></div>
                    {/* View Toggles */}
                    <div className="flex bg-[#1a1b1e] rounded p-1">
                        <button
                            onClick={() => setViewMode('list')}
                            className={`p-1.5 rounded transition-colors ${viewMode === 'list' ? 'bg-white/10 text-white' : 'text-gray-500 hover:text-white'}`}
                        >
                            <ListIcon size={14} />
                        </button>
                        <button
                            onClick={() => setViewMode('gallery')}
                            className={`p-1.5 rounded transition-colors ${viewMode === 'gallery' ? 'bg-white/10 text-white' : 'text-gray-500 hover:text-white'}`}
                        >
                            <LayoutGrid size={14} />
                        </button>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {/* Bulk Actions */}
                    {selectedIds.size > 0 && (
                        <div className="flex items-center gap-2 mr-4 bg-blue-500/10 px-3 py-1.5 rounded border border-blue-500/20 animate-in fade-in">
                            <span className="text-xs text-blue-400 font-bold">{selectedIds.size} selected</span>
                            <button onClick={handleBulkUpdate} className="text-xs hover:underline text-blue-300 ml-2">Edit All</button>
                        </div>
                    )}

                    <button
                        onClick={() => setShowImportModal(true)}
                        className="flex items-center gap-2 px-3 py-1.5 bg-[#1a1b1e] hover:bg-[#25262b] rounded text-xs font-bold transition-colors border border-white/10"
                    >
                        <Upload size={14} /> Import Excel
                    </button>
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 px-3 py-1.5 bg-[#1a1b1e] hover:bg-[#25262b] rounded text-xs font-bold transition-colors border border-white/10"
                    >
                        <Download size={14} /> Export
                    </button>
                    <button
                        onClick={handleCreateShot}
                        className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-xs font-bold transition-colors shadow-lg shadow-blue-900/20"
                    >
                        <Plus size={14} /> New Shot
                    </button>
                </div>
            </div>

            {/* List Header */}
            {viewMode === 'list' && (
                <div className="grid grid-cols-[40px_60px_2fr_1.5fr_1.5fr_1fr_60px_1fr] gap-0 bg-[#000] border-b border-white/10 text-xs font-bold text-gray-400 sticky top-0 z-10">
                    <div className="p-3 flex items-center justify-center">
                        <input type="checkbox" checked={shots.length > 0 && selectedIds.size === shots.length} onChange={toggleSelectAll} className="accent-blue-500" />
                    </div>
                    <div className="p-3 border-r border-white/5">ID</div>
                    <div className="p-3 border-r border-white/5">Scene Description</div>
                    <div className="p-3 border-r border-white/5 flex items-center gap-2"><Users size={12} /> Subjects</div>
                    <div className="p-3 border-r border-white/5 flex items-center gap-2"><MapPin size={12} /> Env</div>
                    <div className="p-3 border-r border-white/5 flex items-center gap-2"><Camera size={12} /> Tags</div>
                    <div className="p-3 border-r border-white/5">Dur</div>
                    <div className="p-3">Workflow</div>
                </div>
            )}

            {/* Table/Gallery Body */}
            <div className="flex-1 overflow-y-auto custom-scrollbar bg-[#141414]">
                {viewMode === 'list' ? (
                    // LIST VIEW
                    shots.map(shot => (
                        <div
                            draggable
                            onDragStart={(e) => handleDragStart(e, shot)}
                            onDragOver={(e) => handleDragOver(e, shot.id)}
                            onDrop={(e) => handleDrop(e, shot)}
                            onDragEnd={handleDragEnd}
                            key={shot.id}
                            className={`grid grid-cols-[40px_60px_2fr_1.5fr_1.5fr_1fr_60px_1fr] gap-0 border-b border-white/5 hover:bg-white/[0.02] transition-colors group ${selectedIds.has(shot.id) ? 'bg-blue-900/10' : ''} ${dragOverId === shot.id ? 'border-t-2 border-blue-500' : ''}`}
                        >
                            {/* Checkbox & Drag Handle */}
                            <div className="p-3 flex items-center justify-center cursor-grab active:cursor-grabbing">
                                <input
                                    type="checkbox"
                                    checked={selectedIds.has(shot.id)}
                                    onChange={() => toggleSelect(shot.id)}
                                    className="accent-blue-500 opacity-50 group-hover:opacity-100 transition-opacity"
                                />
                            </div>

                            {/* ID & Confirm Status */}
                            <div className="p-3 border-r border-white/5 text-xs text-gray-500 font-mono truncate flex items-center gap-2">
                                <span>{shot.id.split('-').pop()}</span>
                                {shot.status === 'confirmed' && (
                                    <Lock size={10} className="text-amber-500" title="Confirmed Shot" />
                                )}
                            </div>

                            {/* Description (Editable) */}
                            <div className="p-3 border-r border-white/5 text-sm p-0">
                                <input
                                    className="w-full h-full bg-transparent p-3 outline-none focus:bg-white/5 transition-colors text-gray-300 placeholder-gray-700"
                                    value={shot.scene_description}
                                    onChange={(e) => handleCellUpdate(shot.id, 'scene_description', e.target.value)}
                                    placeholder="Describe the scene..."
                                    disabled={shot.status === 'confirmed'}
                                />
                            </div>

                            {/* Subjects (Complex Cell) */}
                            <div
                                className="p-3 border-r border-white/5 text-xs relative group/cell cursor-pointer hover:bg-white/5 transition-colors"
                                onClick={() => shot.status !== 'confirmed' && handleSubjectClick(shot.id)}
                            >
                                {shot.subjects?.length > 0 ? (
                                    <div className="flex flex-wrap gap-1">
                                        {shot.subjects.map((sub, i) => (
                                            <span key={i} className="px-1.5 py-0.5 bg-purple-500/20 text-purple-300 rounded border border-purple-500/30">
                                                {sub.character_id}
                                            </span>
                                        ))}
                                    </div>
                                ) : (
                                    <span className="text-gray-700 italic group-hover/cell:text-gray-500">No subjects</span>
                                )}
                            </div>

                            {/* Env (Complex Cell) */}
                            <div
                                className="p-3 border-r border-white/5 text-xs relative group/cell cursor-pointer hover:bg-white/5 transition-colors"
                                onClick={() => shot.status !== 'confirmed' && handleEnvironmentClick(shot.id)}
                            >
                                <div className="truncate text-gray-400">
                                    {shot.environment?.location || <span className="text-gray-700 italic">Set location...</span>}
                                </div>
                            </div>

                            {/* Tags (Formerly Tech) */}
                            <div
                                className="p-3 border-r border-white/5 text-xs relative group/cell cursor-pointer hover:bg-white/5 transition-colors"
                                onClick={() => shot.status !== 'confirmed' && handleCinematicClick(shot.id)}
                            >
                                <div className="flex flex-wrap gap-1">
                                    {shot.technical?.camera && (
                                        <span className="px-1.5 py-0.5 bg-blue-500/10 text-blue-300 rounded border border-blue-500/20 text-[10px]">
                                            {shot.technical.camera}
                                        </span>
                                    )}
                                    {shot.technical?.lens && (
                                        <span className="px-1.5 py-0.5 bg-cyan-500/10 text-cyan-300 rounded border border-cyan-500/20 text-[10px]">
                                            {shot.technical.lens}
                                        </span>
                                    )}
                                    {!shot.technical?.camera && !shot.technical?.lens && (
                                        <span className="text-gray-700 italic group-hover/cell:text-gray-500">add tags...</span>
                                    )}
                                </div>
                            </div>

                            {/* Duration */}
                            <div className="p-3 border-r border-white/5 text-xs text-center text-gray-500">
                                {shot.duration_seconds}s
                            </div>

                            {/* Workflow/Status */}
                            <div className="p-3 text-xs flex items-center justify-between gap-2">
                                <div className="relative group/status flex-1">
                                    <select
                                        value={shot.status}
                                        onChange={(e) => handleCellUpdate(shot.id, 'status', e.target.value)}
                                        className={`w-full appearance-none bg-transparent pl-2 pr-6 py-0.5 rounded-full capitalize cursor-pointer focus:outline-none focus:ring-1 focus:ring-white/20 ${shot.status === 'confirmed' ? 'bg-amber-500/20 text-amber-500 font-bold border border-amber-500/30' :
                                            shot.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                                                shot.status === 'queued' ? 'bg-blue-500/20 text-blue-400' :
                                                    shot.status === 'running' ? 'bg-amber-500/20 text-amber-400' :
                                                        shot.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                                                            'bg-gray-800 text-gray-400'
                                            }`}
                                        disabled={shot.status === 'confirmed'} // Cannot change status manually after confirm
                                    >
                                        <option value="pending" className="bg-[#1a1b1e] text-gray-400">Pending</option>
                                        <option value="ready" className="bg-[#1a1b1e] text-blue-400">Ready</option>
                                        <option value="queued" className="bg-[#1a1b1e] text-blue-400">Queued</option>
                                        <option value="running" className="bg-[#1a1b1e] text-amber-400">Running</option>
                                        <option value="completed" className="bg-[#1a1b1e] text-green-400">Completed</option>
                                        <option value="failed" className="bg-[#1a1b1e] text-red-400">Failed</option>
                                        <option value="confirmed" className="bg-[#1a1b1e] text-amber-500" disabled>Confirmed</option>
                                    </select>
                                    <ChevronDown size={10} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none opacity-50" />
                                </div>

                                {/* Action Buttons */}
                                <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                                    {shot.status !== 'confirmed' ? (
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handleConfirmShot(shot); }}
                                            className="p-1 hover:bg-amber-500/20 text-amber-500 rounded mr-1"
                                            title="Confirm Shot (Lock & Create Folders)"
                                        >
                                            <Lock size={14} />
                                        </button>
                                    ) : (
                                        <button
                                            className="p-1 text-gray-600 cursor-not-allowed"
                                            title="Shot is locked"
                                        >
                                            <Lock size={14} />
                                        </button>
                                    )}

                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleGenerate(shot); }}
                                        className="p-1 hover:bg-green-500/20 text-green-400 rounded mr-1"
                                        title="Generate Shot"
                                        disabled={shot.status === 'confirmed'}
                                    >
                                        <Play size={14} fill="currentColor" />
                                    </button>

                                    <button
                                        className="p-1 hover:bg-white/10 rounded text-gray-500 hover:text-white"
                                        title="Open Folder"
                                        onClick={async (e) => {
                                            e.stopPropagation();
                                            try { await shotApi.openFolder(shot.id); }
                                            catch (err) { alert("Failed to open folder: " + err.message); }
                                        }}
                                    >
                                        <FolderOpen size={14} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))
                ) : (
                    // GALLERY VIEW
                    <div className="p-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                        {shots.map(shot => (
                            <div
                                key={shot.id}
                                className={`bg-[#1a1b1e] border border-white/5 rounded-lg overflow-hidden group hover:border-white/20 transition-all ${selectedIds.has(shot.id) ? 'ring-2 ring-blue-500' : ''}`}
                                onClick={() => toggleSelect(shot.id)}
                            >
                                {/* Card Header */}
                                <div className="p-3 flex items-center justify-between border-b border-white/5 bg-black/20">
                                    <span className="font-mono text-xs text-white/50">{shot.id.split('-').pop()}</span>
                                    <span className={`w-2 h-2 rounded-full ${shot.status === 'completed' ? 'bg-green-500' :
                                        shot.status === 'running' ? 'bg-amber-500' :
                                            'bg-white/20'
                                        }`}></span>
                                </div>

                                {/* Card Body (Thumbnail Placeholder) */}
                                <div className="aspect-video bg-black flex items-center justify-center relative group/img">
                                    <span className="text-white/10 text-xs">No Preview</span>
                                    {/* Play Button Overlay */}
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleGenerate(shot); }}
                                        className="absolute inset-0 m-auto w-10 h-10 bg-white/10 rounded-full flex items-center justify-center text-white opacity-0 group-hover/img:opacity-100 hover:bg-green-600 hover:scale-110 transition-all"
                                    >
                                        <Play size={20} fill="currentColor" />
                                    </button>
                                </div>

                                {/* Card Footer */}
                                <div className="p-3 space-y-2">
                                    <p className="text-xs text-gray-400 line-clamp-2 min-h-[2.5em]">
                                        {shot.scene_description || "No description"}
                                    </p>
                                    <div className="flex gap-2 justify-between items-center mt-2 pt-2 border-t border-white/5">
                                        <div
                                            onClick={(e) => { e.stopPropagation(); handleCinematicClick(shot.id); }}
                                            className="px-2 py-1 bg-white/5 rounded text-[10px] text-gray-500 truncate cursor-pointer hover:bg-white/10 flex-1"
                                        >
                                            {shot.technical?.camera || "Cam"}
                                        </div>
                                        <button
                                            className="text-gray-600 hover:text-gray-400 transition"
                                            onClick={async (e) => {
                                                e.stopPropagation();
                                                try { await shotApi.openFolder(shot.id); }
                                                catch (err) { alert("Failed to open folder: " + err.message); }
                                            }}
                                        >
                                            <FolderOpen size={12} />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
            {/* Subject Selector Modal */}
            {showSubjectSelector && (
                <SubjectSelector
                    shotId={activeShotId}
                    currentSubjects={shots.find(s => s.id === activeShotId)?.subjects || []}
                    onSave={handleSubjectSave}
                    onClose={() => setShowSubjectSelector(false)}
                />
            )}
            {showCinematicSelector && (
                <CinematicSelector
                    shotId={activeShotId}
                    onSave={handleCinematicSave}
                    onClose={() => setShowCinematicSelector(false)}
                />
            )}
            {showEnvironmentSelector && (
                <EnvironmentSelector
                    shotId={activeShotId}
                    initialEnv={shots.find(s => s.id === activeShotId)?.environment}
                    onSave={handleEnvironmentSave}
                    onClose={() => setShowEnvironmentSelector(false)}
                />
            )}
            {showImportModal && (
                <ExcelImportModal
                    projectId={projectId}
                    onClose={() => setShowImportModal(false)}
                    onImportComplete={handleImportComplete}
                />
            )}

            {/* Kitsu-style Comments Drawer */}
            {showCommentsPanel && activeShotForComments && (
                <div className="fixed inset-y-0 right-0 w-[400px] bg-[#1a1b1e] border-l border-white/10 shadow-2xl z-50 flex flex-col animate-in slide-in-from-right duration-300">
                    <div className="h-14 border-b border-white/10 flex items-center justify-between px-6 bg-[#202025]">
                        <div>
                            <h3 className="text-sm font-bold text-white tracking-wide">
                                {activeShotForComments.id.split('-').pop()} - Review
                            </h3>
                            <span className="text-xs text-white/40">Activity Log</span>
                        </div>
                        <button onClick={() => setShowCommentsPanel(false)} className="text-white/30 hover:text-white transition">
                            <X size={20} />
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6 space-y-6">
                        {/* Dummy History Items */}
                        <div className="flex gap-3">
                            <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold border border-blue-500/30">JS</div>
                            <div className="flex-1">
                                <div className="flex items-baseline gap-2 mb-1">
                                    <span className="text-sm font-bold text-gray-200">John Smith</span>
                                    <span className="text-[10px] text-gray-500">2 hours ago</span>
                                </div>
                                <p className="text-xs text-gray-400 leading-relaxed bg-white/5 p-3 rounded-lg border border-white/5">
                                    Motion blur on the background looks a bit excessive. Can we reduce it by 20%?
                                    <span className="block mt-2 text-amber-500 text-[10px] font-mono border-t border-white/5 pt-2">
                                        Status changed: Pending → Needs Revision
                                    </span>
                                </p>
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center text-green-400 text-xs font-bold border border-green-500/30">AI</div>
                            <div className="flex-1">
                                <div className="flex items-baseline gap-2 mb-1">
                                    <span className="text-sm font-bold text-gray-200">System</span>
                                    <span className="text-[10px] text-gray-500">Yesterday</span>
                                </div>
                                <p className="text-xs text-gray-400 leading-relaxed">
                                    Shot created via Excel Import.
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="p-4 border-t border-white/10 bg-[#25262b]">
                        <div className="relative">
                            <textarea
                                className="w-full bg-[#141414] border border-white/10 rounded-lg p-3 text-sm text-white placeholder-white/20 outline-none focus:border-blue-500/50 transition-colors resize-none pr-10"
                                placeholder="Write a comment..."
                                rows={3}
                            />
                            <button className="absolute right-3 bottom-3 p-1.5 bg-blue-600 hover:bg-blue-500 rounded text-white transition-colors">
                                <Send size={14} />
                            </button>
                        </div>
                        <div className="flex justify-between items-center mt-2 px-1">
                            <span className="text-[10px] text-gray-500">Markdown supported</span>
                            <div className="flex gap-2">
                                <button className="text-[10px] px-2 py-1 bg-white/5 hover:bg-white/10 rounded text-gray-400 border border-white/5">
                                    Set Status
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ShotTable;
