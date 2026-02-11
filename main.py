import asyncio
import sys
import os
import yaml
from core.event_bus import bus
from modules.brain.brain import SayraBrain
from modules.watchers.retina_guard import start_retina_guard

# Load Constitution
with open("config/settings.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
    
shutdown_event = asyncio.Event()

# Initialize Brain
brain = SayraBrain()

async def handle_vision_break(message):
    """Retina Guard trigger hone par ye execute hoga"""
    print(f"\n[SAYRA - PROTECTOR]: {message}")
    # Future: Yahan hum TTS module (Mouth) ko call karenge
    # abhi ke liye system alert kafi hai.

async def handle_shutdown(data):
    """Axiom 5: Instant Kill Switch"""
    print(f"\n[SAYRA]: Shutdown signal received. Goodbye, Boss.")
    # Trigger the event to stop the main loop
    shutdown_event.set()

async def sayra_shell():
    """Interactive loop for Dwarika to talk to Sayra"""
    print(f"\nSAYRA v0.1 Online | Mode: {config['identity']['mode']}")
    print("Type 'exit' to shutdown or just talk to me.")
    
    while True:
        user_input = await asyncio.get_event_loop().run_in_executor(None, input, "Boss: ")
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            await bus.emit("SYSTEM_SHUTDOWN")
            break
            
        # Brain processing
        response = await brain.generate_response(user_input)
        print(f"SAYRA: {response}")

async def main():
    # 1. Subscribe to Core Events
    bus.subscribe("VISION_BREAK", handle_vision_break)
    bus.subscribe("SYSTEM_SHUTDOWN", handle_shutdown)
    
    # 2. Start Background Watchers (Retina Guard, etc.)
    # interval hum config se uthayenge
    vision_interval = config['protocols']['retina_guard']['interval_minutes']
    
    # Create tasks
    tasks = [
        asyncio.create_task(start_retina_guard(vision_interval)),
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