
from .base import BaseLLM
from .groq import GroqAILLM
from .enum import ProviderEnum

def LLM_Factory(platform: str) -> BaseLLM:
    if platform == ProviderEnum.GROQ.value:
        return GroqAILLM()
    raise Exception("Unsupported platform specified.")