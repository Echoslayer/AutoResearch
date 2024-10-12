from .ChatModel import ChatModel
import openai

class OpenAIChat(ChatModel):
    model = None
    client = None

    @classmethod
    def initialize(cls, model: str, api_key: str) -> None:
        cls.model = model
        cls.client = openai.OpenAI(api_key=api_key)

    @classmethod
    def generate(cls, text: str, temperature: float = 1, max_tokens: int = 250) -> str:
        if not cls.client or not cls.model:
            raise ValueError("OpenAIChat must be initialized before use.")
        
        response = cls.client.chat.completions.create(
            model=cls.model,
            messages=[{"role": "user", "content": text}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()

    @classmethod
    def batch_generate(cls, text_batch: list[str], temperature: float = 0, max_tokens: int = 250) -> list[str]:
        if not cls.client or not cls.model:
            raise ValueError("OpenAIChat must be initialized before use.")
        
        responses = []
        for text in text_batch:
            response = cls.generate(text, temperature, max_tokens)
            responses.append(response)
        return responses
