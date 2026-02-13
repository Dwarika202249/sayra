import yaml
import json
import ollama
from modules.brain.reflex import reflex

class SemanticRouter:
    def __init__(self):
        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.model = config['brain']['ollama']['model']

    async def determine_intent(self, text):
        """
        Decides: Is this a Command or Chat?
        Returns: {'type': 'COMMAND'|'CHAT', 'intent': '...', 'entities': {...}}
        """
        text = text.lower().strip()

        # --- LAYER 1: REFLEX (Super Fast Regex) ---
        # Identity Checks
        reflex_resp = reflex.check_reflex(text)
        if reflex_resp:
            return {'type': 'REFLEX', 'response': reflex_resp}

        # Simple Commands (Keywords)
        if text.startswith(("play ", "chalao ", "listen ", "bajaao ")):
            song = text.replace("play ", "").replace("chalao ", "").replace("listen ", "").replace("bajaao ", "").strip()
            return {'type': 'COMMAND', 'intent': 'MUSIC_PLAY', 'entities': {'song': song}}

        if text.startswith(("open ", "launch ")):
            app = text.replace("open ", "").replace("launch ", "").strip()
            return {'type': 'COMMAND', 'intent': 'OPEN_APP', 'entities': {'app': app}}

        if "screenshot" in text:
            return {'type': 'COMMAND', 'intent': 'SYSTEM_CONTROL', 'entities': {'action': 'screenshot'}}

        # --- LAYER 2: SEMANTIC LLM (Smart Routing) ---
        # Agar keyword match nahi hua, to LLM se pucho
        # "Is user trying to perform an action or just chatting?"
        
        system_prompt = """
        You are the Action Planner for Sayra OS.
        Break down the user's input into a JSON LIST of commands.
        
        AVAILABLE INTENTS:
        1. FILE_OPERATION: move/copy/delete files. Entities: action, target, source, destination.
        2. MUSIC_PLAY: Play songs. Entities: song.
        3. OPEN_APP: Launch apps. Entities: app.
        4. SYSTEM_CONTROL: volume_up, volume_down, mute, screenshot, shutdown. Entities: action.
        5. WEB_SEARCH: Google search. Entities: query.
        6. CHAT: General conversation (Use this only if no other intent matches).

        RULES:
        - If the user asks for multiple things (e.g., "Play music AND open notepad"), return MULTIPLE command objects in the list.
        - Return ONLY valid JSON.

        EXAMPLES:
        Input: "Play Believer and then open Notepad"
        Output: {
            "tasks": [
                {"intent": "MUSIC_PLAY", "entities": {"song": "Believer"}},
                {"intent": "OPEN_APP", "entities": {"app": "Notepad"}}
            ]
        }
        
        Input: "Move all pdfs to documents and take a screenshot"
        Output: {
            "tasks": [
                {"intent": "FILE_OPERATION", "entities": {"action": "move", "target": "*.pdf", "source": "downloads", "destination": "documents"}},
                {"intent": "SYSTEM_CONTROL", "entities": {"action": "screenshot"}}
            ]
        }
        """
        
        try:
            # Use Ollama to classify (Force JSON mode if possible, else parse)
            response = ollama.chat(model=self.model, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"Input: {text}"}
            ], format='json') # 'json' format is supported in newer Ollama versions
            
            result = json.loads(response['message']['content'])
            
            # Standardization: Ensure we always return a list wrapper
            tasks = result.get('tasks', [])
            
            # Agar LLM ne single object diya galti se, to list bana do
            if isinstance(result, dict) and 'tasks' not in result and 'intent' in result:
                tasks = [result]
            
            # Agar koi task nahi mila, to CHAT maan lo
            if not tasks:
                return {'type': 'CHAT'}

            # Agar list mein 'CHAT' intent hai, to poora flow CHAT return karega 
            # (unless it's mixed, but usually chat is standalone)
            if len(tasks) == 1 and tasks[0]['intent'] == 'CHAT':
                return {'type': 'CHAT'}

            return {'type': 'BATCH', 'tasks': tasks}

        except Exception as e:
            # Fallback to Chat if routing fails
            print(f"[Router Error]: {e}")
            return {'type': 'CHAT'}

# Global Instance
router = SemanticRouter()