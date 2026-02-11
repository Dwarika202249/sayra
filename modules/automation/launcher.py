import subprocess
import yaml
import pyautogui
import asyncio
import os
from modules.speak.mouth import mouth

class AppLauncher:
    def __init__(self):
        try:
            with open("config/apps.yaml", "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
            self.app_map = self.config.get('apps', {})
        except FileNotFoundError:
            self.app_map = {}
            print("[Launcher]: apps.yaml not found. Using fallback only.")

    async def open_app(self, app_name):
        app_name = app_name.lower().strip()
        
        # Strategy 1: YAML Lookup (Fastest)
        if app_name in self.app_map:
            path = self.app_map[app_name]
            try:
                # subprocess.Popen is non-blocking
                subprocess.Popen(path, shell=True)
                await mouth.speak(f"Opening {app_name}")
                return
            except Exception as e:
                print(f"[Launcher Error]: {e}")

        # Strategy 2: Windows Start Menu Fallback
        await mouth.speak(f"Searching for {app_name}")
        await self.fallback_search(app_name)

    async def fallback_search(self, app_name):
        """Simulates User action: Press Win -> Type -> Enter"""
        # Give control back to UI
        pyautogui.press('win')
        await asyncio.sleep(0.5) # Wait for menu animation
        
        pyautogui.write(app_name, interval=0.05)
        await asyncio.sleep(0.5) # Wait for search results
        
        pyautogui.press('enter')

# Global Instance
launcher = AppLauncher()