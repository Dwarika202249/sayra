import re
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
        if text.startswith(("play ", "chalao ", "listen ")):
            song = text.replace("play ", "").replace("chalao ", "").replace("listen ", "").strip()
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
        You are the Intent Classifier for Sayra OS.
        Analyze the user input and output a JSON object.
        
        Possible Intents:
        - MUSIC_PLAY (if user wants to hear songs/video)
        - WEB_SEARCH (if user wants to google something)
        - SYSTEM_CONTROL (volume, mute, shutdown)
        - CHAT (general conversation, questions, coding help)
        
        Format:
        {
          "intent": "INTENT_NAME",
          "entities": { "song": "...", "query": "...", "action": "..." }
        }
        """
        
        try:
            # Use Ollama to classify (Force JSON mode if possible, else parse)
            response = ollama.chat(model=self.model, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"Input: {text}"}
            ], format='json') # 'json' format is supported in newer Ollama versions
            
            result = json.loads(response['message']['content'])
            
            if result['intent'] == 'CHAT':
                return {'type': 'CHAT'}
            else:
                return {'type': 'COMMAND', 'intent': result['intent'], 'entities': result.get('entities', {})}

        except Exception as e:
            # Fallback to Chat if routing fails
            print(f"[Router Error]: {e}")
            return {'type': 'CHAT'}

# Global Instance
router = SemanticRouter()