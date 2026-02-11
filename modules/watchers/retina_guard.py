import asyncio
import pyautogui
from core.event_bus import bus

async def start_retina_guard(interval_mins=20):
    while True:
        await asyncio.sleep(interval_mins * 60)
        # Emit event to the bus
        await bus.emit("VISION_BREAK", "Boss, look away! 20 seconds rest for your eyes.")
        
        # Simple popup (non-intrusive initially, can be upgraded to screen lock)
        pyautogui.alert("Retina Guard: Look 20 feet away for 20 seconds. NOW.")