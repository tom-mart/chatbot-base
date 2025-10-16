from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from typing import List

from langchain_chat.models import ChatSession, Message

import logging

logger = logging.getLogger(__name__)

class DjangoMessageHistory(BaseChatMessageHistory):

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session = ChatSession.objects.get(id=session_id)
    
    @property
    def messages(self) -> List[BaseMessage]:
        #Retrieve messages from database as LangChain message objects.
        db_messages = Message.objects.filter(
            session=self.session
        ).order_by('created_at')
        
        langchain_messages = []
        for msg in db_messages:
            if msg.role == 'human':
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == 'ai':
                langchain_messages.append(AIMessage(content=msg.content))
            elif msg.role == 'system':
                langchain_messages.append(SystemMessage(content=msg.content))
        
        return langchain_messages
    
    def add_message(self, message: BaseMessage) -> None:
        #Save a message to the database.
        role_map = {
            'human': 'human',
            'ai': 'ai',
            'system': 'system',
        }
        
        role = role_map.get(message.type, 'human')
        
        Message.objects.create(
            session=self.session,
            role=role,
            content=message.content
        )
    
    def clear(self) -> None:
        #Clear all messages for this session.
        Message.objects.filter(session=self.session).delete()