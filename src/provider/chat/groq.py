from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from .base import BaseLLM


class GroqAILLM(BaseLLM):
    """
    Models List (Chat Completion) :=
    - https://console.groq.com/docs/models
    - https://console.groq.com/settings/limits
    """

    def __init__(self):
        super().__init__()

    def load_model(self, model_name: str):
        if not self._api_key:
            raise ValueError("Groq API Key Not Set")
        try:
            self.model = ChatGroq(
                temperature=0,
                groq_api_key=self._api_key,
                model_name=model_name,
            )
        except Exception as e:
            raise RuntimeError(f"Error role Groq model: {str(e)}")

    def format_messages(self, messages: list) -> str:
        return [
            (msg["role"] if msg["role"] != "user" else "human", msg["content"])
            for msg in messages
        ]

    async def chat(self, messages: list):
        if not self.model:
            raise RuntimeError("Model not loaded. Call `load_model()` first.")
        try:
            prompt = ChatPromptTemplate.from_messages(self.format_messages(messages))
            chain = prompt | self.model

            for chunk in chain.stream({"input": ""}):
                yield chunk.content

        except Exception as e:
            raise RuntimeError(f"Error during chat completion: {str(e)}")
