import axios from 'axios';

// In production build (served from FastAPI), use same-origin (empty string).
// In Vite dev mode, VITE_API_BASE_URL defaults to the local master server.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? '' : 'http://127.0.0.1:8002');

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const projectApi = {
    list: () => api.get('/projects/'),
    create: (id, description) => api.post('/projects/', { project_id: id, description }),
    load: (id) => api.post(`/projects/${id}/load`),
    uploadThumbnail: (id, formData) => api.post(`/projects/${id}/thumbnail`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),
    exportEdl: (id) => api.get(`/projects/${id}/export/edl`, { responseType: 'blob' }),
    archive: (id) => api.get(`/projects/${id}/archive`, { responseType: 'blob' }),
    compose: (id, transition = 'fade', transitionDuration = 0.5) =>
        api.post(`/projects/${id}/compose`, { transition, transition_duration: transitionDuration }),
    downloadComposed: (id) => api.get(`/projects/${id}/compose/download`, { responseType: 'blob' }),
};

export const shotApi = {
    list: () => api.get('/shots/'),
    // Legacy create (client-side ID)
    create: (shot) => api.post('/shots/', shot),
    // NEW: Server-side ID generation (recommended)
    createWithServerId: (data = {}) => api.post('/shots/create', data),
    update: (id, updates) => api.put(`/shots/${id}`, updates),
    reorder: (ids) => api.post('/shots/reorder', ids),
    export: () => api.get('/shots/export', { responseType: 'blob' }),
    import: (formData) => api.post('/shots/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),
    bulkUpdate: (ids, updates) => api.post('/shots/bulk_update', { ids, updates }),
    openFolder: (id) => api.post(`/shots/${id}/open_folder`),
    // NEW: Confirm shot (locks folder structure)
    confirm: (id) => api.post(`/shots/${id}/confirm`),
    // NEW: Generate shots from script using LLM
    generateFromScript: (data) => api.post('/shots/generate-from-script', data),
    // NEW: List available LLM providers
    listProviders: () => api.get('/shots/llm-providers'),
};

export const cinematicApi = {
    listPresets: () => api.get('/cinematics/presets'),
    getPreset: (id) => api.get(`/cinematics/presets/${id}`),
    scan: () => api.post('/cinematics/scan'),
};

export const jobApi = {
    list: (projectId) => api.get(`/jobs/?project_id=${projectId || ''}`),
    create: (jobData) => api.post('/jobs/', jobData),
    get: (jobId) => api.get(`/jobs/${jobId}`),
};

export const characterApi = {
    list: () => api.get('/characters/'),
    create: (char) => api.post('/characters/', char),
    update: (id, updates) => api.put(`/characters/${id}`, updates),
    delete: (id) => api.delete(`/characters/${id}`),
    uploadThumbnail: (id, formData) => api.post(`/characters/${id}/thumbnail`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    })
};

export const workerApi = {
    list: () => api.get('/workers/'),
    register: (worker) => api.post('/workers/register', worker),
    heartbeat: (id) => api.post(`/workers/${id}/heartbeat`),
    delete: (id) => api.delete(`/workers/${id}`),
};

export const cpeApi = {
    health: () => api.get('/api/cpe/health'),
    validate: (config) => api.post('/api/cpe/validate', config),
    generatePrompt: (config) => api.post('/api/cpe/generate-prompt', config),
    listPresets: () => api.get('/api/cpe/presets'),
    getPreset: (id) => api.get(`/api/cpe/presets/${id}`),
    applyPreset: (data) => api.post('/api/cpe/apply-preset', data),
    listEnums: () => api.get('/api/cpe/enums'),
    getEnum: (name) => api.get(`/api/cpe/enums/${name}`),
    ruleCount: () => api.get('/api/cpe/rules/count'),
};




export default api;
