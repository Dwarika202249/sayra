import { useState, useEffect } from 'react';
import io from 'socket.io-client';
import { Mic, Activity } from 'lucide-react';

// Connect to Python Backend
const socket = io('http://localhost:8080');

function App() {
  const [status, setStatus] = useState('offline');
  const [mode, setMode] = useState('idle'); // idle, listening, processing
  const [lastMessage, setLastMessage] = useState('Sayra Systems Initializing...');

  useEffect(() => {
    // Connection Handlers
    socket.on('connect', () => setStatus('online'));
    socket.on('disconnect', () => setStatus('offline'));
    
    // Custom Events from Server
    socket.on('bot_message', (msg) => {
      setLastMessage(msg);
      setMode('idle');
    });

    socket.on('sayra_state', (state) => setMode(state));
    
    return () => socket.off();
  }, []);

  const handleMicClick = () => {
    setMode('listening');
    socket.emit('voice_trigger');
  };

  // --- MINIMAL ORB UI ---
  return (
    <div className="flex items-center justify-center w-screen h-screen">
      {/* The Glowing Orb */}
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
      >
        {/* Inner Icon */}
        {mode === 'listening' ? (
          <Mic className="w-8 h-8 text-white animate-bounce" />
        ) : (
          <div className={`w-12 h-12 rounded-full bg-linear-to-tr from-sayra-blue to-sayra-cyan opacity-80 ${mode === 'idle' ? 'animate-pulse-slow' : 'animate-spin'}`} />
        )}
        
        {/* Status Tooltip (Simple Debug) */}
        <div className="absolute -top-12 left-1/2 -translate-x-1/2 w-48 text-xs text-center text-white bg-black/80 p-1 rounded opacity-0 hover:opacity-100 transition-opacity pointer-events-none">
          {lastMessage}
        </div>
      </div>
    </div>
  );
}

export default App;