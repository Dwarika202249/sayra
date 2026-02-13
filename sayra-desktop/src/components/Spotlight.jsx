import React, { useState, useEffect, useRef } from 'react';
import { Search, CornerDownLeft, X } from 'lucide-react';

const Spotlight = ({ onClose, onCommand, visible }) => {
  const [input, setInput] = useState('');
  const inputRef = useRef(null);

  // Auto-focus jab bhi open ho
  useEffect(() => {
    if (visible && inputRef.current) {
      inputRef.current.focus();
    }
  }, [visible]);

  // Handle Enter Key
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && input.trim()) {
      onCommand(input);
      setInput('');
      onClose();
    }
    if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!visible) return null;

  return (
    <div className="fixed inset-0 flex items-start justify-center pt-[20vh] bg-black/40 backdrop-blur-sm z-50 animate-in fade-in duration-200">
      
      {/* Search Bar Container */}
      <div className="w-[600px] bg-sayra-bg/80 border border-sayra-cyan/30 rounded-xl shadow-[0_0_40px_rgba(0,217,255,0.1)] overflow-hidden backdrop-blur-md">
        
        {/* Input Area */}
        <div className="flex items-center px-4 py-4 border-b border-white/10">
          <Search className="w-6 h-6 text-sayra-cyan mr-3" />
          <input
            ref={inputRef}
            type="text"
            className="flex-1 bg-transparent border-none outline-none text-xl text-white placeholder-gray-500 font-mono"
            placeholder="Ask Sayra or execute command..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 border border-white/10 px-2 py-1 rounded">ESC</span>
          </div>
        </div>

        {/* Quick Suggestions (Optional visual fill) */}
        <div className="bg-black/20 px-4 py-2 text-xs text-gray-500 flex justify-between items-center">
          <span>SAYRA v0.1 INTELLIGENCE</span>
          <span className="flex items-center gap-1">
            Execute <CornerDownLeft size={12} />
          </span>
        </div>
      </div>
    </div>
  );
};

export default Spotlight;