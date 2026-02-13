import pvporcupine
import struct
import pyaudio
import os
import yaml
import sys
from dotenv import load_dotenv

load_dotenv()

class WakeWordListener:
    def __init__(self):
        # Config Load
        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            
        self.access_key = os.getenv("PICOVOICE_ACCESS_KEY")
        self.model_file = self.config['hearing'].get('wake_word_file')
        self.sensitivity = self.config['hearing'].get('sensitivity', 0.5)
        
        self.porcupine = None
        self.pa = None
        self.audio_stream = None

        if not self.access_key:
            print("[WakeWord Error]: PICOVOICE_ACCESS_KEY not found in .env")
            return

        try:
            # Model Selection Logic
            keyword_paths = []
            if self.model_file:
                abs_path = os.path.abspath(self.model_file)
                if os.path.exists(abs_path):
                    keyword_paths = [abs_path]
                    print(f"[SAYRA]: Loading Custom Wake Word: {self.model_file}")
                else:
                    print(f"[WakeWord Warning]: Custom file not found. Using Default.")
            
            # Initialize Porcupine
            if keyword_paths:
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keyword_paths=keyword_paths,
                    sensitivities=[self.sensitivity] * len(keyword_paths)
                )
            else:
                print("[SAYRA]: Using Default Wake Word (Jarvis)")
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keywords=['jarvis']
                )
            
            self.pa = pyaudio.PyAudio()
            self.open_stream() # Initial Stream Start
            
        except Exception as e:
            print(f"[WakeWord Init Error]: {e}")
            self.porcupine = None

    def open_stream(self):
        """Opens the PyAudio stream"""
        if self.porcupine and (self.audio_stream is None):
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )

    def listen(self):
        """Reads stream. Returns True if Hotword Detected."""
        # Agar stream closed hai (Paused), to listen mat karo
        if not self.audio_stream:
            return False

        try:
            pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            
            keyword_index = self.porcupine.process(pcm)
            
            if keyword_index >= 0:
                print(f"[WakeWord]: ⚡ Hotword Detected!")
                return True
                
        except Exception as e:
            # Stream errors (like buffer overflow) ko ignore karo
            pass
        
        return False

    def pause(self):
        """Releases the Mic for other modules"""
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
            print("[WakeWord]: Mic Released (Paused)")

    def resume(self):
        """Re-acquires the Mic"""
        self.open_stream()
        print("[WakeWord]: Mic Re-acquired (Resumed)")

    def cleanup(self):
        if self.porcupine:
            self.porcupine.delete()
        if self.audio_stream:
            self.audio_stream.close()
        if self.pa:
            self.pa.terminate()

# Global Instance
wake_listener = WakeWordListener()