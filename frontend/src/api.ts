import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

export const SettingsAPI = {
  getSettings: () => api.get('/settings/'),
  updateSettings: (configs: Record<string, any>) => api.post('/settings/', { configs }),
};

export const ProjectsAPI = {
  listProjects: () => api.get('/projects/'),
  deleteProject: (id: number) => api.delete(`/projects/${id}`),
  getVulnerabilities: (name: string) => api.get(`/projects/${name}/vulnerabilities`),
  getLogs: (name: string) => api.get(`/projects/${name}/logs`),
};

export const ScannerAPI = {
  getStatus: () => api.get('/scanner/status'),
  startScanner: (projectName: string) => api.post(`/scanner/start?project_name=${projectName}`),
  stopScanner: () => api.post('/scanner/stop'),
};

export const VulnerabilitiesAPI = {
  listAll: () => api.get('/vulnerabilities/'),
};

export default api;
