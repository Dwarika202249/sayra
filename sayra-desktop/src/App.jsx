import { useState, useEffect } from 'react';
import io from 'socket.io-client';
import { Mic, LayoutDashboard } from 'lucide-react';
import Dashboard from './components/Dashboard';

// Connect to Python Backend
const socket = io('http://localhost:8080');

function App() {
  const [status, setStatus] = useState('offline');
  const [mode, setMode] = useState('idle'); // idle, listening, processing
  const [lastMessage, setLastMessage] = useState('Systems Initializing...');
  const [showHud, setShowHud] = useState(false);
  const [vitals, setVitals] = useState({ cpu: 0, ram: 0, battery: 0, power: '' });
  const [chatLogs, setChatLogs] = useState([]);

  useEffect(() => {
    // Connection Handlers
    socket.on('connect', () => setStatus('online'));
    socket.on('disconnect', () => setStatus('offline'));

    // Handle Vitals
    socket.on('system_vitals', (data) => {
      setVitals(data);
    });
    
    // Handle Messages & Logs
    socket.on('bot_message', (msg) => {
      setLastMessage(msg);
      setMode('idle');
      addLog('bot', msg);
    });

    socket.on('user_transcription', (text) => {
      addLog('user', text);
    });

    socket.on('sayra_state', (state) => setMode(state));
    
    return () => socket.off();
  }, []);

  const addLog = (type, message) => {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setChatLogs(prev => [...prev, { type, message, time }]);
  };

  const handleMicClick = () => {
    setMode('listening');
    socket.emit('voice_trigger');
  };

  return (
    <div className="w-screen h-screen overflow-hidden">
      
      {/* THE DASHBOARD OVERLAY */}
      {showHud && (
        <Dashboard 
          vitals={vitals} 
          logs={chatLogs} 
          status={mode} 
          onClose={() => setShowHud(false)} 
        />
      )}

      {/* THE ORB (Always visible in corner) */}
      <div className="absolute bottom-10 right-10 flex flex-col items-end gap-2">
        
        {/* Toggle HUD Button (Small) */}
        <button 
          onClick={() => setShowHud(!showHud)}
          className="bg-black/50 p-2 rounded-full text-sayra-cyan border border-sayra-cyan/30 hover:bg-sayra-cyan/20 transition-all"
          title="Open Dashboard"
        >
          <LayoutDashboard size={16} />
        </button>

        {/* Main Orb */}
        <div 
          className={`
            relative flex items-center justify-center 
            w-20 h-20 rounded-full glass-panel cursor-pointer
            transition-all duration-500
            ${mode === 'listening' ? 'border-red-500 shadow-[0_0_30px_rgba(239,68,68,0.6)]' : 
              mode === 'processing' ? 'border-purple-500 animate-pulse' : 
              'border-sayra-cyan shadow-[0_0_20px_rgba(0,217,255,0.4)]'}
            ${status === 'offline' ? 'grayscale opacity-50' : ''}
          `}
          onClick={handleMicClick}
          onDoubleClick={() => setShowHud(true)} // Double click shortcut
        >
          {mode === 'listening' ? (
            <Mic className="w-8 h-8 text-white animate-bounce" />
          ) : (
            <div className={`w-12 h-12 rounded-full bg-linear-to-tr from-sayra-blue to-sayra-cyan opacity-80 ${mode === 'idle' ? 'animate-pulse-slow' : 'animate-spin'}`} />
          )}
        </div>
        
        {/* Toast Message */}
        {!showHud && (
          <div className="bg-black/60 backdrop-blur text-xs text-white px-3 py-1 rounded-md border border-white/10 max-w-[50] truncate">
            {lastMessage}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;