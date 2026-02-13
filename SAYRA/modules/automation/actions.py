import pywhatkit
import pyautogui
import os
import subprocess
import time
import asyncio
from core.event_bus import bus

class ActionEngine:
    def __init__(self):
        # Safety Fail-safe: Mouse ko corner me le jaoge to script ruk jayegi
        pyautogui.FAILSAFE = True

    async def execute(self, intent, entities):
        """
        Router se aayi command ko execute karta hai.
        intent: 'MUSIC_PLAY', 'OPEN_APP', etc.
        entities: {'song': '...'} or {'app': '...'}
        """
        print(f"[ActionEngine]: Executing {intent} with {entities}")

        try:
            if intent == 'MUSIC_PLAY':
                song = entities.get('song')
                if song:
                    # PyWhatKit runs blocking code, so run in executor
                    await asyncio.to_thread(pywhatkit.playonyt, song)
                    return f"Playing {song} on YouTube."

            elif intent == 'WEB_SEARCH':
                query = entities.get('query')
                if query:
                    await asyncio.to_thread(pywhatkit.search, query)
                    return f"Searching Google for {query}."

            elif intent == 'OPEN_APP':
                app = entities.get('app')
                if app:
                    pyautogui.press('win')
                    time.sleep(0.5)
                    pyautogui.write(app)
                    time.sleep(0.5)
                    pyautogui.press('enter')
                    return f"Opening {app}..."
            
            elif intent == 'SYSTEM_CONTROL':
                action = entities.get('action')
                if action == 'volume_up':
                    pyautogui.press('volumeup', presses=5)
                    return "Volume increased."
                elif action == 'volume_down':
                    pyautogui.press('volumedown', presses=5)
                    return "Volume decreased."
                elif action == 'mute':
                    pyautogui.press('volumemute')
                    return "System muted."
                elif action == 'screenshot':
                    img_path = os.path.join("protected", f"screenshot_{int(time.time())}.png")
                    os.makedirs("protected", exist_ok=True)
                    pyautogui.screenshot(img_path)
                    return f"Screenshot saved to {img_path}"

            return "Action executed successfully."

        except Exception as e:
            print(f"[Action Error]: {e}")
            return f"Error executing action: {e}"

# Global Instance
action_engine = ActionEngine()