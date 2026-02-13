import pywhatkit
import pyautogui
import os
import shutil
import glob
import time
import asyncio
from pathlib import Path

class ActionEngine:
    def __init__(self):
        # Safety Fail-safe: Mouse ko corner me le jaoge to script ruk jayegi
        pyautogui.FAILSAFE = True
        
    # User Paths Setup (Windows)
        self.user_home = os.path.expanduser('~')
        self.folders = {
            "downloads": os.path.join(self.user_home, "Downloads"),
            "documents": os.path.join(self.user_home, "Documents"),
            "desktop": os.path.join(self.user_home, "Desktop"),
            "pictures": os.path.join(self.user_home, "Pictures"),
            "music": os.path.join(self.user_home, "Music"),
            "videos": os.path.join(self.user_home, "Videos"),
            "protected": os.path.join(os.getcwd(), "protected") # Project specific folder
        }
        
    def _resolve_path(self, folder_name):
        """Map generic names like 'downloads' to real paths"""
        return self.folders.get(folder_name.lower(), self.folders["documents"])

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
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    img_path = os.path.join(self.folders["pictures"], f"screenshot_{timestamp}.png")
                    pyautogui.screenshot(img_path)
                    return f"Screenshot saved to Pictures folder."
                
                # --- FILE OPERATIONS ---
            elif intent == 'FILE_OPERATION':
                action = entities.get('action') # move, delete, copy
                target = entities.get('target') # *.pdf, filename.txt
                source = entities.get('source', 'downloads') # default to downloads
                dest = entities.get('destination', 'documents')

                src_path = self._resolve_path(source)
                dst_path = self._resolve_path(dest)
                
                # Pattern Matching (e.g., "*.pdf" or "report.docx")
                # Agar user bole "all pdfs", to hum "*.pdf" bana denge logic se
                if "all" in target and "pdf" in target: search_pattern = "*.pdf"
                elif "all" in target and "image" in target: search_pattern = "*.jpg" # Simple assumption
                elif "all" in target and "text" in target: search_pattern = "*.txt"
                else: search_pattern = target

                files_found = glob.glob(os.path.join(src_path, search_pattern))
                
                if not files_found:
                    return f"No files matching '{target}' found in {source}."

                count = 0
                for file in files_found:
                    try:
                        file_name = os.path.basename(file)
                        if action == 'move':
                            shutil.move(file, os.path.join(dst_path, file_name))
                        elif action == 'copy':
                            shutil.copy(file, os.path.join(dst_path, file_name))
                        elif action == 'delete':
                            os.remove(file)
                        count += 1
                    except Exception as e:
                        print(f"File Error: {e}")

                return f"Successfully {action}d {count} files from {source} to {dest}."

            return "Action executed successfully."

        except Exception as e:
            print(f"[Action Error]: {e}")
            return f"Error executing action: {e}"

# Global Instance
action_engine = ActionEngine()