import screen_brightness_control as sbc
import webbrowser
import pyautogui
import asyncio
from modules.speak.mouth import mouth

class Atmosphere:
    def __init__(self):
        # Default Lofi Girl Playlist or Video
        self.lofi_url = "https://www.youtube.com/watch?v=jfKfPfyJRdk"

    async def activate_rest_mode(self):
        await mouth.speak("Activating Rest Mode.")
        
        # 1. Dim Brightness
        try:
            current = sbc.get_brightness()
            # Fade effect (Optional, direct set is faster)
            sbc.set_brightness(30) 
            print("[Atmosphere]: Brightness set to 30%")
        except Exception as e:
            print(f"[Brightness Error]: {e}")

        # 2. Play Music (Minimized)
        webbrowser.open(self.lofi_url)
        
        # Wait for browser to open then Minimize
        await asyncio.sleep(3) 
        # Win+Down minimizes active window
        pyautogui.hotkey('win', 'down')
        # Do it twice to ensure full minimization if it wasn't maximized
        await asyncio.sleep(0.2)
        pyautogui.hotkey('win', 'down')

    async def activate_work_mode(self):
        await mouth.speak("Back to work. Focus settings applied.")
        
        # 1. Restore Brightness
        try:
            sbc.set_brightness(90)
            print("[Atmosphere]: Brightness set to 90%")
        except Exception as e:
            print(f"[Brightness Error]: {e}")
            
        # Note: Closing the specific YouTube tab programmatically is hard 
        # without browser extensions or selenium. 
        # For now, we leave it to the user to close music manually.
        
    async def set_brightness_level(self, level: int):
    # Set brightness dynamically based on user input (0-100).
    
        try:
            # Validation
            if not 0 <= level <= 100:
                await mouth.speak("Brightness level must be between 0 and 100.")
                return
            
            sbc.set_brightness(level)
            print(f"[Atmosphere]: Brightness set to {level}%")
            await mouth.speak(f"Brightness set to {level} percent.")
            
        except Exception as e:
            print(f"[Brightness Error]: {e}")
            await mouth.speak("Unable to change brightness.")

# Global Instance
atmosphere = Atmosphere()