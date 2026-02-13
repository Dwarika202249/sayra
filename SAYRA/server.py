import socketio
from aiohttp import web
import asyncio
import yaml
import json
import psutil
import time
import winsound # For Beep Sound
from core.event_bus import bus

# Import Modules
from modules.brain.brain import SayraBrain
from modules.watchers.retina_guard import start_retina_guard
from modules.watchers.circadian_fixer import start_circadian_fixer
from modules.watchers.feeder import start_feeder
from modules.watchers.eyes import start_presence_monitor
from modules.automation.system_control import start_system_control
from modules.speak.mouth import mouth
from modules.hear.ear import ear
from modules.hear.wake_word import wake_listener 
from modules.automation.launcher import launcher
from modules.automation.atmosphere import atmosphere
from modules.tools.web_search import web_searcher
from modules.brain.router import router
from modules.automation.actions import action_engine
from modules.brain.reflex import reflex

# Load Config
with open("config/settings.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# --- SERVER SETUP ---
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

brain = SayraBrain()
shutdown_event = asyncio.Event()

# --- HELPER: COMMAND PROCESSOR ---
# async def process_command_logic(raw_text):
#     text = raw_text.lower().strip()
    
#     # 1. Shutdown Logic
#     if text in ['exit', 'quit', 'bye', 'shutdown']:
#         await bus.emit("SYSTEM_SHUTDOWN")
#         return

#     # 2. Sentry Mode
#     elif "sentry mode on" in text:
#         await bus.emit("ENABLE_SENTRY")
#         await emit_to_ui('bot_message', "Sentry Mode Activated.")

#     elif "sentry mode off" in text:
#         await bus.emit("DISABLE_SENTRY")
#         await emit_to_ui('bot_message', "Sentry Mode Deactivated.")

#     # 3. App Launcher
#     elif text.startswith("open "):
#         app_name = text.replace("open ", "").strip()
#         await launcher.open_app(app_name)
#         await emit_to_ui('bot_message', f"Opening {app_name}...")

#     # 4. Web Search
#     elif text.startswith(("search ", "find ", "google ")):
#         query = text.split(" ", 1)[1]
#         await mouth.speak(f"Searching web for {query}")
#         await emit_to_ui('bot_message', f"Searching: {query}...")
        
#         search_result = await asyncio.get_event_loop().run_in_executor(None, web_searcher.search, query)
        
#         if search_result:
#             context_prompt = f"Data from web:\n{search_result}\n\nUser Question: {query}\nTask: Answer concisely in Hinglish."
#             response = await brain.generate_response(prompt=context_prompt, context="Web Search Mode")
#             await emit_to_ui('bot_message', response)
#             await mouth.speak(response)
#         else:
#             msg = "Sorry Boss, nothing found."
#             await emit_to_ui('bot_message', msg)
#             await mouth.speak(msg)

#     # 5. Atmosphere
#     elif "rest mode" in text:
#         await atmosphere.activate_rest_mode()
#         await emit_to_ui('bot_message', "Rest Mode Activated 🌙")
#     elif "work mode" in text:
#         await atmosphere.activate_work_mode()
#         await emit_to_ui('bot_message', "Work Mode Activated 🚀")
    
#     # 6. Brain (Default)
#     else:
#         response = await brain.generate_response(text)
#         await emit_to_ui('bot_message', response)
#         await mouth.speak(response)

async def process_command_logic(raw_text):
    text = raw_text.strip()
    if not text: return

    # 1. Shutdown Override (Always keep this hardcoded for safety)
    if text.lower() in ['exit', 'quit', 'bye', 'shutdown']:
        await bus.emit("SYSTEM_SHUTDOWN")
        return

    # 2. ROUTING (Dimaag lagao)
    route = await router.determine_intent(text)
    print(f"[Router]: Route Selected -> {route['type']}")

    # 3. EXECUTION BRANCHES
    
    if route['type'] == 'REFLEX':
        # Identity Questions (Direct Answer)
        # Brain style karega is fact ko
        response = await brain.style_fact(route['response']['fact'])
        await emit_to_ui('bot_message', response)
        await mouth.speak(response)

    elif route['type'] == 'COMMAND':
        # Actions (Hands)
        await emit_to_ui('bot_message', f"Executing: {route['intent']}...")
        result_msg = await action_engine.execute(route['intent'], route['entities'])
        
        # Result batao
        await emit_to_ui('bot_message', result_msg)
        await mouth.speak(result_msg)

    else: # type == 'CHAT'
        # Pure Conversation (Brain)
        response = await brain.generate_response(text)
        await emit_to_ui('bot_message', response)
        await mouth.speak(response)

# --- BRIDGE ---
async def emit_to_ui(event_name, data):
    await sio.emit(event_name, data)

# --- HANDLERS ---
async def handle_vision_break(message):
    await emit_to_ui('show_alert', {'type': 'warning', 'message': message})
    await mouth.speak(message)

async def handle_system_alert(message):
    await emit_to_ui('show_alert', {'type': 'info', 'message': message})
    await mouth.speak(message)

# Greeting Logic with Cooldown
last_greet_time = 0
GREET_COOLDOWN = 600 

async def handle_user_returned(message):
    global last_greet_time
    await emit_to_ui('user_status', 'active')
    
    current_time = time.time()
    if (current_time - last_greet_time) > GREET_COOLDOWN:
        await emit_to_ui('bot_message', message)
        await mouth.speak(message)
        last_greet_time = current_time

async def handle_user_away(data):
    await emit_to_ui('user_status', 'away')

async def handle_shutdown(data):
    await emit_to_ui('system_status', 'shutting_down')
    await mouth.speak("Shutting down systems.")
    shutdown_event.set()
    # Force kill server after 2 seconds
    await asyncio.sleep(2)
    import os, signal
    os.kill(os.getpid(), signal.SIGTERM)

bus.subscribe("VISION_BREAK", handle_vision_break)
bus.subscribe("SYSTEM_ALERT", handle_system_alert)
bus.subscribe("USER_RETURNED", handle_user_returned)
bus.subscribe("USER_AWAY", handle_user_away)
bus.subscribe("SYSTEM_SHUTDOWN", handle_shutdown)


# --- SOCKET IO EVENTS ---
@sio.event
async def connect(sid, environ):
    print(f"[Client Connected] SID: {sid}")
    await sio.emit('system_status', 'online', room=sid)
    # FIX: Initial message sent on connection
    await sio.emit('bot_message', "Sayra Online. Listening for 'Hey Sayra'...")

@sio.event
async def user_command(sid, data):
    raw_text = data.get('text', '')
    print(f"[Command Received]: {raw_text}")
    await sio.emit('sayra_state', 'processing')
    try:
        await process_command_logic(raw_text)
    except Exception as e:
        print(f"[Error]: {e}")
    await sio.emit('sayra_state', 'idle')

@sio.event
async def voice_trigger(sid):
    # Manual Click Trigger Logic
    # Yahan bhi handshake use karenge to be safe
    wake_listener.pause()
    await sio.emit('sayra_state', 'listening')
    
    voice_text = await asyncio.get_event_loop().run_in_executor(None, ear.listen)
    
    if voice_text:
        await sio.emit('user_transcription', voice_text)
        await sio.emit('sayra_state', 'processing')
        await process_command_logic(voice_text)
    
    await sio.emit('sayra_state', 'idle')
    wake_listener.resume()

# --- BACKGROUND TASKS ---
async def monitor_vitals():
    print("[SAYRA]: Vitals Monitor Started.")
    while True:
        try:
            battery = psutil.sensors_battery()
            percent = battery.percent if battery else 100
            vitals = {
                'cpu': psutil.cpu_percent(interval=None),
                'ram': psutil.virtual_memory().percent,
                'battery': percent,
                'power': 'Unknown'
            }
            await sio.emit('system_vitals', vitals)
        except: pass
        await asyncio.sleep(2)

async def start_wake_word_detection():
    print("[SAYRA]: Wake Word Detection Started.")
    await asyncio.sleep(2)
    
    while True:
        # Loop mic read
        triggered = await asyncio.get_event_loop().run_in_executor(None, wake_listener.listen)
        
        if triggered:
            print("[WakeWord]: Triggered! Handing over to Ear...")
            
            # --- THE HANDSHAKE PROTOCOL ---
            
            # 1. Release Mic
            wake_listener.pause()
            
            # 2. Feedback (Sound + Visual)
            await emit_to_ui('sayra_state', 'listening')
            try:
                winsound.Beep(1000, 200) # Ting Sound
            except: pass
            
            # 3. Ear Listen (Ab Ear mic le sakta hai)
            voice_text = await asyncio.get_event_loop().run_in_executor(None, ear.listen)
            
            # 4. Process
            if voice_text:
                await emit_to_ui('user_transcription', voice_text)
                await emit_to_ui('sayra_state', 'processing')
                await process_command_logic(voice_text)
            
            # 5. Reset UI
            await emit_to_ui('sayra_state', 'idle')
            
            # 6. Re-acquire Mic (Resume Wake Word)
            wake_listener.resume()
            
        await asyncio.sleep(0.05) # Tiny sleep to prevent CPU burn

async def start_background_tasks():
    vision_interval = config['protocols']['retina_guard']['interval_minutes']
    
    asyncio.create_task(start_retina_guard(vision_interval))
    asyncio.create_task(start_circadian_fixer())
    asyncio.create_task(start_presence_monitor())
    asyncio.create_task(start_system_control())
    asyncio.create_task(start_feeder())
    asyncio.create_task(monitor_vitals())
    asyncio.create_task(start_wake_word_detection())
    
    print("[SAYRA]: All Background Protocols Started.")

if __name__ == '__main__':
    print("[SAYRA SERVER]: Starting on http://localhost:8080")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(start_background_tasks())
    
    try:
        web.run_app(app, port=8080, loop=loop)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        wake_listener.cleanup()