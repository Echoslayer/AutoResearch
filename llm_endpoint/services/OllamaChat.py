from .ChatModel import ChatModel
import requests
import json
import threading
import time
from tqdm import tqdm
import os
from dotenv import load_dotenv

class OllamaChat(ChatModel):
    base_url = None
    model = None

    @classmethod
    def initialize(cls, model: str = None, base_url: str = None) -> None:
        load_dotenv('.env.local')
        cls.base_url = base_url or os.getenv('OLLAMA_URL', 'http://localhost:11434')
        cls.model = model or os.getenv('OLLAMA_MODEL')

    @classmethod
    def generate(cls, text: str, temperature: float = 0, max_tokens: int = 1024, num_ctx: int = 16382) -> str:
        if not cls.model:
            raise ValueError("OllamaChat not initialized. Call initialize() first.")
        
        url = f"{cls.base_url}/api/generate"
        payload = {
            "model": cls.model,
            "prompt": text,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "options": {
                "num_ctx": num_ctx
            }
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        # Ollama returns streaming responses, so we need to accumulate them
        full_response = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                response_data = json.loads(decoded_line)
                full_response += response_data.get('response', '')
        
        return full_response.strip()

    @classmethod
    def batch_generate(cls, text_batch: list[str], temperature: float = 0, max_tokens: int = 1024, num_ctx: int = 16382) -> list[str]:
        max_threads = 2  # limit max concurrent threads using model API
        res_l = ['No response'] * len(text_batch)
        thread_l = []

        def __chat(text, temp, res_list, idx):
            res_list[idx] = cls.generate(text, temp, max_tokens, num_ctx)

        for i, text in enumerate(text_batch):
            thread = threading.Thread(target=__chat, args=(text, temperature, res_l, i))
            thread_l.append(thread)
            thread.start()
            while len(thread_l) >= max_threads:
                for t in thread_l:
                    if not t.is_alive():
                        thread_l.remove(t)
                time.sleep(0.3)  # Short delay to avoid busy-waiting

        for thread in tqdm(thread_l):
            thread.join()

        return res_l
