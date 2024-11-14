from litellm import completion
from .base import BaseLLM

class Litellm(BaseLLM):
    def __init__(self):
        super().__init__()

    def completion(self, model_name: str, messages: list) -> dict:
        try:
            response = completion(
                model=model_name,
                messages=messages,
                api_key=self._api_key,
                timeout=30
            )
            return response.model_dump()
        except Exception as e:
            raise Exception(f"LiteLLM completion error: {str(e)}")
        
    
    async def async_completion(self, model_name: str, messages: list):
        try:
            response = completion(
                model=model_name,
                messages=messages,
                api_key=self._api_key,
                stream=True
            )
            for chunk in response:
                yield chunk
        except Exception as e:
            raise Exception(f"LiteLLM async completion error: {str(e)}")
        
