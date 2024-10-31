from provider.chat import BaseLLM, LLM_Factory

def chat_completion(api_key: str, model_name: str, provider: str) -> BaseLLM:
    llm = LLM_Factory(provider)
    llm.api_key = api_key
    llm.load_model(model_name)
    return llm