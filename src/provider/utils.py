import os
import json
from provider.generate import BaseLLM, LLM_Factory


def chat_completion(api_key: str, provider: str) -> BaseLLM:
    llm = LLM_Factory(provider)
    llm.api_key = api_key
    return llm


def get_model_list():
    with open(os.path.join(os.getcwd(), "src/provider/generate/data/models_list.json"), "r") as f:
        return json.load(f)
