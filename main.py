import asyncio
import sys
import os
import yaml
from core.event_bus import bus
from modules.brain.brain import SayraBrain
from modules.watchers.retina_guard import start_retina_guard
from modules.watchers.circadian_fixer import start_circadian_fixer
from modules.speak.mouth import mouth
from modules.hear.ear import ear
from modules.watchers.feeder import start_feeder

# Load Constitution
with open("config/settings.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
    
shutdown_event = asyncio.Event()

# Initialize Brain
brain = SayraBrain()

# --- HANDLERS ---

async def handle_vision_break(message):
    """Retina Guard trigger hone par ye execute hoga"""
    print(f"\n[SAYRA - PROTECTOR]: {message}")
    await mouth.speak(message)
    
async def handle_system_alert(message):
    """General Alerts (Battery, Sleep Warning etc)"""
    await mouth.speak(message)

async def handle_shutdown(data):
    """Axiom 5: Instant Kill Switch"""
    print(f"\n[SAYRA]: Shutdown signal received. Goodbye, Boss.")
    await mouth.speak("Shutting down systems. Goodbye Boss.")
    # Trigger the event to stop the main loop
    shutdown_event.set()

async def sayra_shell():
    """Interactive loop for Dwarika to talk to Sayra"""
    await mouth.speak("Hello Boss, I am Sayra - version zero point one - online and ready to help.")
    print(f"\nSAYRA v0.1 Online | Mode: {config['identity']['mode']}")
    print("Type 'exit' to shutdown or just talk to me.")
    
    while True:
        user_input = await asyncio.get_event_loop().run_in_executor(None, input, "Boss: ")
        
        processed_input = user_input.lower().strip()
        
        if processed_input in ['exit', 'quit', 'bye']:
            await bus.emit("SYSTEM_SHUTDOWN")
            break
            
        # Voice Command Trigger
        elif processed_input == 'listen':
            # Ear activate karo
            voice_text = await asyncio.get_event_loop().run_in_executor(None, ear.listen)
            
            if voice_text:
                print(f"You said: {voice_text}")
                processed_input = voice_text # Voice text ko process karo
            else:
                print("Sayra: Couldn't hear you clearly.")
                continue # Loop wapas start
            
        # Brain Processing (Text or Transcribed Voice)
        if processed_input:
            response = await brain.generate_response(processed_input)
            await mouth.speak(response)
            print(f"SAYRA: {response}")

async def main():
    # 1. Subscribe to Core Events
    bus.subscribe("VISION_BREAK", handle_vision_break)
    bus.subscribe("SYSTEM_ALERT", handle_system_alert)
    bus.subscribe("SYSTEM_SHUTDOWN", handle_shutdown)
    
    # 2. Start Background Watchers (Retina Guard, etc.)
    # interval hum config se uthayenge
    vision_interval = config['protocols']['retina_guard']['interval_minutes']
    
    # Create tasks
    tasks = [
        asyncio.create_task(start_retina_guard(vision_interval)),
        asyncio.create_task(start_circadian_fixer()),
        asyncio.create_task(start_feeder()),
        asyncio.create_task(sayra_shell())
    ]
    
    # 3. Wait until shutdown_event is set
    try:
        await shutdown_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        print("[SAYRA]: Cleaning up resources...")
        for task in tasks:
            task.cancel()
        print("[SAYRA]: Offline completed.")

if __name__ == "__main__":
    asyncio.run(main())