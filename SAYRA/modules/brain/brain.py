import ollama
from groq import Groq
import yaml
import os
from dotenv import load_dotenv
from modules.brain.memory import memory
from modules.brain.reflex import reflex  # NEW IMPORT

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
        Hybrid Flow: Reflex -> Memory -> LLM
        """
        
        # --- LAYER 1: REFLEX SYSTEM (The Truth) ---
        reflex_data = reflex.check_reflex(prompt)
        
        if reflex_data:
            # Reflex match gaya! Ab LLM se bas is fact ko 'Hinglish' mein convert karwayenge.
            # Context bleeding impossible hai kyunki hum explicitly fact de rahe hain.
            print(f"[Brain]: Reflex Triggered -> {reflex_data['type']}")
            return await self.style_fact(reflex_data['fact'])

        # --- LAYER 2: DEEP THINKING (The Logic) ---
        # Agar reflex nahi hai, to purana process follow karo
        
        # 1. Recall
        past_memories = memory.recall(prompt)
        
        # 2. Select Model & Query
        if self.should_use_cloud(prompt):
            response = await self.query_groq(prompt, past_memories, context)
        else:
            response = await self.query_ollama(prompt, past_memories, context)

        # 3. Save Memory (Only specific non-reflex interactions)
        if len(prompt.split()) > 2:
            memory.save_memory(prompt, source="user")
        
        return response

    async def style_fact(self, fact):
        """
        Takes a raw fact (e.g., 'You are Dwarika') and converts it to Sayra's personality via LLM.
        """
        style_prompt = f"""
        You are SAYRA. 
        TASK: Rewrite the following FACT in Hinglish (Hindi+English) with respect and loyalty.
        FACT: "{fact}"
        
        User is 'Boss'. Do not change the meaning of the fact. Just add personality.
        """
        try:
            # Is chote task ke liye Local Model best hai
            res = ollama.chat(model=self.local_model, messages=[
                {'role': 'user', 'content': style_prompt}
            ])
            return res['message']['content']
        except:
            return fact # Fallback to raw fact if LLM fails

    def should_use_cloud(self, prompt):
        keywords = ['interview', 'architecture', 'anxiety', 'salary', 'future', 'code', 'plan', 'complex']
        return any(word in prompt.lower() for word in keywords)

    async def query_ollama(self, prompt, memories, context):
        # Dynamic Profile Load
        profile = reflex.profile 
        
        system_instructions = f"""
        ### IDENTITY (ABSOLUTE TRUTH) ###
        Name: {profile['bot_name']}
        Role: {profile['bot_role']}
        User: {profile['user_name']} (Boss)
        
        ### INSTRUCTIONS ###
        - Speak in {profile['language_style']}
        - Use MEMORIES as reference data only.
        - Be concise.
        """

        full_user_message = ""
        if memories:
            full_user_message += f"### MEMORIES ###\n{memories}\n\n"
        if context:
            full_user_message += f"### CONTEXT ###\n{context}\n\n"
            
        full_user_message += f"### QUERY ###\n{prompt}"

        try:
            response = ollama.chat(model=self.local_model, messages=[
                {'role': 'system', 'content': system_instructions},
                {'role': 'user', 'content': full_user_message}
            ])
            return response['message']['content']
        except Exception as e:
            return f"Thinking error: {e}"

    async def query_groq(self, prompt, memories, context):
        # Similar logic for cloud
        profile = reflex.profile 
        system_instructions = f"You are {profile['bot_name']}. User is {profile['user_name']}. Speak in Hinglish."
        
        user_content = f"Query: {prompt}"
        if memories: user_content = f"Memories: {memories}\n\n{user_content}"

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": user_content}
                ],
                model=self.cloud_model,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return "Cloud error."