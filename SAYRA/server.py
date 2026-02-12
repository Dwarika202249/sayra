import socketio
from aiohttp import web
import asyncio
import yaml
import json
from core.event_bus import bus

# Import existing modules
from modules.brain.brain import SayraBrain
from modules.watchers.retina_guard import start_retina_guard
from modules.watchers.circadian_fixer import start_circadian_fixer
from modules.watchers.feeder import start_feeder
from modules.watchers.eyes import start_presence_monitor
from modules.automation.system_control import start_system_control
from modules.speak.mouth import mouth
from modules.hear.ear import ear
from modules.automation.launcher import launcher
from modules.automation.atmosphere import atmosphere
from modules.tools.web_search import web_searcher

# Load Config
with open("config/settings.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# --- SERVER SETUP ---
# CORS allow all (*) kyunki React localhost:5173 pe chalega aur ye localhost:8080 pe
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

# Initialize Brain
brain = SayraBrain()
shutdown_event = asyncio.Event()

# --- THE BRIDGE (Core -> UI) ---
# Jab bhi Event Bus pe kuch ho, use UI pe bhejo

async def emit_to_ui(event_name, data):
    """Bridge function to send data to Frontend"""
    await sio.emit(event_name, {'data': data})
    print(f"[UI-Bridge] Sent {event_name}: {str(data)[:50]}...")

# --- EVENT HANDLERS (System) ---

async def handle_vision_break(message):
    await emit_to_ui('show_alert', {'type': 'warning', 'message': message})
    await mouth.speak(message)

async def handle_system_alert(message):
    await emit_to_ui('show_alert', {'type': 'info', 'message': message})
    await mouth.speak(message)

async def handle_user_returned(message):
    await emit_to_ui('user_status', 'active')
    await emit_to_ui('bot_message', message)
    await mouth.speak(message)

async def handle_user_away(data):
    await emit_to_ui('user_status', 'away')
    # No speaking, silent update

async def handle_shutdown(data):
    await emit_to_ui('system_status', 'shutting_down')
    await mouth.speak("Shutting down systems.")
    shutdown_event.set()

# Subscribe Bridge to Core Events
bus.subscribe("VISION_BREAK", handle_vision_break)
bus.subscribe("SYSTEM_ALERT", handle_system_alert)
bus.subscribe("USER_RETURNED", handle_user_returned)
bus.subscribe("USER_AWAY", handle_user_away)
bus.subscribe("SYSTEM_SHUTDOWN", handle_shutdown)


# --- SOCKET.IO HANDLERS (UI -> Core) ---

@sio.event
async def connect(sid, environ):
    print(f"[Client Connected] SID: {sid}")
    await sio.emit('system_status', 'online', room=sid)
    await sio.emit('bot_message', f"Sayra v0.1 Online. Mode: {config['identity']['mode']}")

@sio.event
async def disconnect(sid):
    print(f"[Client Disconnected] SID: {sid}")

@sio.event
async def user_command(sid, data):
    """
    Main entry point for text commands from React UI
    data = {'text': 'open vs code'}
    """
    raw_text = data.get('text', '').lower().strip()
    print(f"[Command Received]: {raw_text}")
    
    # 1. Emit 'thinking' state to UI
    await sio.emit('sayra_state', 'processing') 

    # 2. Process Command (Logic copied from main.py)
    try:
        # Shutdown
        if raw_text in ['exit', 'quit', 'bye']:
            await bus.emit("SYSTEM_SHUTDOWN")
            return

        # Sentry Mode
        elif "sentry mode on" in raw_text:
            await bus.emit("ENABLE_SENTRY")
            await sio.emit('bot_message', "Sentry Mode Activated.")
        elif "sentry mode off" in raw_text:
            await bus.emit("DISABLE_SENTRY")
            await sio.emit('bot_message', "Sentry Mode Deactivated.")

        # App Launcher
        elif raw_text.startswith("open "):
            app_name = raw_text.replace("open ", "").strip()
            await launcher.open_app(app_name)
            await sio.emit('bot_message', f"Opening {app_name}...")

        # Web Search
        elif raw_text.startswith(("search ", "find ", "google ")):
            query = raw_text.split(" ", 1)[1]
            await mouth.speak(f"Searching web for {query}")
            await sio.emit('bot_message', f"Searching: {query}...")
            
            search_result = await asyncio.get_event_loop().run_in_executor(None, web_searcher.search, query)
            
            if search_result:
                # Brain processing
                context_prompt = f"Data from web:\n{search_result}\n\nUser Question: {query}\nTask: Answer concisely in Hinglish."
                response = await brain.generate_response(prompt=context_prompt, context="Web Search Mode")
                
                await sio.emit('bot_message', response)
                await mouth.speak(response)
            else:
                msg = "Sorry Boss, nothing found."
                await sio.emit('bot_message', msg)
                await mouth.speak(msg)

        # Atmosphere
        elif "rest mode" in raw_text:
            await atmosphere.activate_rest_mode()
            await sio.emit('bot_message', "Rest Mode Activated 🌙")
        elif "work mode" in raw_text:
            await atmosphere.activate_work_mode()
            await sio.emit('bot_message', "Work Mode Activated 🚀")

        # General Brain Query
        else:
            response = await brain.generate_response(raw_text)
            await sio.emit('bot_message', response)
            await mouth.speak(response)

    except Exception as e:
        print(f"[Error Processing Command]: {e}")
        await sio.emit('show_alert', {'type': 'error', 'message': str(e)})

    # 3. Reset State
    await sio.emit('sayra_state', 'idle')

@sio.event
async def voice_trigger(sid):
    """Called when user clicks Mic button in UI"""
    await sio.emit('sayra_state', 'listening')
    voice_text = await asyncio.get_event_loop().run_in_executor(None, ear.listen)
    
    if voice_text:
        await sio.emit('user_transcription', voice_text)
        # Recursively call command handler
        await user_command(sid, {'text': voice_text})
    else:
        await sio.emit('sayra_state', 'idle')

# --- MAIN ENTRY POINT ---

async def start_background_tasks():
    vision_interval = config['protocols']['retina_guard']['interval_minutes']
    
    # Run all watchers
    asyncio.create_task(start_retina_guard(vision_interval))
    asyncio.create_task(start_circadian_fixer())
    asyncio.create_task(start_presence_monitor())
    asyncio.create_task(start_system_control())
    asyncio.create_task(start_feeder())
    print("[SAYRA]: Background Protocols Started.")

if __name__ == '__main__':
    print("[SAYRA SERVER]: Starting on http://localhost:8080")
    
    # Create the App Runner
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Schedule background tasks
    loop.create_task(start_background_tasks())
    
    # Run Server
    web.run_app(app, port=8080, loop=loop)