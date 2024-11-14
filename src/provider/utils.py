from provider.chat import BaseLLM, LLM_Factory

def chat_completion(api_key: str, provider: str) -> BaseLLM:
    llm = LLM_Factory(provider)
    llm.api_key = api_key
    return llm