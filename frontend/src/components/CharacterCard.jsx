import React from 'react';
import { MoreVertical, Edit2, Trash2, Image as ImageIcon } from 'lucide-react';
import { API_BASE_URL } from '../lib/api';

const CharacterCard = ({ character, onEdit, onDelete, onImageClick }) => {
    // Thumbnail Path Construction
    // Assuming backend returns absolute URL or we prepend base
    // But our API returns /projects/... which is relative to server root
    // We need to prepend API_BASE_URL
    const backendUrl = API_BASE_URL;
    const imageUrl = character.thumbnail
        ? `${backendUrl}${character.thumbnail}`
        : null;

    return (
        <div className="group relative bg-[#1a1b1e] rounded-xl overflow-hidden border border-white/5 hover:border-white/20 transition-all duration-300 hover:shadow-2xl hover:-translate-y-1">
            {/* Image Section */}
            <div
                className="h-64 w-full bg-[#111] relative overflow-hidden cursor-pointer"
                onClick={() => onImageClick(character)}
            >
                {imageUrl ? (
                    <img
                        src={imageUrl}
                        alt={character.name}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                        onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'flex'; // Show fallback
                        }}
                    />
                ) : null}

                {/* Fallback / Overlay */}
                <div className={`absolute inset-0 flex items-center justify-center bg-gradient-to-t from-black/80 to-transparent ${imageUrl ? 'hidden' : 'flex'}`}>
                    <ImageIcon className="w-12 h-12 text-gray-700" />
                </div>

                {/* Text Overlay on Image */}
                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60"></div>

                <div className="absolute bottom-0 left-0 p-4 w-full">
                    <h3 className="text-xl font-bold text-white truncate shadow-black drop-shadow-md">{character.name}</h3>
                    <p className="text-xs text-gray-300 truncate opacity-80">{character.age} • {character.gender}</p>
                </div>
            </div>

            {/* Actions (Hidden by default, shown on hover) */}
            <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                    onClick={(e) => { e.stopPropagation(); onEdit(character); }}
                    className="p-2 bg-black/50 hover:bg-black/80 text-white rounded-full backdrop-blur-md transition-colors"
                    title="Edit Details"
                >
                    <Edit2 size={14} />
                </button>
                <button
                    onClick={(e) => { e.stopPropagation(); onDelete(character.id); }}
                    className="p-2 bg-red-900/50 hover:bg-red-900/80 text-white rounded-full backdrop-blur-md transition-colors"
                    title="Delete"
                >
                    <Trash2 size={14} />
                </button>
            </div>

            {/* Content Section (Optional details) */}
            {/* <div className="p-4 space-y-2">
                <div className="text-sm text-gray-400 line-clamp-2 min-h-[2.5rem]">
                    {character.description || "No description provided."}
                </div>
            </div> */}
        </div>
    );
};

export default CharacterCard;
