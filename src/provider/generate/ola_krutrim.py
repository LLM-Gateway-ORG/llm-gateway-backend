from .base import BaseLLM
from krutrim_cloud import KrutrimCloud


class OlaKrutrim(BaseLLM):
    def __init__(self) -> None:
        super().__init__()
        self.client = None
    
    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, api_key: str) -> None:
        self._api_key = api_key
        self.client = KrutrimCloud(api_key=api_key)

    def completion(self, model_name: str, messages: list) -> dict:
        if not self.client:
            raise Exception("Client is not initialized. Please set the API key.")
        try:
            response = self.client.chat.completions.create(
                model=model_name, messages=messages
            )
            return response.model_dump()
        except Exception as e:
            raise Exception(f"Ola Krutrim completion error: {str(e)}")

    def async_completion(self, model_name: str, messages: list):
        if not self.client:
            raise Exception("Client is not initialized. Please set the API key.")
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True
            )
            for chunk in response:
                yield chunk
        except Exception as e:
            raise Exception(f"Ola Krutrim async completion error: {str(e)}")
