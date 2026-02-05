import React, { useState, useEffect } from 'react';
import { Reorder, motion } from 'framer-motion';
import { shotApi } from '../lib/api';
import { Play, Pause, Save, Clock, GripVertical } from 'lucide-react';

const Timeline = ({ projectId }) => {
    const [items, setItems] = useState([]);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentFrame, setCurrentFrame] = useState(0); // Index of playing shot
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadShots();
    }, [projectId]);

    const loadShots = async () => {
        try {
            const res = await shotApi.list();
            // Ensure shots are sorted by their current order if backend returned them sorted
            setItems(res.data);
            setLoading(false);
        } catch (err) {
            console.error("Failed to load shots", err);
            setLoading(false);
        }
    };

    const handleReorder = (newOrder) => {
        setItems(newOrder);
    };

    const saveOrder = async () => {
        const ids = items.map(item => item.id);
        try {
            await shotApi.reorder(ids);
            alert("Timeline saved!");
        } catch (err) {
            alert("Failed to save order: " + err.message);
        }
    };

    // Playback Logic
    useEffect(() => {
        let interval;
        if (isPlaying) {
            interval = setInterval(() => {
                setCurrentFrame((prev) => {
                    const next = prev + 1;
                    if (next >= items.length) {
                        setIsPlaying(false);
                        return 0;
                    }
                    return next;
                });
            }, 1000); // 1 sec per shot (simple preview)
        }
        return () => clearInterval(interval);
    }, [isPlaying, items.length]);

    const currentShot = items[currentFrame];

    return (
        <div className="flex flex-col h-full bg-[#141414] text-white overflow-hidden">
            {/* Player / Preview Area */}
            <div className="flex-1 bg-black flex items-center justify-center relative border-b border-white/10 p-4">
                {currentShot ? (
                    <div className="relative aspect-video h-full max-h-[60vh] bg-[#222] rounded flex items-center justify-center overflow-hidden">
                        {currentShot.generated_video_path ? (
                            <video src={currentShot.generated_video_path} controls autoPlay className="w-full h-full object-contain" />
                        ) : currentShot.generated_image_path ? (
                            <img src={currentShot.generated_image_path} alt={currentShot.id} className="w-full h-full object-contain" />
                        ) : (
                            <div className="text-center p-10">
                                <h3 className="text-2xl font-bold text-white/20 mb-2">{currentShot.id}</h3>
                                <p className="text-white/40 text-sm">{currentShot.scene_description || "No content"}</p>
                            </div>
                        )}
                        {/* Overlay Info */}
                        <div className="absolute bottom-4 left-4 bg-black/50 backdrop-blur px-3 py-1 rounded text-xs">
                            {currentFrame + 1} / {items.length} : {currentShot.id}
                        </div>
                    </div>
                ) : (
                    <div className="text-white/20">Empty Timeline</div>
                )}
            </div>

            {/* Timeline Controls */}
            <div className="h-12 bg-[#1a1b1e] border-b border-white/5 flex items-center px-4 justify-between">
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setIsPlaying(!isPlaying)}
                        className={`p-2 rounded-full ${isPlaying ? 'bg-yellow-500 text-black' : 'bg-white/10 hover:bg-white/20'}`}
                    >
                        {isPlaying ? <Pause size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
                    </button>
                    <span className="text-xs text-gray-400 font-mono ml-2">
                        {currentFrame + 1} / {items.length}
                    </span>
                </div>
                <button
                    onClick={saveOrder}
                    className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-xs rounded font-medium transition-colors"
                >
                    <Save size={14} /> Save Order
                </button>
            </div>

            {/* Draggable Track */}
            <div className="h-48 overflow-x-auto overflow-y-hidden p-4 bg-[#111]">
                <Reorder.Group
                    axis="x"
                    values={items}
                    onReorder={handleReorder}
                    className="flex gap-2 h-full items-center"
                >
                    {items.map((item, index) => (
                        <Reorder.Item
                            key={item.id}
                            value={item}
                            className={`flex-shrink-0 w-48 h-32 bg-[#222] rounded border border-white/10 cursor-grab active:cursor-grabbing relative group overflow-hidden ${index === currentFrame ? 'ring-2 ring-yellow-500' : ''}`}
                            onClick={() => setCurrentFrame(index)}
                        >
                            {/* Reorder Handle */}
                            <div className="absolute top-1 right-1 p-1 bg-black/40 rounded opacity-0 group-hover:opacity-100 transition-opacity z-10">
                                <GripVertical size={12} />
                            </div>

                            {/* Content */}
                            <div className="w-full h-full flex flex-col">
                                <div className="flex-1 bg-black/20 flex items-center justify-center relative">
                                    {item.generated_image_path ? (
                                        <img src={item.generated_image_path} className="w-full h-full object-cover opacity-70" />
                                    ) : (
                                        <span className="text-white/10 text-xs font-mono">{item.id}</span>
                                    )}
                                </div>
                                <div className="h-8 bg-[#1a1b1e] flex items-center px-2 text-[10px] text-gray-400 border-t border-white/5 truncate">
                                    <span className="mr-auto truncate">{item.scene_description}</span>
                                    <span className="flex items-center gap-1 text-white/30 ml-2">
                                        <Clock size={10} /> {item.duration_seconds}s
                                    </span>
                                </div>
                            </div>
                        </Reorder.Item>
                    ))}
                </Reorder.Group>
            </div>
        </div>
    );
};

export default Timeline;
