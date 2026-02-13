import React, { useEffect, useRef } from 'react';
import { Activity, Battery, Cpu, Shield, Wifi, X } from 'lucide-react';

const Dashboard = ({ vitals, logs, onClose, status }) => {
  const logsEndRef = useRef(null);

  // Auto-scroll to latest log
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-50">
      {/* Main HUD Container */}
      <div className="w-[200] h-[125] glass-panel rounded-lg flex flex-col p-6 relative animate-in fade-in zoom-in duration-300">
        
        {/* Header */}
        <div className="flex justify-between items-center border-b border-sayra-cyan/30 pb-4 mb-4">
          <div className="flex items-center gap-3">
            <Activity className="text-sayra-cyan animate-pulse" />
            <h1 className="text-xl font-bold tracking-widest text-sayra-cyan">SAYRA SYSTEMS</h1>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono text-gray-400">
            <span>MODE: {status.toUpperCase()}</span>
            <button onClick={onClose} className="hover:text-red-500 transition-colors">
              <X />
            </button>
          </div>
        </div>

        {/* Grid Layout */}
        <div className="grid grid-cols-3 gap-6 flex-1 overflow-hidden">
          
          {/* Left Column: Vitals */}
          <div className="flex flex-col gap-4">
            <VitalsCard label="CPU LOAD" value={vitals.cpu} icon={Cpu} color="text-yellow-400" />
            <VitalsCard label="MEMORY" value={vitals.ram} icon={Activity} color="text-purple-400" />
            <VitalsCard label="BATTERY" value={vitals.battery} icon={Battery} sub={vitals.power} color={vitals.power === 'Charging' ? 'text-green-400' : 'text-blue-400'} />
            
            {/* Protocol Status Mini-List */}
            <div className="mt-auto p-3 bg-sayra-bg/50 rounded border border-white/5">
              <h3 className="text-xs text-gray-500 mb-2">ACTIVE PROTOCOLS</h3>
              <div className="space-y-1">
                <StatusItem label="Retina Guard" active={true} />
                <StatusItem label="Sentry Mode" active={false} /> {/* Future: Connect to real state */}
                <StatusItem label="Circadian" active={true} />
              </div>
            </div>
          </div>

          {/* Middle & Right Column: The Brain (Logs/Chat) */}
          <div className="col-span-2 bg-black/40 rounded border border-white/10 flex flex-col font-mono text-sm relative">
            <div className="absolute top-0 left-0 bg-sayra-cyan/20 px-2 py-1 text-[10px] text-sayra-cyan">LIVE FEED</div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-3 mt-4 custom-scrollbar">
              {logs.length === 0 && <div className="text-gray-600 italic">Waiting for input...</div>}
              
              {logs.map((log, index) => (
                <div key={index} className={`flex flex-col ${log.type === 'user' ? 'items-end' : 'items-start'}`}>
                  <span className={`px-3 py-2 rounded max-w-[90%] ${
                    log.type === 'user' 
                      ? 'bg-sayra-blue/20 text-sayra-cyan border border-sayra-blue/30' 
                      : 'bg-gray-800/50 text-gray-300 border border-white/10'
                  }`}>
                    {log.message}
                  </span>
                  <span className="text-[10px] text-gray-600 mt-1">{log.time}</span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

// Sub-components for cleaner code
const VitalsCard = ({ label, value, icon: Icon, color, sub }) => (
  <div className="bg-sayra-bg/50 p-3 rounded border border-white/10 flex items-center justify-between">
    <div>
      <div className="text-[10px] text-gray-500 tracking-wider mb-1">{label}</div>
      <div className={`text-xl font-bold ${color}`}>{value}%</div>
      {sub && <div className="text-[9px] text-gray-400">{sub}</div>}
    </div>
    <Icon className={`w-6 h-6 ${color} opacity-80`} />
  </div>
);

const StatusItem = ({ label, active }) => (
  <div className="flex justify-between items-center text-xs">
    <span className="text-gray-400">{label}</span>
    <span className={`w-2 h-2 rounded-full ${active ? 'bg-green-500 shadow-[0_0_5px_rgba(34,197,94,0.6)]' : 'bg-red-900'}`} />
  </div>
);

export default Dashboard;