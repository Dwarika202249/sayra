import cv2
import asyncio
import yaml
import os
from core.event_bus import bus

class SayraEyes:
    def __init__(self):
        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        
        # Load Haar Cascade for Face Detection (Lightweight, CPU friendly)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.camera_index = 0 # Default Webcam

    def check_presence(self):
        """Checks if a face is visible via Webcam"""
        try:
            cap = cv2.VideoCapture(self.camera_index)
            
            if not cap.isOpened():
                return False

            # Capture single frame
            ret, frame = cap.read()
            cap.release() # Release immediately to save resource

            if not ret:
                return False

            # Convert to Grayscale (Faster processing)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect Faces
            # MODIFICATION: Increased minNeighbors from 4 to 5 for stricter detection
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
            
            # Agar face list empty nahi hai, matlab Boss wahan hai
            return len(faces) > 0

        except Exception as e:
            # print(f"[Eyes Error]: {e}")
            return False

class PresenceMonitor:
    def __init__(self):
        self.eyes = SayraEyes()
        self.is_present = False
        
        # --- NEW: Stability Buffer ---
        self.missed_frames = 0
        # 4 checks * 5 seconds interval = 20 seconds buffer before marking 'Away'
        self.AWAY_THRESHOLD = 4 

    async def start(self):
        print("[SAYRA]: Vision System Active (Stable Monitoring)")
        
        while True:
            # Check presence
            currently_present = await asyncio.get_event_loop().run_in_executor(None, self.eyes.check_presence)
            
            if currently_present:
                # CASE 1: Face Detected
                # Reset missed counter immediately because user is clearly here
                self.missed_frames = 0
                
                if not self.is_present:
                    # User was marked away, now returned
                    self.is_present = True
                    await bus.emit("USER_RETURNED", "Welcome back, Boss.")
                    # print("[SAYRA]: User Detected.")
            
            else:
                # CASE 2: Face NOT Detected
                if self.is_present:
                    # User is currently marked 'Present', so we increment the counter
                    self.missed_frames += 1
                    
                    # Only mark 'Away' if threshold is crossed
                    if self.missed_frames >= self.AWAY_THRESHOLD:
                        self.is_present = False
                        await bus.emit("USER_AWAY", None)
                        # print("[SAYRA]: User Away.")
            
            # Har 5 second mein check karo (Low CPU usage)
            await asyncio.sleep(5)

# Global Starter
async def start_presence_monitor():
    monitor = PresenceMonitor()
    await monitor.start()