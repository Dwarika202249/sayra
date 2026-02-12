import asyncio
import datetime
import os
import platform
import yaml
from core.event_bus import bus

class CircadianFixer:
    def __init__(self):
        # Config load karte hain
        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        
        self.bedtime = self.config['protocols']['circadian_fixer']['bedtime']  # "23:00"
        self.warning_time = self.config['protocols']['circadian_fixer']['shutdown_warning'] # "22:45"
        self.forced_lock = self.config['protocols']['circadian_fixer']['forced_lock']

    async def start(self):
        print(f"[SAYRA]: Circadian Protocol Active (Bedtime: {self.bedtime})")
        
        while True:
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")

            # Check for Warning
            if current_time == self.warning_time:
                # Sirf ek baar trigger ho is minute me, isliye sleep logic niche hai
                await bus.emit("SYSTEM_ALERT", f"Boss, {self.bedtime} baje shutdown hoga. Wrap up karo.")

            # Check for Bedtime
            if current_time == self.bedtime:
                if self.forced_lock:
                    await bus.emit("SYSTEM_ALERT", "Bedtime Reached. Initiating Lockdown.")
                    await asyncio.sleep(5) # 5 sec warning
                    self.execute_shutdown()
            
            # Har 30 second me check karega
            await asyncio.sleep(30)

    def execute_shutdown(self):
        system_os = platform.system()
        
        # Windows Shutdown Logic
        if system_os == "Windows":
            # /s = shutdown, /f = force apps to close, /t 0 = immediately
            # Boss, ye command ruthless hai. Save your work manually!
            # os.system("shutdown /s /f /t 0")
            print("[SAYRA]: Shutdown command executed. (Simulated for safety)")
        
        # Linux/Mac Support (Just in case)
        elif system_os == "Linux" or system_os == "Darwin":
            os.system("shutdown now")

# Global starter function for main.py
async def start_circadian_fixer():
    fixer = CircadianFixer()
    await fixer.start()