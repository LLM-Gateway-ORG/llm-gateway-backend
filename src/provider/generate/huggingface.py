from .base import BaseLLM
    
class Huggingface(BaseLLM):
    def __init__(self):
        super().__init__()

    def completion(self, model_name: str, messages: list) -> dict:
        pass