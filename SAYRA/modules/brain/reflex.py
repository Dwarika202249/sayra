import json
import os
import re

class ReflexSystem:
    def __init__(self):
        # Load Absolute Truths
        config_path = os.path.join(os.getcwd(), "config", "identity.json")
        with open(config_path, "r", encoding="utf-8") as f:
            self.profile = json.load(f)

    def check_reflex(self, text):
        """
        Input text ko analyze karta hai.
        Agar koi identity/basic sawal hai, to 'Fact' return karta hai.
        Agar nahi, to None return karta hai (matlab LLM handle kare).
        """
        text = text.lower().strip()
        
        # --- PATTERN MATCHING (Regex for robustness) ---
        
        # 1. Self Identity (Who are you?)
        if re.search(r"(who are you|your name|tum kaun ho|aap kaun ho|intro|introduction)", text):
            return {
                "type": "identity_bot",
                "fact": f"My name is {self.profile['bot_name']}. I am a {self.profile['bot_role']} created by {self.profile['user_name']}."
            }

        # 2. User Identity (Who am I?)
        if re.search(r"(who am i|my name|main kaun hoon|do you know me)", text):
            return {
                "type": "identity_user",
                "fact": f"You are {self.profile['user_name']}, my {self.profile['user_role']}."
            }

        # 3. Creator Query
        if re.search(r"(who made you|who created you|creator)", text):
            return {
                "type": "creator_fact",
                "fact": f"I was built by {self.profile['user_name']}."
            }
            
        return None

# Global Instance
reflex = ReflexSystem()