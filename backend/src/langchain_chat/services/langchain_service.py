from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import List,Dict, Any, Optional

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class LangchainService:
    def __init__(self, model: str = None, temperature: float = 0.7):
        self.model = model or settings.OLLAMA_DEFAULT_MODEL
        self.temperature = temperature
        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> ChatOllama:
        logger.info(f"Initializing ChatOllama with base_url: {settings.OLLAMA_BASE_URL}, model: {self.model}")
        return ChatOllama(
            model=self.model,
            temperature=self.temperature,
            base_url=settings.OLLAMA_BASE_URL
        )
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        langchain_messages = self._convert_to_langchain_messages(messages)
        response = self.llm.invoke(langchain_messages)
        return response.content

    def stream(self, messages: List[Dict[str, str]]):
        langchain_messages = self._convert_to_langchain_messages(messages)
        for chunk in self.llm.stream(langchain_messages):
            if chunk.content:
                yield chunk.content
    
    def _convert_to_langchain_messages(self, messages: List[Dict[str, str]]):
        langchain_messages = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                langchain_messages.append(HumanMessage(content=content))
        
        return langchain_messages