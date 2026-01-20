import React from 'react';

interface SettingFieldProps {
  label: string;
  type: string;
  value: string | number;
  onChange?: (value: string) => void;
  description: string;
}

const SettingField: React.FC<SettingFieldProps> = ({ label, type, value, onChange, description }) => (
  <div className="space-y-2">
    <div className="flex items-center justify-between">
      <label className="text-sm font-mono text-slate-300 font-medium">{label}</label>
    </div>
    <input 
      type={type} 
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:ring-1 focus:ring-primary outline-none transition-all"
    />
    <p className="text-xs text-slate-500 italic">{description}</p>
  </div>
);

export default SettingField;
