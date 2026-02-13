import pvporcupine
import struct
import pyaudio
import os
import yaml
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WakeWordListener:
    def __init__(self):
        # 1. Load Config
        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            
        self.access_key = os.getenv("PICOVOICE_ACCESS_KEY")
        self.model_file = self.config['hearing'].get('wake_word_file')
        self.sensitivity = self.config['hearing'].get('sensitivity', 0.7)

        if not self.access_key:
            print("[WakeWord Error]: PICOVOICE_ACCESS_KEY not found in .env")
            self.porcupine = None
            return

        try:
            # 2. Check for Custom Model
            keyword_paths = []
            if self.model_file:
                # Absolute path conversion
                abs_path = os.path.abspath(self.model_file)
                if os.path.exists(abs_path):
                    keyword_paths = [abs_path]
                    print(f"[SAYRA]: Loading Custom Wake Word: {self.model_file}")
                else:
                    print(f"[WakeWord Warning]: Custom file not found at {abs_path}. Falling back to default.")
            
            # 3. Initialize Porcupine
            if keyword_paths:
                # Use Custom Model ("Hey Syra")
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keyword_paths=keyword_paths,
                    sensitivities=[self.sensitivity] * len(keyword_paths)
                )
            else:
                # Use Default ("Jarvis")
                print("[SAYRA]: Using Default Wake Word (Jarvis)")
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keywords=['jarvis']
                )
            
            # 4. Audio Stream Setup
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            
        except Exception as e:
            print(f"[WakeWord Init Error]: {e}")
            self.porcupine = None

    def listen(self):
        """
        Reads one frame of audio and checks for the wake word.
        Blocking for a few milliseconds only.
        """
        if not self.porcupine or not self.audio_stream:
            return False

        try:
            pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            
            keyword_index = self.porcupine.process(pcm)
            
            if keyword_index >= 0:
                print(f"[WakeWord]: ⚡ Hotword Detected!")
                return True
                
        except Exception as e:
            # Audio stream errors ignore karte hain taaki loop na toote
            pass
        
        return False

    def cleanup(self):
        if self.porcupine:
            self.porcupine.delete()
        if self.audio_stream:
            self.audio_stream.close()
        if self.pa:
            self.pa.terminate()

# Global Instance
wake_listener = WakeWordListener()