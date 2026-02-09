import axios from 'axios';

// 환경변수 기반 API URL (Vite 환경변수 또는 기본값)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8100';

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
    })
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




export default api;
