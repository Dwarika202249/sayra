import asyncio
import datetime
import yaml
from core.event_bus import bus

class FeederProtocol:
    def __init__(self):
        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        
        self.meal_times = self.config['protocols']['feeder_protocol']['reminders']
        self.water_interval = self.config['protocols']['feeder_protocol']['water_interval']

    async def start(self):
        print("[SAYRA]: Feeder Protocol Active (Tracking Meals & Water)")
        
        # Water Timer loop
        asyncio.create_task(self.water_loop())
        
        # Meal Timer loop
        while True:
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")
            
            if current_time in self.meal_times:
                await bus.emit("SYSTEM_ALERT", f"Boss, Fuel Check. It's {current_time}. Eat something dense.")
                # Is message ke baad 60 sec wait taaki spam na ho
                await asyncio.sleep(60)
                
            await asyncio.sleep(30)

    async def water_loop(self):
        while True:
            # Minutes to Seconds convert
            await asyncio.sleep(self.water_interval * 60)
            await bus.emit("SYSTEM_ALERT", "Hydration Check. Drink water.")

async def start_feeder():
    feeder = FeederProtocol()
    await feeder.start()