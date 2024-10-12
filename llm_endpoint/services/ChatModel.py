from abc import ABC, abstractmethod

class ChatModel(ABC):
    @abstractmethod
    def initialize(self, model: str, api_key: str) -> None:
        pass

    @abstractmethod
    def generate(self, text: str, temperature: float = 1, max_tokens: int = 250) -> str:
        pass

    @abstractmethod
    def batch_generate(self, text_batch: list[str], temperature: float = 0, max_tokens: int = 250) -> list[str]:
        pass