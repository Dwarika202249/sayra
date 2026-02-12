import speech_recognition as sr
from faster_whisper import WhisperModel
import os
import yaml
import asyncio

class SayraEar:
    def __init__(self):
        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        
        # Hardware Config
        self.model_size = self.config['hearing']['model_size'] # 'tiny'
        self.device = self.config['hearing'].get('device', 'cpu')
        self.compute_type = self.config['hearing'].get('compute_type', 'int8')
        
        print(f"[SAYRA]: Loading Ear Model ({self.model_size})...")
        self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        
        # Calibration for ambient noise
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def listen(self):
        """Captures audio and transcribes it locally"""
        try:
            with self.mic as source:
                print("\n[SAYRA]: Listening... (Speak now)")
                # Timeout: Agar 5 sec tak kuch nahi bole to stop
                # Phrase_time_limit: Max 10 sec ki baat sunegi
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Save temp audio for Whisper
            with open("temp_command.wav", "wb") as f:
                f.write(audio.get_wav_data())
            
            # Transcribe
            segments, info = self.model.transcribe("temp_command.wav", beam_size=5)
            
            user_text = ""
            for segment in segments:
                user_text += segment.text
            
            # Cleanup
            if os.path.exists("temp_command.wav"):
                os.remove("temp_command.wav")
                
            return user_text.strip()

        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            print(f"[Ear Error]: {e}")
            return None

# Global Instance
ear = SayraEar()