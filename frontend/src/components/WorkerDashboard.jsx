import React, { useState, useEffect } from 'react';
import { workerApi } from '../lib/api';
import { Server, Cpu, Activity, AlertCircle, RefreshCw } from 'lucide-react';

const WorkerDashboard = () => {
    const [workers, setWorkers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState(null);

    const fetchWorkers = async () => {
        try {
            const res = await workerApi.list();
            setWorkers(res.data);
            setLastUpdated(new Date());
            setLoading(false);
        } catch (err) {
            console.error("Failed to fetch workers:", err);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchWorkers();
        const interval = setInterval(fetchWorkers, 5000); // 5s refresh
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status) => {
        switch (status) {
            case 'idle': return 'bg-green-500';
            case 'busy': return 'bg-amber-500';
            case 'offline': return 'bg-gray-500';
            case 'error': return 'bg-red-500';
            default: return 'bg-gray-500';
        }
    };

    return (
        <div className="h-full flex flex-col bg-[#141414] text-white p-6 overflow-y-auto">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight mb-2">Render Farm Status</h1>
                    <p className="text-gray-400 text-sm">Real-time monitoring of distributed workers</p>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-xs text-gray-500 font-mono">
                        Last synced: {lastUpdated?.toLocaleTimeString() || '-'}
                    </span>
                    <button
                        onClick={fetchWorkers}
                        className="p-2 bg-white/5 hover:bg-white/10 rounded transition-colors"
                    >
                        <RefreshCw size={16} />
                    </button>
                </div>
            </div>

            {loading && workers.length === 0 ? (
                <div className="text-center py-20 text-gray-500">Connecting to Master Server...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {workers.map(worker => (
                        <div key={worker.id} className="bg-[#1a1b1e] border border-white/5 rounded-xl p-5 shadow-lg relative overflow-hidden group">
                            {/* Status Indicator Bar */}
                            <div className={`absolute top-0 left-0 w-full h-1 ${getStatusColor(worker.status)}`}></div>

                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${worker.status === 'offline' ? 'bg-white/5 text-gray-500' : 'bg-blue-500/10 text-blue-400'}`}>
                                        <Server size={20} />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-sm">{worker.hostname}</h3>
                                        <span className={`text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded ${getStatusColor(worker.status)}/20 ${getStatusColor(worker.status).replace('bg-', 'text-')}`}>
                                            {worker.status}
                                        </span>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <span className="block text-xs text-gray-500 font-mono">{worker.ip_address}</span>
                                </div>
                            </div>

                            <div className="space-y-4">
                                {/* GPU Info - Safe access to gpus array */}
                                {(() => {
                                    const gpu = worker.gpus?.[0] || {};
                                    const gpuName = gpu.name || 'Unknown GPU';
                                    const gpuUtil = gpu.utilization || 0;
                                    const vramUsed = (gpu.memory_used || 0) / 1024; // MB to GB
                                    const vramTotal = (gpu.memory_total || 1) / 1024; // MB to GB

                                    return (
                                        <>
                                            <div>
                                                <div className="flex justify-between text-xs text-gray-400 mb-1">
                                                    <span>GPU: {gpuName}</span>
                                                    <span>{gpuUtil}% Load</span>
                                                </div>
                                                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-blue-500 transition-all duration-500"
                                                        style={{ width: `${gpuUtil}%` }}
                                                    ></div>
                                                </div>
                                            </div>

                                            <div>
                                                <div className="flex justify-between text-xs text-gray-400 mb-1">
                                                    <span>VRAM</span>
                                                    <span>{vramUsed.toFixed(1)} / {vramTotal.toFixed(1)} GB</span>
                                                </div>
                                                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-purple-500 transition-all duration-500"
                                                        style={{ width: `${vramTotal > 0 ? (vramUsed / vramTotal) * 100 : 0}%` }}
                                                    ></div>
                                                </div>
                                            </div>
                                        </>
                                    );
                                })()}
                            </div>

                            {/* Job Info */}
                            {worker.current_job_id && (
                                <div className="mt-4 pt-4 border-t border-white/5 mx-[-20px] px-[20px] bg-white/[0.02]">
                                    <div className="flex items-center gap-2 text-amber-500 mb-1">
                                        <Activity size={12} />
                                        <span className="text-xs font-bold">Processing Job</span>
                                    </div>
                                    <p className="text-xs text-gray-400 font-mono truncate">
                                        {worker.current_job_id}
                                    </p>
                                </div>
                            )}

                            {worker.status === 'offline' && (
                                <div className="mt-4 pt-4 border-t border-white/5 text-center">
                                    <span className="text-xs text-gray-600 flex items-center justify-center gap-1">
                                        <AlertCircle size={12} /> Last seen: {new Date(worker.last_heartbeat).toLocaleTimeString()}
                                    </span>
                                </div>
                            )}
                        </div>
                    ))}

                    {workers.length === 0 && (
                        <div className="col-span-full text-center py-20 border-2 border-dashed border-white/5 rounded-xl">
                            <Server size={48} className="mx-auto text-gray-600 mb-4" />
                            <h3 className="text-lg font-bold text-gray-400">No Active Workers</h3>
                            <p className="text-gray-500 text-sm mt-2">Start a worker node with <code>python worker/agent.py</code></p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default WorkerDashboard;
