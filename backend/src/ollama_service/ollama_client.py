import ollama
import logging
from typing import List, Dict, Any, Optional, Iterator, Union
import json
from django.contrib.auth.models import User
from django.conf import settings

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = None, model: str = None, headers: dict = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_DEFAULT_MODEL
        self.client = ollama.Client(
            host=self.base_url,
            timeout=210,
            headers=headers or {})
    
    def is_available(self) -> bool:
        try:
            self.client.list()
            return True
        except Exception as e:
            logger.error(f"Ollama service is not available: {e}")
            return False