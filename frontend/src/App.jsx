import React, { useState, useEffect } from 'react';
import { LayoutGrid, Clapperboard, Users, Settings, Plus, Play, Server, Activity } from 'lucide-react';
import ShotTable from './components/ShotTable';
import { projectApi } from './lib/api';

const CharacterBibleView = () => (
    <div className="p-6">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
            <Users className="w-6 h-6 text-purple-400" /> Character Bible
        </h2>
        <div className="glass-panel p-8 text-center text-muted-foreground">
            Character Cards & LoRA Management (Coming Soon)
        </div>
    </div>
);

const RenderFarmView = () => (
    <div className="p-6">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
            <Server className="w-6 h-6 text-green-400" /> Render Farm Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="glass-panel p-4 border-l-4 border-green-500">
                <div className="flex justify-between items-center mb-2">
                    <span className="font-bold">Worker-01 (RTX 4090)</span>
                    <span className="px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 text-xs">IDLE</span>
                </div>
                <div className="text-sm text-muted-foreground">VRAM: 2.1 / 24.0 GB</div>
                <div className="mt-2 text-xs">Supported: FLUX, WAN, LTX-2</div>
            </div>
            <div className="glass-panel p-4 border-l-4 border-yellow-500">
                <div className="flex justify-between items-center mb-2">
                    <span className="font-bold">Worker-02 (RTX 3090)</span>
                    <span className="px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 text-xs">BUSY</span>
                </div>
                <div className="text-sm text-muted-foreground">VRAM: 22.4 / 24.0 GB</div>
                <div className="mt-2 text-xs">Generating SHT-0012 (WAN-Animate)...</div>
            </div>
        </div>
    </div>
);

function App() {
    const [activeTab, setActiveTab] = useState('shots');
    const [projectId, setProjectId] = useState('test_prj_01'); // Default test project
    const [projectLoaded, setProjectLoaded] = useState(false);

    useEffect(() => {
        // Load default project on mount
        const initProject = async () => {
            try {
                await projectApi.create(projectId); // Ensure it exists
                await projectApi.load(projectId);
                setProjectLoaded(true);
                console.log("Project loaded:", projectId);
            } catch (e) {
                console.error("Project load failed", e);
                // Try loading if create failed (maybe already exists)
                try {
                    await projectApi.load(projectId);
                    setProjectLoaded(true);
                } catch (loadErr) {
                    console.error("Retry load failed", loadErr);
                }
            }
        };
        initProject();
    }, [projectId]);

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans">
            {/* Sidebar */}
            <aside className="w-64 border-r border-white/10 bg-black/20 flex flex-col">
                <div className="p-4 border-b border-white/10">
                    <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
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
                        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:bg-white/5 hover:text-white transition-colors"
                    >
                        <Settings size={18} /> Settings
                    </button>
                </nav>

                <div className="p-4 border-t border-white/10">
                    <div className={`flex items-center gap-2 text-xs ${projectLoaded ? 'text-green-400' : 'text-yellow-400'}`}>
                        <div className={`w-2 h-2 rounded-full ${projectLoaded ? 'bg-green-500' : 'bg-yellow-500'} animate-pulse`}></div>
                        {projectLoaded ? 'Connected' : 'Connecting...'}
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
                            onChange={(e) => setProjectId(e.target.value)}
                            className="bg-transparent text-sm font-bold border-none focus:ring-0 cursor-pointer"
                        >
                            <option value="test_prj_01" className="bg-background">test_prj_01</option>
                            <option value="new_project" className="bg-background">+ New Project</option>
                        </select>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setActiveTab('shots')}
                            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-xs px-3 py-1.5 rounded-md transition-colors"
                        >
                            <Plus size={14} /> New Shot
                        </button>
                        <button className="flex items-center gap-2 bg-green-600 hover:bg-green-500 text-white text-xs px-3 py-1.5 rounded-md transition-colors">
                            <Play size={14} /> Render All
                        </button>
                    </div>
                </header>

                <div className="container mx-auto max-w-7xl p-6">
                    {activeTab === 'shots' && (
                        <div className="space-y-6">
                            {/* Shot Table */}
                            <ShotTable projectId={projectLoaded ? projectId : null} />
                        </div>
                    )}
                    {activeTab === 'characters' && <CharacterBibleView />}
                    {activeTab === 'farm' && <RenderFarmView />}
                </div>
            </main>
        </div>
    )
}

export default App
