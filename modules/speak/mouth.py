import edge_tts
import pygame
import asyncio
import os
import yaml

class SayraMouth:
    def __init__(self):
        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        self.voice = config['speech']['voice']
        self.rate = config['speech']['rate']
        self.volume = config['speech']['volume']
        self.output_file = "sayra_voice_temp.mp3"

    async def speak(self, text):
        """Text ko Audio me convert karke play karega"""
        if not text:
            return

        # Terminal feedback
        print(f"SAYRA (🔊): {text}")

        # Generate Audio
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, volume=self.volume)
        await communicate.save(self.output_file)

        # Play Audio
        self.play_audio()

    def play_audio(self):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(self.output_file)
            pygame.mixer.music.play()
            
            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.quit()
            
            # Cleanup temp file
            if os.path.exists(self.output_file):
                os.remove(self.output_file)
                
        except Exception as e:
            print(f"[Mouth Error]: {e}")

# Global instance
mouth = SayraMouth()