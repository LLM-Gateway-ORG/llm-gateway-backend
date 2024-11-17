from abc import ABC, abstractmethod

class BaseLLM(ABC):
    def __init__(self) -> None:
        super().__init__()
        self._api_key = None
        
    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("API Key Not Found")
        self._api_key = api_key

    @abstractmethod
    def completion(self, model_name: str, messages: list) -> dict:
        pass