import ollama
from groq import Groq
import yaml
import os
from dotenv import load_dotenv

load_dotenv()

class SayraBrain:
    def __init__(self, config_path="config/settings.yaml"):
        with open(config_path, 'r', encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        
        self.local_model = self.config['brain']['ollama']['model']
        self.cloud_model = self.config['brain']['groq']['model']
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    async def generate_response(self, prompt, context=""):
        # Logic: Simple tasks stay local to save RAM/Privacy
        # Complex tasks or "Career/Emotional" modes use Groq
        
        if self.should_use_cloud(prompt):
            return await self.query_groq(prompt, context)
        else:
            return await self.query_ollama(prompt, context)

    def should_use_cloud(self, prompt):
        # Trigger Groq for complex keywords or career/emotional support
        keywords = ['interview', 'architecture', 'anxiety', 'salary', 'future']
        return any(word in prompt.lower() for word in keywords)

    async def query_ollama(self, prompt, context):
        # Construct the persona from config
        boss_name = self.config['identity']['boss_name']
        mode = self.config['identity']['mode']
        
        # This is the "Soul" of Sayra
        system_prompt = f"""
        You are SAYRA, an advanced AI system built by {boss_name}.
        Your goal is to protect and assist {boss_name}.
        Current Mode: {mode}.
        
        Guidelines:
        1. Address the user as 'Boss'.
        2. Be concise. Use Hinglish (Hindi + English).
        3. If asked about sleep/health, check the config context.
        4. Never hallucinate. If you don't know, say 'Data not available'.
        """

        try:
            response = ollama.chat(model=self.local_model, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"{context}\n\n{prompt}"}
            ])
            return response['message']['content']
        except Exception as e:
            return f"Ollama Error: {e}. Switching to cloud failover..."

    async def query_groq(self, prompt, context):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are SAYRA, Dwarika's executive function. Use Hinglish. Be brutal but empathetic."},
                {"role": "user", "content": f"{context}\n\n{prompt}"}
            ],
            model=self.cloud_model,
        )
        return chat_completion.choices[0].message.content