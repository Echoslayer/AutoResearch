from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.OllamaChat import OllamaChat
from .services.OpenAIChat import OpenAIChat
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

class ChatAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Generate text using selected chat provider",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['provider', 'prompt'],
            properties={
                'provider': openapi.Schema(type=openapi.TYPE_STRING, description="Chat provider (ollama or openai)", default="ollama"),
                'prompt': openapi.Schema(type=openapi.TYPE_STRING, description="Input prompt for generation"),
                'temperature': openapi.Schema(type=openapi.TYPE_NUMBER, description="Temperature for text generation", default=0),
                'max_tokens': openapi.Schema(type=openapi.TYPE_INTEGER, description="Maximum number of tokens to generate", default=1024),
                'num_ctx': openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of context tokens (for Ollama)", default=16382),
                'base_url': openapi.Schema(type=openapi.TYPE_STRING, description="Base URL for the API (optional)"),
                'model': openapi.Schema(type=openapi.TYPE_STRING, description="Model to use (optional)")
            }
        ),
        responses={200: openapi.Response("Generated text")}
    )
    def post(self, request):
        provider = request.data.get('provider', 'ollama')
        prompt = request.data.get('prompt')
        temperature = request.data.get('temperature', 0)
        max_tokens = request.data.get('max_tokens', 1024)
        num_ctx = request.data.get('num_ctx', 16382)
        base_url = request.data.get('base_url')
        model = request.data.get('model')

        if not provider or not prompt:
            return Response({"error": "Provider and prompt are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if provider.lower() == 'ollama':
                base_url = base_url or os.getenv('OLLAMA_URL')
                model = model or os.getenv('OLLAMA_MODEL')
                OllamaChat.initialize(model=model, base_url=base_url)
                generated_text = OllamaChat.generate(prompt, temperature, max_tokens, num_ctx)
            elif provider.lower() == 'openai':
                api_key = base_url or os.getenv('OPENAI_API_KEY')
                model = model or os.getenv('OPENAI_MODEL')
                OpenAIChat.initialize(model=model, api_key=api_key)
                generated_text = OpenAIChat.generate(prompt, temperature, max_tokens)
            else:
                return Response({"error": "Invalid provider"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"generated_text": generated_text}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BatchGenerateAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Batch generate text using selected chat provider",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['provider', 'prompt_batch'],
            properties={
                'provider': openapi.Schema(type=openapi.TYPE_STRING, description="Chat provider (ollama or openai)", default="ollama"),
                'prompt_batch': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description="List of input prompts for generation"),
                'temperature': openapi.Schema(type=openapi.TYPE_NUMBER, description="Temperature for text generation", default=0),
                'max_tokens': openapi.Schema(type=openapi.TYPE_INTEGER, description="Maximum number of tokens to generate", default=1024),
                'num_ctx': openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of context tokens (for Ollama)", default=16382),
                'base_url': openapi.Schema(type=openapi.TYPE_STRING, description="Base URL for the API (optional)", default=None),
                'model': openapi.Schema(type=openapi.TYPE_STRING, description="Model to use (optional)", default=None)
            }
        ),
        responses={200: openapi.Response("List of generated texts")}
    )
    def post(self, request):
        provider = request.data.get('provider', 'ollama')
        prompt_batch = request.data.get('prompt_batch')
        temperature = request.data.get('temperature', 0)
        max_tokens = request.data.get('max_tokens', 1024)
        num_ctx = request.data.get('num_ctx', 16382)
        base_url = request.data.get('base_url')
        model = request.data.get('model')

        if not provider or not prompt_batch or not isinstance(prompt_batch, list):
            return Response({"error": "provider must be specified and prompt_batch must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if provider.lower() == 'ollama':
                base_url = base_url or os.getenv('OLLAMA_URL')
                model = model or os.getenv('OLLAMA_MODEL')
                OllamaChat.initialize(model=model, base_url=base_url)
                generated_texts = OllamaChat.batch_generate(prompt_batch, temperature, max_tokens, num_ctx)
            elif provider.lower() == 'openai':
                api_key = base_url or os.getenv('OPENAI_API_KEY')
                model = model or os.getenv('OPENAI_MODEL')
                OpenAIChat.initialize(model=model, api_key=api_key)
                generated_texts = OpenAIChat.batch_generate(prompt_batch, temperature, max_tokens)
            else:
                return Response({"error": "Invalid provider"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"generated_texts": generated_texts}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
