from abc import ABC, abstractmethod

class BaseLLM(ABC):
    def __init__(self) -> None:
        super().__init__()
        self.model = None
        self._api_key = None
        
    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, api_key: str):
        if not api_key:
            raise ValueError("Groq API Key Not Found")
        self._api_key = api_key

    @abstractmethod
    def load_model(self, model_name: str) -> str:
        pass

    @abstractmethod
    def format_messages(self, messages: list) -> str:
        pass