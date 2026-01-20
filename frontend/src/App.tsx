import React, { useState } from 'react';
import { 
  ShieldAlert, 
  Settings, 
  Activity, 
  AlertTriangle,
  ChevronRight,
  Database
} from 'lucide-react';

import NavItem from './components/NavItem';
import ScannerView from './views/ScannerView';
import SettingsView from './views/SettingsView';
import ProjectsView from './views/ProjectsView';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('scanner');

  return (
    <div className="flex h-screen bg-[#0f172a] font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-[#1e293b] border-r border-slate-700 flex flex-col">
        <div className="p-6 flex items-center gap-3">
          <div className="bg-primary/20 p-2 rounded-lg">
            <ShieldAlert className="text-primary w-8 h-8" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">AegisX</h1>
        </div>

        <nav className="flex-1 px-4 py-4 space-y-1">
          <NavItem 
            icon={<Activity size={20} />} 
            label="开始扫描" 
            active={activeTab === 'scanner'} 
            onClick={() => setActiveTab('scanner')} 
          />
          <NavItem 
            icon={<Database size={20} />} 
            label="项目管理" 
            active={activeTab === 'projects'} 
            onClick={() => setActiveTab('projects')} 
          />
        </nav>

        <div className="p-4 border-t border-slate-700">
          <NavItem 
            icon={<Settings size={20} />} 
            label="系统设置" 
            active={activeTab === 'settings'} 
            onClick={() => setActiveTab('settings')} 
          />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-[#1e293b]/50 border-b border-slate-700 flex items-center justify-between px-8">
          <div className="flex items-center gap-4 text-slate-400">
            <span className="text-sm">项目: <span className="text-white font-medium">Default_Project</span></span>
            <ChevronRight size={16} />
            <span className="text-sm text-white capitalize">
              {activeTab === 'scanner' ? '开始扫描' :
               activeTab === 'projects' ? '项目管理' : '系统设置'}
            </span>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-8">
          {activeTab === 'scanner' && <ScannerView />}
          {activeTab === 'settings' && <SettingsView />}
          {activeTab === 'projects' && <ProjectsView />}
        </div>
      </main>
    </div>
  );
};

export default App;
