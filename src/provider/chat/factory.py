from .base import BaseLLM
from .huggingface import Huggingface
from .litellm import Litellm
from .enum import ProviderEnum

def LLM_Factory(platform: str) -> BaseLLM:
    if platform == ProviderEnum.HUGGINGFACE.value:
        return Huggingface()
    if any(platform == e.value for e in ProviderEnum):
        return Litellm()
    raise Exception("Unsupported platform specified.")