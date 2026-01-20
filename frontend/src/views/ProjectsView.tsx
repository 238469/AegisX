import React, { useState, useEffect } from 'react';
import { 
  Trash2, 
  ExternalLink, 
  Search, 
  Calendar, 
  AlertTriangle, 
  MessageSquare,
  Activity,
  History,
  ChevronRight,
  X,
  Loader2
} from 'lucide-react';
import { ProjectsAPI } from '../api';

interface Project {
  id: number;
  name: string;
  created_at: string;
  vuln_count: number;
  log_count: number;
}

interface Log {
  id: number;
  agent_name: string;
  timestamp: string;
  prompt: string;
  response: string;
}

interface Vulnerability {
  id: number;
  vuln_type: string;
  severity: string;
  parameter: string;
  payload: string;
  evidence: string;
  full_request: string;
  found_at: string;
  url: string;
  method: string;
}

const ProjectsView: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [logs, setLogs] = useState<Log[]>([]);
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [activeSubTab, setActiveSubTab] = useState<'logs' | 'vulnerabilities'>('logs');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLog, setSelectedLog] = useState<Log | null>(null);
  const [selectedVuln, setSelectedVuln] = useState<Vulnerability | null>(null);

  const filteredProjects = projects.filter(p => 
    p.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      fetchProjectDetails();
    }
  }, [selectedProject, activeSubTab]);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const response = await ProjectsAPI.listProjects();
      setProjects(response.data);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchProjectDetails = async () => {
    if (!selectedProject) return;
    setDetailsLoading(true);
    try {
      if (activeSubTab === 'logs') {
        const response = await ProjectsAPI.getLogs(selectedProject.name);
        setLogs(response.data);
      } else {
        const response = await ProjectsAPI.getVulnerabilities(selectedProject.name);
        setVulnerabilities(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch project details:', error);
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleDeleteProject = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!confirm('确定要删除该项目及其所有历史数据吗？此操作不可撤销。')) return;
    
    try {
      await ProjectsAPI.deleteProject(id);
      setProjects(prev => prev.filter(p => p.id !== id));
      if (selectedProject?.id === id) setSelectedProject(null);
    } catch (error) {
      console.error('Failed to delete project:', error);
      alert('删除失败');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-primary" size={48} />
      </div>
    );
  }

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold">项目管理</h3>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
          <input 
            type="text" 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm outline-none focus:ring-1 focus:ring-primary w-64" 
            placeholder="搜索项目..." 
          />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 flex-1 overflow-hidden">
        {/* Project List */}
        <div className="xl:col-span-1 bg-[#1e293b] rounded-xl border border-slate-700 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-700 bg-slate-800/30">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">项目列表 ({filteredProjects.length})</span>
          </div>
          <div className="flex-1 overflow-y-auto divide-y divide-slate-700">
            {filteredProjects.map(project => (
              <div 
                key={project.id}
                onClick={() => setSelectedProject(project)}
                className={`p-4 cursor-pointer transition-colors hover:bg-slate-800/50 ${selectedProject?.id === project.id ? 'bg-primary/5 border-l-4 border-primary' : ''}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-bold text-slate-200">{project.name}</h4>
                  <button 
                    onClick={(e) => handleDeleteProject(e, project.id)}
                    className="text-slate-500 hover:text-danger transition-colors p-1"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                  <div className="flex items-center gap-1">
                    <Calendar size={12} />
                    {new Date(project.created_at).toLocaleDateString()}
                  </div>
                  <div className="flex items-center gap-1 text-danger">
                    <AlertTriangle size={12} />
                    {project.vuln_count} 漏洞
                  </div>
                  <div className="flex items-center gap-1 text-primary">
                    <MessageSquare size={12} />
                    {project.log_count} 条日志
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Project Details / Logs */}
        <div className="xl:col-span-2 bg-[#1e293b] rounded-xl border border-slate-700 flex flex-col overflow-hidden">
          {selectedProject ? (
            <>
              <div className="p-6 border-b border-slate-700 flex items-center justify-between bg-slate-800/30">
                <div>
                  <h3 className="text-lg font-bold flex items-center gap-2">
                    {selectedProject.name}
                    <span className="text-xs font-normal bg-slate-700 px-2 py-0.5 rounded text-slate-400">ID: {selectedProject.id}</span>
                  </h3>
                  <p className="text-sm text-slate-400 mt-1">查看详细漏洞情况及 LLM 交互审计日志</p>
                </div>
              </div>

              <div className="flex-1 flex flex-col overflow-hidden">
                <div className="flex border-b border-slate-700 px-6">
                  <button 
                    onClick={() => setActiveSubTab('logs')}
                    className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeSubTab === 'logs' ? 'border-primary text-primary' : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    LLM Prompt 审计日志
                  </button>
                  <button 
                    onClick={() => setActiveSubTab('vulnerabilities')}
                    className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeSubTab === 'vulnerabilities' ? 'border-primary text-primary' : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    发现漏洞看板
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6">
                  {detailsLoading ? (
                    <div className="flex items-center justify-center h-32">
                      <Loader2 className="animate-spin text-primary" size={24} />
                    </div>
                  ) : activeSubTab === 'logs' ? (
                    <div className="space-y-4">
                      {logs.length === 0 ? (
                        <div className="text-center text-slate-500 py-12 italic">该项目暂无审计日志</div>
                      ) : logs.map(log => (
                        <div key={log.id} className="bg-slate-900/50 rounded-lg border border-slate-800 overflow-hidden">
                          <div className="bg-slate-800/50 px-4 py-2 flex justify-between items-center border-b border-slate-800">
                            <div className="flex items-center gap-3">
                              <span className="text-xs font-mono text-primary font-bold">[{log.agent_name}]</span>
                            </div>
                            <span className="text-[10px] text-slate-500 font-mono">{new Date(log.timestamp).toLocaleString()}</span>
                          </div>
                          <div className="p-4">
                            <div className="text-xs text-slate-400 mb-2 font-semibold uppercase tracking-wider">AI Thinking / Response:</div>
                            <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed bg-black/20 p-3 rounded border border-slate-800">
                              {log.response}
                            </pre>
                            <div className="mt-3 flex justify-end">
                              <button 
                                onClick={() => setSelectedLog(log)}
                                className="text-[10px] text-primary hover:underline flex items-center gap-1"
                              >
                                查看完整上下文 <ChevronRight size={10} />
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-6">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-bold text-slate-300">漏洞发现列表</h4>
                      </div>
                      <div className="bg-slate-900/50 rounded-lg border border-slate-800 overflow-hidden">
                        <table className="w-full text-left">
                          <thead className="bg-slate-800/50 text-slate-400 text-[10px] font-semibold uppercase">
                            <tr>
                              <th className="px-4 py-3">类型</th>
                              <th className="px-4 py-3">风险</th>
                              <th className="px-4 py-3">参数</th>
                              <th className="px-4 py-3">URL</th>
                              <th className="px-4 py-3">时间</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800">
                            {vulnerabilities.length === 0 ? (
                              <tr>
                                <td colSpan={5} className="px-4 py-8 text-center text-slate-500 italic">未发现漏洞</td>
                              </tr>
                            ) : vulnerabilities.map(v => (
                              <tr 
                                key={v.id} 
                                onClick={() => setSelectedVuln(v)}
                                className="hover:bg-slate-800/30 transition-colors cursor-pointer text-xs"
                              >
                                <td className="px-4 py-3 font-medium">{v.vuln_type}</td>
                                <td className="px-4 py-3">
                                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                                    v.severity === 'critical' || v.severity === 'high' ? 'bg-danger/10 text-danger' :
                                    v.severity === 'medium' ? 'bg-warning/10 text-warning' : 'bg-primary/10 text-primary'
                                  }`}>
                                    {v.severity}
                                  </span>
                                </td>
                                <td className="px-4 py-3 font-mono text-slate-400">{v.parameter || '-'}</td>
                                <td className="px-4 py-3 text-slate-500 truncate max-w-[200px]" title={v.url}>{v.url}</td>
                                <td className="px-4 py-3 text-slate-500">{new Date(v.found_at).toLocaleDateString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500 gap-4">
              <History size={48} className="opacity-20" />
              <p>请从左侧选择一个项目查看详情</p>
            </div>
          )}
        </div>
      </div>

      {/* Log Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-8">
          <div className="bg-[#1e293b] w-full max-w-4xl max-h-[80vh] rounded-2xl border border-slate-700 flex flex-col shadow-2xl">
            <div className="p-4 border-b border-slate-700 flex items-center justify-between">
              <h4 className="font-bold">LLM Prompt 详情审计</h4>
              <button onClick={() => setSelectedLog(null)} className="text-slate-400 hover:text-white">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 overflow-y-auto bg-black/20 font-mono text-sm text-slate-300 space-y-6">
              <div>
                <div className="text-primary font-bold border-b border-primary/20 pb-1 mb-3"># AGENT_PROMPT (INPUT)</div>
                <pre className="opacity-80 whitespace-pre-wrap">{selectedLog.prompt}</pre>
              </div>
              
              <div>
                <div className="text-success font-bold border-b border-success/20 pb-1 mb-3"># AI_RESPONSE (OUTPUT)</div>
                <pre className="opacity-90 whitespace-pre-wrap">{selectedLog.response}</pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Vulnerability Detail Modal */}
      {selectedVuln && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-8">
          <div className="bg-[#1e293b] w-full max-w-5xl max-h-[90vh] rounded-2xl border border-slate-700 flex flex-col shadow-2xl">
            <div className="p-4 border-b border-slate-700 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertTriangle className="text-danger" size={20} />
                <h4 className="font-bold text-lg">漏洞详情: {selectedVuln.vuln_type}</h4>
                <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${
                  selectedVuln.severity === 'critical' || selectedVuln.severity === 'high' ? 'bg-danger/10 text-danger' :
                  selectedVuln.severity === 'medium' ? 'bg-warning/10 text-warning' : 'bg-primary/10 text-primary'
                }`}>
                  {selectedVuln.severity}
                </span>
              </div>
              <button onClick={() => setSelectedVuln(null)} className="text-slate-400 hover:text-white transition-colors">
                <X size={24} />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-8">
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <div className="text-xs text-slate-500 uppercase font-bold mb-1">目标 URL</div>
                    <div className="bg-slate-900 p-3 rounded border border-slate-800 font-mono text-sm break-all">
                      <span className="text-primary mr-2">{selectedVuln.method}</span>
                      {selectedVuln.url}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 uppercase font-bold mb-1">受影响参数 / Payload</div>
                    <div className="bg-slate-900 p-3 rounded border border-slate-800 font-mono text-sm">
                      <div><span className="text-slate-400">Parameter:</span> {selectedVuln.parameter || 'N/A'}</div>
                      <div className="mt-2 pt-2 border-t border-slate-800">
                        <span className="text-slate-400">Payload:</span> <span className="text-warning">{selectedVuln.payload}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* AI Judgment */}
                <div className="flex flex-col h-full">
                  <div className="text-xs text-success uppercase font-bold mb-1 flex items-center gap-1">
                    <Activity size={14} /> AI 判断依据 (Evidence)
                  </div>
                  <div className="flex-1 bg-success/5 border border-success/20 p-4 rounded-lg text-sm text-slate-200 italic leading-relaxed whitespace-pre-wrap">
                    {selectedVuln.evidence}
                  </div>
                </div>
              </div>

              {/* Original Request */}
              <div>
                <div className="text-xs text-primary uppercase font-bold mb-2 flex items-center gap-1">
                  <ExternalLink size={14} /> 原始请求信息 (Original Request)
                </div>
                <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
                  <div className="bg-slate-800/50 px-4 py-2 border-b border-slate-800 text-[10px] text-slate-400 font-mono">
                  </div>
                  <pre className="p-4 font-mono text-xs text-slate-300 overflow-x-auto">
                    {(() => {
                      try {
                        const req = typeof selectedVuln.full_request === 'string' 
                          ? JSON.parse(selectedVuln.full_request) 
                          : selectedVuln.full_request;
                        
                        if (typeof req === 'object' && req !== null) {
                          let raw = `${req.method} ${req.url}\n`;
                          if (req.headers) {
                            Object.entries(req.headers).forEach(([k, v]) => {
                              raw += `${k}: ${v}\n`;
                            });
                          }
                          if (req.body) {
                            raw += `\n${typeof req.body === 'object' ? JSON.stringify(req.body, null, 2) : req.body}`;
                          }
                          return raw;
                        }
                        return selectedVuln.full_request;
                      } catch (e) {
                        return selectedVuln.full_request;
                      }
                    })()}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectsView;
