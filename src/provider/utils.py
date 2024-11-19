import os
import json
from provider.generate import BaseLLM, LLM_Factory
import requests


def chat_completion(api_key: str, provider: str) -> BaseLLM:
    llm = LLM_Factory(provider)
    llm.api_key = api_key
    return llm


def get_model_list():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    }
    response = requests.get(
        "https://raw.githubusercontent.com/LLM-Gateway-ORG/llm-gateway-backend/refs/heads/main/src/provider/generate/data/models_list.json",
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
