import ollama
from groq import Groq
import yaml
import os
from dotenv import load_dotenv
from modules.brain.memory import memory  # Hippocampus connect kiya

load_dotenv()

class SayraBrain:
    def __init__(self, config_path="config/settings.yaml"):
        with open(config_path, 'r', encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        
        self.local_model = self.config['brain']['ollama']['model']
        self.cloud_model = self.config['brain']['groq']['model']
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    async def generate_response(self, prompt, context=""):
        """
        Main function jo Memory Recall karega, Model select karega, aur Memory Save karega.
        """
        # --- STEP 1: MEMORY RECALL (Yaad karo) ---
        # Sayra check karegi ki user ne pehle is topic par kuch bola hai kya?
        past_memories = memory.recall(prompt)
        
        # Context enhance karte hain memories ke saath
        enhanced_context = context
        if past_memories:
            enhanced_context += f"\n\n[RELEVANT PAST MEMORIES]:\n{past_memories}\n"

        # --- STEP 2: MODEL SELECTION ---
        if self.should_use_cloud(prompt):
            response = await self.query_groq(prompt, enhanced_context)
        else:
            response = await self.query_ollama(prompt, enhanced_context)

        # --- STEP 3: MEMORY STORAGE (Seekho) ---
        # User ki baat ko permanent memory mein daalo
        # (Hum background mein save karte hain taaki response fast rahe)
        memory.save_memory(prompt, source="user")
        
        return response

    def should_use_cloud(self, prompt):
        # Trigger Groq for complex keywords or career/emotional support
        keywords = ['interview', 'architecture', 'anxiety', 'salary', 'future', 'code', 'plan', 'complex']
        return any(word in prompt.lower() for word in keywords)

    async def query_ollama(self, prompt, context):
        # Construct the persona from config
        boss_name = self.config['identity']['boss_name']
        mode = self.config['identity']['mode']
        
        # System Prompt me thoda tweak kiya hai taaki wo Context use kare
        system_prompt = f"""
        You are SAYRA, an advanced AI system built by {boss_name}.
        Your goal is to protect and assist {boss_name}.
        Current Mode: {mode}.
        
        Guidelines:
        1. Address the user as 'Boss'.
        2. Be concise. Use Hinglish (Hindi + English).
        3. Use the [RELEVANT PAST MEMORIES] provided in context to personalize your answer.
        4. Never hallucinate. If you don't know, say 'Data not available'.
        """

        try:
            response = ollama.chat(model=self.local_model, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"Context: {context}\n\nUser: {prompt}"}
            ])
            return response['message']['content']
        except Exception as e:
            print(f"[Ollama Error]: {e}")
            return "Local Brain overheat ho raha hai Boss. Check Ollama."

    async def query_groq(self, prompt, context):
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": "You are SAYRA, Dwarika's executive function. Use Hinglish. Be brutal but empathetic. Use provided memories to maintain continuity."
                    },
                    {
                        "role": "user", 
                        "content": f"Context: {context}\n\nUser: {prompt}"
                    }
                ],
                model=self.cloud_model,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"[Groq Error]: {e}")
            return "Cloud connection lost, Boss."