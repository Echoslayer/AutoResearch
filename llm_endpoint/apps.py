from django.apps import AppConfig
from .services.OllamaChat import OllamaChat
from .services.OpenAIChat import OpenAIChat
import os
from dotenv import load_dotenv


class LlmEndpointConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'llm_endpoint'

    def ready(self):
        load_dotenv('.env.local')
        
        # Initialize OllamaChat
        ollama_model = os.getenv('OLLAMA_MODEL')
        ollama_url = os.getenv('OLLAMA_URL')
        OllamaChat.initialize(model=ollama_model, base_url=ollama_url)

        # # Initialize OpenAIChat
        # openai_model = os.getenv('OPENAI_MODEL')
        # openai_api_key = os.getenv('OPENAI_API_KEY')
        # OpenAIChat.initialize(model=openai_model, api_key=openai_api_key)
