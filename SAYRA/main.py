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
from modules.watchers.eyes import start_presence_monitor
from modules.automation.system_control import start_system_control
from modules.automation.launcher import launcher
from modules.automation.atmosphere import atmosphere
from modules.tools.web_search import web_searcher

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
    
async def handle_user_returned(message):
    """Jab Boss wapas aayein"""
    # await mouth.speak(message)
    print(f"\n[SAYRA - WELCOME]: {message}")

async def sayra_shell():
    """Interactive loop for Dwarika to talk to Sayra"""
    print(f"\nSAYRA v0.1 Online | Mode: {config['identity']['mode']}")
    print("Type 'exit' to shutdown or just talk to me.")
    
    while True:
        # print("\nBoss: ", end="", flush=True)
        user_input = await asyncio.get_event_loop().run_in_executor(None, input, "Boss: ")
        
        processed_input = user_input.lower().strip()
        
        if processed_input in ['exit', 'quit', 'bye']:
            await bus.emit("SYSTEM_SHUTDOWN")
            break
        
         # Command parsing mein add karenge:
        elif "sentry mode on" in processed_input or "enable security" in processed_input:
            await bus.emit("ENABLE_SENTRY")
            continue

        elif "sentry mode off" in processed_input or "disable security" in processed_input: 
            await bus.emit("DISABLE_SENTRY")
            continue
        
        # Pattern: "open <app_name>"
        elif processed_input.startswith("open "):
            app_name = processed_input.replace("open ", "").strip()
            await launcher.open_app(app_name)
            continue
        
        # --- WEB SEARCH COMMANDS ---
        # Pattern: "search <query>" or "google <query>"
        elif processed_input.startswith(("search ", "find ", "google ")):
            # 1. Extract Query
            query = processed_input.split(" ", 1)[1]
            await mouth.speak(f"Searching web for {query}")
            
            # 2. Perform Search (Run in executor because DDG is sync)
            search_result = await asyncio.get_event_loop().run_in_executor(None, web_searcher.search, query)
            
            if search_result:
                print(f"\n{search_result}") # Raw data for you to see
                
                # 3. Feed to Brain for Natural Answer
                # Hum Brain ko bolenge: "Ye data hai, ab user ke sawal ka jawab do"
                context_prompt = f"Here is the latest data from the web:\n{search_result}\n\nUser Question: {query}\nTask: Answer the user based on this data in Hinglish. Be concise."
                
                response = await brain.generate_response(prompt=context_prompt, context="Web Search Mode")
                await mouth.speak(response)
                
            else:
                await mouth.speak("Sorry Boss, I couldn't find anything relevant.")
            
            continue

        # --- ATMOSPHERE COMMANDS ---
        elif "rest mode" in processed_input:
            await atmosphere.activate_rest_mode()
            continue
            
        elif "work mode" in processed_input or "focus mode" in processed_input:
            await atmosphere.activate_work_mode()
            continue
        
        elif "set brightness to" in processed_input:
            try:
                # Extract number from input
                level = int(''.join(filter(str.isdigit, processed_input)))
                await atmosphere.set_brightness_level(level)
            except ValueError:
                await mouth.speak("Please provide a valid brightness level.")
            continue
            
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
            # print(f"SAYRA: {response}")
            


async def main():
    # 1. Subscribe to Core Events
    bus.subscribe("VISION_BREAK", handle_vision_break)
    bus.subscribe("SYSTEM_ALERT", handle_system_alert)
    bus.subscribe("USER_RETURNED", handle_user_returned)
    bus.subscribe("SYSTEM_SHUTDOWN", handle_shutdown)
    
    # 2. Start Background Watchers (Retina Guard, etc.)
    # interval hum config se uthayenge
    vision_interval = config['protocols']['retina_guard']['interval_minutes']
    
    # Create tasks
    tasks = [
        asyncio.create_task(start_retina_guard(vision_interval)),
        asyncio.create_task(start_circadian_fixer()),
        asyncio.create_task(start_presence_monitor()),
        asyncio.create_task(start_system_control()),
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