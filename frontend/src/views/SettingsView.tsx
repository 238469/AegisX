import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Settings, Database, Save, Loader2 } from 'lucide-react';
import SettingField from '../components/SettingField';
import { SettingsAPI } from '../api';

const SettingsView: React.FC = () => {
  const [configs, setConfigs] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await SettingsAPI.getSettings();
      setConfigs(response.data);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await SettingsAPI.updateSettings(configs);
      alert('配置保存成功！');
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('保存失败，请检查后端服务。');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (key: string, value: any) => {
    setConfigs(prev => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  return (
    <div className="max-w-4xl space-y-8 pb-12">
      <div className="flex items-center justify-between sticky top-0 bg-[#0f172a] py-4 z-10">
        <h3 className="text-xl font-bold">系统设置</h3>
        <button 
          onClick={handleSave}
          disabled={saving}
          className="bg-primary hover:bg-primary/90 text-white px-6 py-2 rounded-lg font-medium transition-all flex items-center gap-2 disabled:opacity-50"
        >
          {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
          {saving ? '正在保存...' : '保存更改'}
        </button>
      </div>

      <div className="space-y-6">
        {/* LLM Configuration */}
        <section className="bg-[#1e293b] rounded-xl border border-slate-700 overflow-hidden">
          <div className="bg-slate-800 px-6 py-3 border-b border-slate-700">
            <h4 className="font-semibold flex items-center gap-2">
              <Activity size={18} className="text-primary" />
              LLM 配置 (Large Language Model)
            </h4>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <SettingField 
              label="OPENAI_API_KEY" 
              type="password" 
              value={configs.OPENAI_API_KEY} 
              onChange={(v) => handleChange('OPENAI_API_KEY', v)}
              description="用于驱动 Agent 推理的 API Key" 
            />
            <SettingField 
              label="OPENAI_API_BASE" 
              type="text" 
              value={configs.OPENAI_API_BASE} 
              onChange={(v) => handleChange('OPENAI_API_BASE', v)}
              description="API 基础端点地址" 
            />
            <SettingField 
              label="MODEL_NAME_MANAGER" 
              type="text" 
              value={configs.MODEL_NAME_MANAGER} 
              onChange={(v) => handleChange('MODEL_NAME_MANAGER', v)}
              description="Manager 节点主控模型" 
            />
            <SettingField 
              label="MODEL_NAME_WORKER" 
              type="text" 
              value={configs.MODEL_NAME_WORKER} 
              onChange={(v) => handleChange('MODEL_NAME_WORKER', v)}
              description="Worker 节点执行模型" 
            />
          </div>
        </section>

        {/* Proxy & Network */}
        <section className="bg-[#1e293b] rounded-xl border border-slate-700 overflow-hidden">
          <div className="bg-slate-800 px-6 py-3 border-b border-slate-700">
            <h4 className="font-semibold flex items-center gap-2">
              <ShieldAlert size={18} className="text-warning" />
              代理与网络配置
            </h4>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <SettingField 
              label="MITM_PROXY_PORT" 
              type="number" 
              value={configs.MITM_PROXY_PORT} 
              onChange={(v) => handleChange('MITM_PROXY_PORT', parseInt(v))}
              description="流量拦截代理端口" 
            />
            <SettingField 
              label="SCAN_PROXY" 
              type="text" 
              value={configs.SCAN_PROXY || ''} 
              onChange={(v) => handleChange('SCAN_PROXY', v)}
              description="探测请求发出的上游代理" 
            />
            <SettingField 
              label="SCAN_TIMEOUT" 
              type="number" 
              value={configs.SCAN_TIMEOUT} 
              onChange={(v) => handleChange('SCAN_TIMEOUT', parseFloat(v))}
              description="单次请求超时时间 (秒)" 
            />
          </div>
        </section>

        {/* Scan Control */}
        <section className="bg-[#1e293b] rounded-xl border border-slate-700 overflow-hidden">
          <div className="bg-slate-800 px-6 py-3 border-b border-slate-700">
            <h4 className="font-semibold flex items-center gap-2">
              <Settings size={18} className="text-success" />
              扫描策略控制
            </h4>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <SettingField 
              label="SCAN_MAX_TASKS" 
              type="number" 
              value={configs.SCAN_MAX_TASKS} 
              onChange={(v) => handleChange('SCAN_MAX_TASKS', parseInt(v))}
              description="同时处理的最大流量请求数" 
            />
            <SettingField 
              label="SCAN_MAX_CONCURRENCY" 
              type="number" 
              value={configs.SCAN_MAX_CONCURRENCY} 
              onChange={(v) => handleChange('SCAN_MAX_CONCURRENCY', parseInt(v))}
              description="单个任务内的并发探测线程" 
            />
            <SettingField 
              label="SCAN_MAX_RETRIES" 
              type="number" 
              value={configs.SCAN_MAX_RETRIES} 
              onChange={(v) => handleChange('SCAN_MAX_RETRIES', parseInt(v))}
              description="AI 尝试 Bypass 的最大重试轮数" 
            />
            <SettingField 
              label="TARGET_WHITELIST" 
              type="text" 
              value={Array.isArray(configs.TARGET_WHITELIST) ? configs.TARGET_WHITELIST.join(', ') : configs.TARGET_WHITELIST} 
              onChange={(v) => handleChange('TARGET_WHITELIST', v)}
              description="允许扫描的目标范围 (逗号分隔)" 
            />
          </div>
        </section>

        {/* Storage & Infrastructure */}
        <section className="bg-[#1e293b] rounded-xl border border-slate-700 overflow-hidden">
          <div className="bg-slate-800 px-6 py-3 border-b border-slate-700">
            <h4 className="font-semibold flex items-center gap-2">
              <Database size={18} className="text-primary" />
              基础设施配置
            </h4>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <SettingField 
              label="REDIS_URL" 
              type="text" 
              value={configs.REDIS_URL} 
              onChange={(v) => handleChange('REDIS_URL', v)}
              description="去重与指纹存储地址" 
            />
            <SettingField 
              label="LOG_LEVEL" 
              type="text" 
              value={configs.LOG_LEVEL} 
              onChange={(v) => handleChange('LOG_LEVEL', v)}
              description="系统日志详细程度 (DEBUG/INFO/WARN)" 
            />
            <div className="flex items-center justify-between p-4 bg-slate-900 rounded-lg border border-slate-700">
              <div>
                <div className="text-sm font-medium text-slate-300">LOG_PROMPT_INTERACTION</div>
                <div className="text-xs text-slate-500 italic">是否记录全量 LLM Prompt 交互日志</div>
              </div>
              <input 
                type="checkbox" 
                checked={configs.LOG_PROMPT_INTERACTION} 
                onChange={(e) => handleChange('LOG_PROMPT_INTERACTION', e.target.checked)}
                className="w-5 h-5 rounded border-slate-700 bg-slate-800 text-primary focus:ring-primary" 
              />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default SettingsView;
