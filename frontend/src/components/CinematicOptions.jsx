import React, { useState, useEffect } from 'react';
import { Camera, RefreshCw, Download, Clapperboard, Search } from 'lucide-react';
import { cinematicApi } from '../lib/api';

const CinematicCard = ({ option }) => (
    <div className="bg-[#1a1b1e] border border-white/10 rounded-lg p-4 hover:border-blue-500/50 hover:bg-white/5 transition-all group cursor-pointer relative overflow-hidden">
        <div className="absolute top-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="bg-blue-600 text-[10px] px-2 py-0.5 rounded text-white font-bold">SELECT</div>
        </div>

        <h3 className="font-bold text-white mb-2 truncat pr-8">{option.name}</h3>

        <div className="text-xs text-gray-400 space-y-1 mb-3">
            <div className="flex justify-between">
                <span className="text-gray-600">Camera</span>
                <span className="text-gray-300">{option.camera_body || '-'}</span>
            </div>
            <div className="flex justify-between">
                <span className="text-gray-600">Lens</span>
                <span className="text-gray-300">{option.lens_type || '-'}</span>
            </div>
            {option.shot_type && (
                <div className="flex justify-between">
                    <span className="text-gray-600">Shot</span>
                    <span className="text-blue-400">{option.shot_type}</span>
                </div>
            )}
        </div>

        {/* Filters / Tags */}
        <div className="flex flex-wrap gap-1 mt-auto h-12 content-start overflow-hidden">
            {option.filters?.map((f, i) => (
                <span key={i} className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-[10px] text-gray-500 whitespace-nowrap">
                    {f}
                </span>
            ))}
        </div>
    </div>
);

const CinematicOptions = ({ projectId }) => {
    const [options, setOptions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [scanning, setScanning] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');

    const fetchData = async () => {
        if (!projectId) return;
        setLoading(true);
        try {
            const res = await cinematicApi.list();
            setOptions(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleScan = async () => {
        setScanning(true);
        try {
            const res = await cinematicApi.scan();
            alert(res.data.message); // Notify user of count
            fetchData();
        } catch (err) {
            alert("Scan failed: " + err.message);
        } finally {
            setScanning(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [projectId]);

    const filteredOptions = options.filter(o =>
        o.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (o.shot_type && o.shot_type.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    return (
        <div className="h-full flex flex-col animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Clapperboard className="w-8 h-8 text-yellow-500" /> Cinematic Options
                    </h2>
                    <p className="text-gray-400 mt-1">Configure camera, lighting, and style presets for your shots.</p>
                </div>
                <div className="flex gap-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                        <input
                            type="text"
                            placeholder="Search presets..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="bg-black/30 border border-white/10 rounded-full pl-10 pr-4 py-2 text-white focus:outline-none focus:border-yellow-500 w-64 transition-all"
                        />
                    </div>
                    <button
                        onClick={handleScan}
                        disabled={scanning}
                        className="bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-2 rounded-full font-bold flex items-center gap-2 border border-white/10 transition-all disabled:opacity-50"
                    >
                        {scanning ? <RefreshCw className="animate-spin" size={20} /> : <Download size={20} />}
                        Scan Presets
                    </button>
                    <button className="bg-yellow-600 hover:bg-yellow-500 text-black px-4 py-2 rounded-full font-bold flex items-center gap-2 shadow-lg hover:shadow-yellow-500/20 transition-all">
                        <Camera size={20} /> Create New
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                {loading ? (
                    <div className="h-64 flex items-center justify-center text-gray-500">Loading options...</div>
                ) : filteredOptions.length === 0 ? (
                    <div className="h-64 flex flex-col items-center justify-center text-gray-500 border-2 border-dashed border-white/5 rounded-xl">
                        <Clapperboard size={48} className="mb-4 opacity-50" />
                        <p>No cinematic options found.</p>
                        <p className="text-sm mt-2">Click "Scan Presets" to import from reference library.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-10">
                        {filteredOptions.map(opt => (
                            <CinematicCard key={opt.id} option={opt} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default CinematicOptions;
