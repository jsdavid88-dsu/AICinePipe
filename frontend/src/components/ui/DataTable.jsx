import React, { useState, useEffect, useRef } from 'react';
import { Plus, MoreHorizontal, Trash2, X } from 'lucide-react';

// Cell Components
const TextCell = ({ value, onChange, onBlur, autoFocus }) => (
    <input
        type="text"
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        onKeyDown={(e) => {
            if (e.key === 'Enter') onBlur();
        }}
        autoFocus={autoFocus}
        className="w-full bg-transparent border-none outline-none px-2 py-1 text-sm h-full"
    />
);

const SelectCell = ({ value, options, onChange, onBlur, autoFocus }) => (
    <select
        value={value || ''}
        onChange={(e) => {
            onChange(e.target.value);
            onBlur();
        }}
        onBlur={onBlur}
        autoFocus={autoFocus}
        className="w-full bg-transparent border-none outline-none px-1 py-1 text-sm h-full appearance-none cursor-pointer"
    >
        <option value="" className="bg-slate-800 text-gray-400">Select...</option>
        {options.map(opt => (
            <option key={opt.value} value={opt.value} className="bg-slate-800 text-white">
                {opt.label}
            </option>
        ))}
    </select>
);

const Cell = ({ row, column, value, onUpdate }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [tempValue, setTempValue] = useState(value);

    useEffect(() => {
        setTempValue(value);
    }, [value]);

    const handleBlur = () => {
        setIsEditing(false);
        if (tempValue !== value) {
            onUpdate(row.id, column.key, tempValue);
        }
    };

    if (column.editable === false) {
        return <div className="px-3 py-2 text-sm text-gray-400 font-mono select-none">{value}</div>;
    }

    if (isEditing) {
        if (column.type === 'select') {
            return (
                <div className="h-full w-full bg-slate-800 ring-2 ring-blue-500 rounded-sm">
                    <SelectCell
                        value={tempValue}
                        options={column.options}
                        onChange={setTempValue}
                        onBlur={handleBlur}
                        autoFocus
                    />
                </div>
            );
        }
        return (
            <div className="h-full w-full bg-slate-800 ring-2 ring-blue-500 rounded-sm">
                <TextCell
                    value={tempValue}
                    onChange={setTempValue}
                    onBlur={handleBlur}
                    autoFocus
                />
            </div>
        );
    }

    // Display Mode
    let content = value;
    let className = "px-3 py-2 text-sm h-full border border-transparent hover:border-gray-600 cursor-text truncate transition-colors";

    if (column.type === 'select') {
        const option = column.options?.find(o => o.value === value);
        const label = option?.label || value;

        let badgeClass = "bg-gray-700 text-gray-300";
        if (value === 'completed') badgeClass = "bg-green-900/50 text-green-400 border border-green-800";
        if (value === 'generating') badgeClass = "bg-yellow-900/50 text-yellow-400 border border-yellow-800";
        if (value === 'pending') badgeClass = "bg-gray-700 text-gray-400";

        content = (
            <span className={`px-2 py-0.5 rounded-full text-xs ${badgeClass}`}>
                {label}
            </span>
        );
        className = "px-3 py-2 text-sm h-full cursor-pointer flex items-center";
    }

    return (
        <div
            onClick={() => setIsEditing(true)}
            className={className}
        >
            {content || <span className="text-gray-600 italic text-xs">Empty</span>}
        </div>
    );
};

const DataTable = ({ columns, data, onRowUpdate, onRowAdd, onRowDelete, renderRowAction }) => {
    return (
        <div className="border border-white/10 rounded-lg overflow-hidden bg-[#1a1b1e] text-gray-300">
            {/* Header */}
            <div className="flex border-b border-white/10 bg-[#25262b]">
                {columns.map(col => (
                    <div
                        key={col.key}
                        className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider border-r border-white/5 last:border-none shrink-0"
                        style={{ width: col.width || 150, flexGrow: col.grow ? 1 : 0 }}
                    >
                        {col.label}
                    </div>
                ))}
                {(onRowDelete || renderRowAction) && <div className="w-24 shrink-0 px-3 py-2"></div>}
            </div>

            {/* Rows */}
            <div className="divide-y divide-white/5 relative z-0">
                {data.length === 0 && (
                    <div className="p-8 text-center text-gray-500 text-sm">
                        No data available. Click "Add Record" to start.
                    </div>
                )}
                {data.map((row) => (
                    <div key={row.id} className="flex group hover:bg-white/5 transition-colors relative">
                        {columns.map(col => (
                            <div
                                key={col.key}
                                className="border-r border-white/5 last:border-none shrink-0 relative"
                                style={{ width: col.width || 150, flexGrow: col.grow ? 1 : 0 }}
                            >
                                <Cell
                                    row={row}
                                    column={col}
                                    value={row[col.key]}
                                    onUpdate={onRowUpdate}
                                />
                            </div>
                        ))}

                        {/* Actions */}
                        <div className="w-24 shrink-0 flex items-center justify-center gap-1 border-white/5">
                            {renderRowAction && renderRowAction(row)}
                            {onRowDelete && (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onRowDelete(row.id);
                                    }}
                                    className="p-1.5 text-gray-500 hover:text-red-400 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                                >
                                    <Trash2 size={14} />
                                </button>
                            )}
                        </div>
                    </div>
                ))}

                {/* Add Row Button */}
                {onRowAdd && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            console.log("Add Row Clicked");
                            onRowAdd();
                        }}
                        className="w-full py-2 flex items-center justify-start px-4 text-xs text-gray-500 hover:text-blue-400 hover:bg-blue-500/10 transition-colors gap-2 relative z-10 cursor-pointer"
                    >
                        <Plus size={14} />
                        <span>Add Record</span>
                    </button>
                )}
            </div>
        </div>
    );
};

export default DataTable;
