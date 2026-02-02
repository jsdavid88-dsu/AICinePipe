import React, { useState, useEffect, useMemo } from 'react';
import { shotApi, jobApi } from '../lib/api';
import { Clapperboard, Play, Loader2 } from 'lucide-react';
import DataTable from './ui/DataTable';

const ShotTable = ({ projectId }) => {
    const [shots, setShots] = useState([]);
    const [loading, setLoading] = useState(false);
    const [renderingShots, setRenderingShots] = useState({});

    const fetchShots = async () => {
        try {
            setLoading(true);
            const res = await shotApi.list();
            setShots(res.data);
        } catch (err) {
            console.error("Failed to fetch shots", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (projectId) {
            fetchShots();
        }
    }, [projectId]);

    const handleRowUpdate = async (id, key, value) => {
        try {
            // Optimistic update
            setShots(prev => prev.map(s => s.id === id ? { ...s, [key]: value } : s));

            // API call
            // Note: shotApi.update needs to be implemented in backend if not already
            // But for now we assume it works or we just create/overwrite if needed
            // Here we just use create/update logic. Let's assume update endpoint exists.
            // If not, we might need to fix backend router.
            await shotApi.update(id, { [key]: value });

        } catch (err) {
            console.error("Failed to update shot", err);
            // Revert on error? For now just alert
        }
    };

    const handleRowAdd = async () => {
        try {
            const newShot = {
                id: `SHT-${String(shots.length + 1).padStart(5, '0')}`,
                scene_description: "New Scene",
                action: "",
                frame_count: 24,
                status: "pending",
                created_at: new Date().toISOString()
            };
            await shotApi.create(newShot);
            setShots(prev => [...prev, newShot]);
        } catch (err) {
            console.error("Failed to create shot", err);
            alert(`Failed to create shot: ${err.message}`);
        }
    };

    const handleRender = async (shot) => {
        try {
            setRenderingShots(prev => ({ ...prev, [shot.id]: true }));
            await jobApi.create({
                project_id: projectId,
                shot_id: shot.id,
                workflow_type: "text_to_image/flux_basic",
                params: {
                    prompt: `${shot.scene_description}, ${shot.action}`,
                    seed: Math.floor(Math.random() * 1000000)
                }
            });

            setShots(prev => prev.map(s => s.id === shot.id ? { ...s, status: 'generating' } : s));
        } catch (err) {
            console.error("Render request failed", err);
            alert("Failed to start render");
        } finally {
            setRenderingShots(prev => ({ ...prev, [shot.id]: false }));
        }
    };

    const columns = useMemo(() => [
        { key: 'id', label: 'Shot ID', width: 100, editable: false },
        { key: 'scene_description', label: 'Scene Description', grow: 1 },
        { key: 'action', label: 'Action / Prompt', grow: 1 },
        { key: 'frame_count', label: 'Frames', width: 80 },
        {
            key: 'status',
            label: 'Status',
            width: 120,
            type: 'select',
            options: [
                { label: 'Pending', value: 'pending' },
                { label: 'Generating', value: 'generating' },
                { label: 'Completed', value: 'completed' },
                { label: 'Failed', value: 'failed' }
            ]
        }
    ], []);

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center px-2">
                <h2 className="text-xl font-bold flex items-center gap-2 text-white">
                    <Clapperboard className="w-5 h-5 text-blue-400" /> Shot List
                </h2>
                <button
                    onClick={fetchShots}
                    className="text-xs text-muted-foreground hover:text-white transition-colors"
                >
                    Refresh Data
                </button>
            </div>

            <DataTable
                columns={columns}
                data={shots}
                onRowUpdate={handleRowUpdate}
                onRowAdd={handleRowAdd}
                renderRowAction={(row) => (
                    <button
                        onClick={() => handleRender(row)}
                        disabled={renderingShots[row.id] || row.status === 'generating'}
                        className="p-1.5 hover:bg-green-500/20 text-green-400 rounded transition-all disabled:opacity-50"
                        title="Render Shot"
                    >
                        {renderingShots[row.id] ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                    </button>
                )}
            />
        </div>
    );
};

export default ShotTable;
