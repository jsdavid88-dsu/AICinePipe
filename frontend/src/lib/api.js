import axios from 'axios';

const api = axios.create({
    baseURL: '/api', // Vite proxy setting handles this
    headers: {
        'Content-Type': 'application/json',
    },
});

export const projectApi = {
    list: () => api.get('/projects/'),
    create: (projectId) => api.post('/projects/', { project_id: projectId }),
    load: (projectId) => api.post(`/projects/${projectId}/load`),
};

export const shotApi = {
    list: () => api.get('/shots/'),
    create: (shot) => api.post('/shots/', shot),
    update: (id, updates) => api.put(`/shots/${id}`, updates),
};

export const jobApi = {
    list: (projectId) => api.get(`/jobs/?project_id=${projectId || ''}`),
    create: (jobData) => api.post('/jobs/', jobData),
    get: (jobId) => api.get(`/jobs/${jobId}`),
};

export default api;
