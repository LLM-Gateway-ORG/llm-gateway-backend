from .base import BaseLLM
from .huggingface import Huggingface
from .litellm import Litellm
from .ola_krutrim import OlaKrutrim
from .enum import ProviderEnum

def LLM_Factory(platform: str) -> BaseLLM:
    if platform == ProviderEnum.HUGGINGFACE.value:
        return Huggingface()
    elif platform == ProviderEnum.OLA_KRUTRIM.value:
        return OlaKrutrim()
    elif any(platform == e.value for e in ProviderEnum):
        return Litellm()
    raise Exception("Unsupported platform specified.")