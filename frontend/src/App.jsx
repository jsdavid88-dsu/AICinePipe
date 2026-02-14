import React, { useState, useEffect } from 'react';
import { LayoutGrid, Clapperboard, Users, Settings, Plus, Play, Server, Activity, Camera, Film, Wand2 } from 'lucide-react';
import ShotTable from './components/ShotTable';
import CharacterBible from './components/CharacterBible';
import CinematicOptions from './components/CinematicOptions';
import WorkerDashboard from './components/WorkerDashboard';
import Timeline from './components/Timeline';
import ScriptGenerator from './components/ScriptGenerator';
import { projectApi } from './lib/api';



import ProjectSelection from './components/ProjectSelection';
import { Download } from 'lucide-react';

const SettingsView = ({ projectId }) => {
    const [composing, setComposing] = React.useState(false);
    const [composeResult, setComposeResult] = React.useState(null);
    const [transition, setTransition] = React.useState('fade');
    const [transitionDuration, setTransitionDuration] = React.useState(0.5);

    const handleDownloadEDL = () => {
        window.open(`http://127.0.0.1:8002/projects/${projectId}/export/edl`, '_blank');
    };

    const handleArchive = () => {
        if (confirm("This may take a while. Continue?")) {
            window.open(`http://127.0.0.1:8002/projects/${projectId}/archive`, '_blank');
        }
    };

    const handleCompose = async () => {
        setComposing(true);
        setComposeResult(null);
        try {
            const { data } = await projectApi.compose(projectId, transition, transitionDuration);
            setComposeResult({ success: true, ...data });
        } catch (err) {
            setComposeResult({ success: false, error: err.response?.data?.detail || err.message });
        } finally {
            setComposing(false);
        }
    };

    const handleDownloadComposed = () => {
        window.open(`http://127.0.0.1:8002/projects/${projectId}/compose/download`, '_blank');
    };

    const transitions = [
        { value: 'none', label: '✂️ Cut (None)' },
        { value: 'fade', label: '🌅 Fade' },
        { value: 'fadeblack', label: '⬛ Fade Black' },
        { value: 'fadewhite', label: '⬜ Fade White' },
        { value: 'dissolve', label: '💫 Dissolve' },
        { value: 'wipeleft', label: '👈 Wipe Left' },
        { value: 'wiperight', label: '👉 Wipe Right' },
        { value: 'slideleft', label: '⬅️ Slide Left' },
        { value: 'slideright', label: '➡️ Slide Right' },
        { value: 'circleopen', label: '⭕ Circle Open' },
        { value: 'circleclose', label: '🔴 Circle Close' },
        { value: 'pixelize', label: '🟦 Pixelize' },
    ];

    return (
        <div className="p-6 text-white">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <Settings className="w-6 h-6 text-gray-400" /> Project Settings
            </h2>

            <div className="space-y-6 max-w-2xl">
                {/* Video Composition */}
                <div className="bg-[#1a1b1e] p-6 rounded-xl border border-white/5">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        🎬 Compose Final Video
                    </h3>
                    <p className="text-sm text-gray-400 mb-4">
                        Merge all shot videos into a single final video using FFmpeg.
                    </p>

                    {/* Transition Options */}
                    <div className="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <label className="block text-xs text-gray-500 mb-1">Transition Type</label>
                            <select
                                value={transition}
                                onChange={(e) => setTransition(e.target.value)}
                                className="w-full bg-[#111] border border-white/10 rounded px-3 py-2 text-sm text-white"
                            >
                                {transitions.map(t => (
                                    <option key={t.value} value={t.value}>{t.label}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs text-gray-500 mb-1">Duration (sec)</label>
                            <input
                                type="number"
                                value={transitionDuration}
                                onChange={(e) => setTransitionDuration(parseFloat(e.target.value) || 0.5)}
                                min="0" max="3" step="0.1"
                                disabled={transition === 'none'}
                                className="w-full bg-[#111] border border-white/10 rounded px-3 py-2 text-sm text-white disabled:opacity-40"
                            />
                        </div>
                    </div>

                    <div className="flex gap-3">
                        <button
                            onClick={handleCompose}
                            disabled={composing}
                            className="px-4 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 rounded-lg flex items-center gap-2 text-sm font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {composing ? (
                                <><span className="animate-spin">⏳</span> Composing...</>
                            ) : (
                                <><Film size={16} /> Compose Video</>
                            )}
                        </button>
                        <button
                            onClick={handleDownloadComposed}
                            className="px-4 py-2.5 bg-white/10 hover:bg-white/20 rounded-lg flex items-center gap-2 text-sm font-medium transition-colors"
                        >
                            <Download size={16} /> Download Final
                        </button>
                    </div>

                    {composeResult && (
                        <div className={`mt-3 p-3 rounded-lg text-sm ${composeResult.success
                            ? 'bg-emerald-900/30 border border-emerald-500/30 text-emerald-300'
                            : 'bg-red-900/30 border border-red-500/30 text-red-300'
                            }`}>
                            {composeResult.success
                                ? `✅ Composed ${composeResult.shots_count} shots with "${composeResult.transition}" transition`
                                : `❌ ${composeResult.error}`
                            }
                        </div>
                    )}
                </div>

                {/* Publish & Delivery */}
                <div className="bg-[#1a1b1e] p-6 rounded-xl border border-white/5">
                    <h3 className="text-lg font-bold mb-4">Publish & Delivery</h3>
                    <div className="flex gap-4">
                        <button
                            onClick={handleDownloadEDL}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded flex items-center gap-2 text-sm font-medium transition-colors"
                        >
                            <Clapperboard size={16} /> Export EDL (CMX3600)
                        </button>
                        <button
                            onClick={handleArchive}
                            className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded flex items-center gap-2 text-sm font-medium transition-colors"
                        >
                            <Download size={16} /> Archive Project (.zip)
                        </button>
                    </div>
                    <p className="mt-3 text-xs text-gray-500">
                        EDL is compatible with Premiere Pro / DaVinci Resolve.
                        Archive includes all assets, shots, and renders.
                    </p>
                </div>

                <div className="bg-[#1a1b1e] p-6 rounded-xl border border-white/5 opacity-50 pointer-events-none">
                    <h3 className="text-lg font-bold mb-4">General Configuration</h3>
                    <p className="text-sm text-gray-500">Global settings coming soon.</p>
                </div>
            </div>
        </div>
    );
};

function App() {
    const [activeTab, setActiveTab] = useState('shots');
    const [projectId, setProjectId] = useState('');
    const [projectList, setProjectList] = useState([]); // Keep this for sidebar dropdown if needed
    const [projectLoaded, setProjectLoaded] = useState(false);

    // Fetch project list for dropdown (Main View)
    const fetchProjects = async () => {
        try {
            const res = await projectApi.list();
            setProjectList(res.data);
        } catch (err) {
            console.error("Failed to list projects", err);
        }
    };

    useEffect(() => {
        if (projectId) {
            fetchProjects();
        }
    }, [projectId]);

    useEffect(() => {
        if (!projectId) {
            setProjectLoaded(false);
            return;
        }

        const loadProject = async () => {
            setProjectLoaded(false);
            try {
                await projectApi.load(projectId);
                setProjectLoaded(true);
                console.log("Project loaded:", projectId);
            } catch (e) {
                console.error("Project load failed", e);
                setProjectLoaded(false);
            }
        };
        loadProject();
    }, [projectId]);

    // Handle project selection from Home Screen
    const handleSelectProject = (id) => {
        setProjectId(id);
    };

    // Handle project switch from Header
    const handleProjectChange = async (e) => {
        const val = e.target.value;
        if (val === '') {
            setProjectId(''); // Go back to selection
            return;
        }
        if (val === 'new_project') {
            const name = window.prompt("Enter new project name (ID):");
            if (name) {
                try {
                    // Simple validation
                    const safeName = name.replace(/[^a-zA-Z0-9_-]/g, '_');
                    await projectApi.create(safeName);
                    await fetchProjects();
                    setProjectId(safeName);
                    alert(`Project '${safeName}' created.`);
                } catch (err) {
                    alert("Failed to create project: " + err.message);
                }
            }
        } else {
            setProjectId(val);
        }
    };

    if (!projectId) {
        return <ProjectSelection onSelectProject={handleSelectProject} />;
    }

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans">
            {/* Sidebar */}
            <aside className="w-64 border-r border-white/10 bg-black/20 flex flex-col">
                <div className="p-4 border-b border-white/10">
                    <h1
                        className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent cursor-pointer"
                        onClick={() => setProjectId('')}
                        title="Back to Project Selection"
                    >
                        AI Pipeline
                    </h1>

                    <p className="text-xs text-muted-foreground">Production Manager</p>
                </div>

                <nav className="flex-1 p-2 space-y-1">
                    <button
                        onClick={() => setActiveTab('shots')}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${activeTab === 'shots' ? 'bg-white/10 text-white' : 'text-muted-foreground hover:bg-white/5'}`}
                    >
                        <Clapperboard size={18} /> Shots
                    </button>
                    <button
                        onClick={() => setActiveTab('characters')}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${activeTab === 'characters' ? 'bg-white/10 text-white' : 'text-muted-foreground hover:bg-white/5'}`}
                    >
                        <Users size={18} /> Characters
                    </button>
                    <button
                        onClick={() => setActiveTab('cinematics')}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${activeTab === 'cinematics' ? 'bg-white/10 text-white' : 'text-muted-foreground hover:bg-white/5'}`}
                    >
                        <Camera size={18} /> Cinematic Options
                    </button>
                    <button
                        onClick={() => setActiveTab('script')}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${activeTab === 'script' ? 'bg-white/10 text-white' : 'text-muted-foreground hover:bg-white/5'}`}
                    >
                        <Wand2 size={18} /> Script → Shots
                    </button>
                    <button
                        onClick={() => setActiveTab('timeline')}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${activeTab === 'timeline' ? 'bg-white/10 text-white' : 'text-muted-foreground hover:bg-white/5'}`}
                    >
                        <Clapperboard size={18} /> Storyboard
                    </button>
                    <button
                        onClick={() => setActiveTab('farm')}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${activeTab === 'farm' ? 'bg-white/10 text-white' : 'text-muted-foreground hover:bg-white/5'}`}
                    >
                        <Server size={18} /> Render Farm
                    </button>
                    <button
                        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:bg-white/5 hover:text-white transition-colors"
                    >
                        <Activity size={18} /> Activity
                    </button>
                    <button
                        onClick={() => setActiveTab('settings')}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${activeTab === 'settings' ? 'bg-white/10 text-white' : 'text-muted-foreground hover:bg-white/5'}`}
                    >
                        <Settings size={18} /> Settings
                    </button>
                </nav>

                <div className="p-4 border-t border-white/10">
                    <div className={`flex items-center gap-2 text-xs ${projectLoaded ? 'text-green-400' : 'text-yellow-400'}`}>
                        <div className={`w-2 h-2 rounded-full ${projectLoaded ? 'bg-green-500' : 'bg-yellow-500'} animate-pulse`}></div>
                        {projectLoaded ? `Connected: ${projectId}` : 'No Project Loaded'}
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto bg-gradient-to-br from-background to-secondary/20">
                <header className="h-14 border-b border-white/10 flex items-center justify-between px-6 bg-black/20 backdrop-blur-sm sticky top-0 z-10">
                    <div className="flex items-center gap-4">
                        <span className="text-sm font-medium text-muted-foreground">Project:</span>
                        <select
                            value={projectId}
                            onChange={handleProjectChange}
                            className="bg-transparent text-sm font-bold border-none focus:ring-0 cursor-pointer min-w-[150px] outline-none"
                        >
                            <option value="" className="bg-background text-gray-400">← Back to Home</option>
                            {projectList.map(p => (
                                <option key={p} value={p} className="bg-background">{p}</option>
                            ))}
                            <option value="new_project" className="bg-background text-blue-400 font-bold">+ New Project</option>
                        </select>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setActiveTab('shots')}
                            className={`flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-xs px-3 py-1.5 rounded-md transition-colors ${activeTab !== 'shots' ? 'hidden' : ''}`}
                        >
                            <Plus size={14} /> New Shot
                        </button>
                    </div>
                </header>

                <div className="container mx-auto max-w-7xl p-6 h-[calc(100vh-3.5rem)] overflow-auto">
                    {!projectLoaded ? (
                        <div className="flex flex-col items-center justify-center h-full text-muted-foreground animate-pulse gap-4">
                            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                            <p>Loading Project...</p>
                        </div>
                    ) : (
                        <>
                            {activeTab === 'shots' && (
                                <div className="space-y-6">
                                    <ShotTable key={projectId} projectId={projectId} />
                                </div>
                            )}
                            {activeTab === 'characters' && <CharacterBible key={projectId} projectId={projectId} />}
                            {activeTab === 'script' && <ScriptGenerator onGenerated={() => setActiveTab('shots')} />}
                            {activeTab === 'cinematics' && <CinematicOptions key={projectId} projectId={projectId} />}
                            {activeTab === 'timeline' && <Timeline key={projectId} projectId={projectId} />}
                            {activeTab === 'farm' && <WorkerDashboard />}
                            {activeTab === 'settings' && <SettingsView projectId={projectId} />}
                        </>
                    )}
                </div>
            </main>
        </div>
    )
}

export default App
