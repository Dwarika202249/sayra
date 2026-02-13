import chromadb
import os
import uuid
import yaml

class SayraMemory:
    def __init__(self):
        # Config load kar rahe hain (Future proofing ke liye)
        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            
        # Persistence setup: Data 'memory_db' folder mein save hoga
        self.db_path = os.path.join(os.getcwd(), "memory_db")
        
        try:
            # PersistentClient data ko disk par save rakhta hai
            self.client = chromadb.PersistentClient(path=self.db_path)
            
            # Collection create ya load karo
            # 'cosine' distance use karenge similarity ke liye
            self.collection = self.client.get_or_create_collection(
                name="sayra_long_term",
                metadata={"hnsw:space": "cosine"}
            )
            print(f"[SAYRA]: Memory System Online ({self.collection.count()} memories)")
            
        except Exception as e:
            print(f"[Memory Error]: {e}")
            self.client = None

    def save_memory(self, text, source="user"):
        """
        Save any text to long-term memory.
        source: 'user' (Boss ne kaha) or 'bot' (Sayra ne kaha)
        """
        if not self.client: return
        
        try:
            # Har memory ko unique ID chahiye
            mem_id = str(uuid.uuid4())
            
            # Metadata help karega baad mein filter karne mein
            meta = {"source": source, "timestamp": "timestamp_here"} # Timestamp logic add kar sakte hain
            
            self.collection.add(
                documents=[text],
                metadatas=[meta],
                ids=[mem_id]
            )
            # print(f"[Memory]: Stored -> '{text[:30]}...'")
            
        except Exception as e:
            print(f"[Memory Save Error]: {e}")

    def recall(self, query, n_results=2):
        """
        Search memory for relevant context based on query.
        """
        if not self.client or self.collection.count() == 0:
            return ""
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Results ko clean string mein convert karo
            memories = results['documents'][0]
            if not memories:
                return ""
                
            print(f"[Memory]: Recalled -> {memories}")
            return "\n".join([f"- {m}" for m in memories])
            
        except Exception as e:
            print(f"[Memory Recall Error]: {e}")
            return ""

# Global Instance
memory = SayraMemory()