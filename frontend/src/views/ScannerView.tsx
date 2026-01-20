import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Activity, Play, StopCircle, Loader2 } from 'lucide-react';
import { ScannerAPI } from '../api';

interface LogEntry {
  time: string;
  level: string;
  content: string;
}

const ScannerView: React.FC = () => {
  const [projectName, setProjectName] = useState('Default_Project');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [status, setStatus] = useState<'idle' | 'running' | 'error'>('idle');
  const scrollRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // 检查初始状态
    const checkStatus = async () => {
      try {
        const response = await ScannerAPI.getStatus();
        if (response.data.status === 'running') {
          setIsScanning(true);
          setStatus('running');
          connectWebSocket();
        }
      } catch (error) {
        console.error('Failed to get scanner status:', error);
      }
    };
    checkStatus();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const startScanner = async () => {
    setIsScanning(true);
    setStatus('running');
    try {
      await ScannerAPI.startScanner(projectName);
      connectWebSocket();
    } catch (error) {
      console.error('Failed to start scanner:', error);
      setStatus('error');
      setIsScanning(false);
    }
  };

  const connectWebSocket = () => {
    if (wsRef.current) wsRef.current.close();

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/scanner/ws/logs`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const log: LogEntry = JSON.parse(event.data);
        setLogs(prev => [...prev.slice(-100), log]); // Keep last 100 logs
      } catch (e) {
        // Handle plain text logs if any
        setLogs(prev => [...prev.slice(-100), { time: new Date().toLocaleTimeString(), level: 'INFO', content: event.data }]);
      }
    };

    ws.onclose = () => {
      if (isScanning) {
        setTimeout(connectWebSocket, 3000); // Reconnect
      }
    };

    wsRef.current = ws;
  };

  const stopScanner = async () => {
    try {
      await ScannerAPI.stopScanner();
    } catch (error) {
      console.error('Failed to stop scanner:', error);
    }
    setIsScanning(false);
    setStatus('idle');
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-full">
      <div className="lg:col-span-1 space-y-6">
        <div className="bg-[#1e293b] rounded-xl border border-slate-700 p-6">
          <h3 className="text-lg font-semibold mb-6">扫描配置</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-2">项目名称</label>
              <input 
                type="text" 
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                disabled={isScanning}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-primary outline-none transition-all disabled:opacity-50" 
              />
            </div>
            
            <div className="pt-4">
              {!isScanning ? (
                <button 
                  onClick={startScanner}
                  className="w-full bg-primary hover:bg-primary/90 text-white py-3 rounded-lg font-semibold transition-all shadow-lg shadow-primary/20 flex items-center justify-center gap-2"
                >
                  <Play size={18} />
                  开始监听流量
                </button>
              ) : (
                <button 
                  onClick={stopScanner}
                  className="w-full bg-danger hover:bg-danger/90 text-white py-3 rounded-lg font-semibold transition-all shadow-lg shadow-danger/20 flex items-center justify-center gap-2"
                >
                  <StopCircle size={18} />
                  停止监听
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="bg-[#1e293b] rounded-xl border border-slate-700 p-6">
          <h4 className="text-sm font-semibold mb-4 text-slate-300">运行状态</h4>
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${isScanning ? 'bg-success animate-pulse' : 'bg-slate-600'}`} />
            <span className="text-sm text-slate-400">
              {isScanning ? '正在实时审计流量...' : '空闲中'}
            </span>
          </div>
        </div>
      </div>

      <div className="lg:col-span-2 bg-black/50 rounded-xl border border-slate-700 overflow-hidden flex flex-col">
        <div className="bg-slate-800 px-4 py-2 border-b border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal size={16} className="text-slate-400" />
            <span className="text-xs font-mono text-slate-400">AegisX_Live_Console</span>
          </div>
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/20" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/20" />
            <div className="w-3 h-3 rounded-full bg-green-500/20" />
          </div>
        </div>
        <div 
          ref={scrollRef}
          className="flex-1 p-4 font-mono text-sm overflow-y-auto terminal-scrollbar space-y-1"
        >
          {logs.length === 0 && !isScanning && (
            <div className="text-slate-600 italic">等待开启监听以接收实时审计日志...</div>
          )}
          {logs.map((log, i) => (
            <div key={i} className="text-slate-400 break-all">
              <span className="text-slate-600">[{log.time}]</span>{' '}
              <span className={`font-bold ${
                log.level === 'ERROR' ? 'text-danger' : 
                log.level === 'SUCCESS' ? 'text-success' : 
                log.level === 'WARNING' ? 'text-warning' : 'text-primary'
              }`}>
                {log.level}
              </span>{' '}
              {log.content}
            </div>
          ))}
          {isScanning && (
            <div className="animate-pulse inline-block w-2 h-4 bg-primary ml-1 align-middle" />
          )}
        </div>
      </div>
    </div>
  );
};

export default ScannerView;
