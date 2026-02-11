import asyncio
import ctypes
import pyautogui
from core.event_bus import bus

class SystemControl:
    def __init__(self):
        self.lock_task = None  # To keep track of the countdown

    async def start(self):
        print("[SAYRA]: System Automation Active (Lock/Wake Ready)")
        # Subscribe to events
        bus.subscribe("USER_AWAY", self.handle_away)
        bus.subscribe("USER_RETURNED", self.handle_returned)
        
        # Keep the module alive
        while True:
            await asyncio.sleep(3600)

    async def handle_away(self, data):
        """Starts a countdown to lock the screen"""
        # Agar pehle se koi countdown chal raha hai to cancel karo (safety)
        if self.lock_task:
            self.lock_task.cancel()
        
        # Start new countdown task
        self.lock_task = asyncio.create_task(self.execute_lock_sequence())

    async def handle_returned(self, data):
        """Cancels lock and wakes screen"""
        # 1. Cancel pending lock
        if self.lock_task:
            self.lock_task.cancel()
            self.lock_task = None
            # Debug msg (optional)
            # print("[SAYRA]: Lock cancelled. Welcome back.")

        # 2. Wake up screen
        # Hum 'shift' key press karenge jo harmless hai par screen jaga degi
        pyautogui.press('space')  # Spacebar press to wake up

    async def execute_lock_sequence(self):
        try:
            print("[SAYRA]: User away. Locking in 10 seconds...")
            await asyncio.sleep(10) # Buffer time
            
            print("[SAYRA]: Locking Workstation.")
            # Windows Lock Command
            ctypes.windll.user32.LockWorkStation()
            
        except asyncio.CancelledError:
            # Ye tab hoga jab aap 10 sec ke andar wapas aa gaye
            print("[SAYRA]: Auto-Lock aborted.")

# Global starter
async def start_system_control():
    control = SystemControl()
    await control.start()