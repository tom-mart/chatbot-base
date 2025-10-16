from ninja import Schema
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class MessageSchema(Schema):
    id: UUID
    role: str
    content: str
    created_at: datetime

class ChatSessionSchema(Schema):
    #Complete session details for GET/POST responses.
    # Core fields
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    
    # LLM Configuration
    model: str
    system_prompt: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    repeat_penalty: Optional[float] = None
    seed: Optional[int] = None
    num_predict: Optional[int] = None
    num_ctx: Optional[int] = None
    
    # Agent Configuration
    tools_enabled: Optional[List[str]] = None
    rag_enabled: bool
    rag_sources: Optional[List] = None
    
    # Status & Metadata
    is_active: bool
    show_in_history: bool
    total_tokens: int
    total_cost: float
    metadata: Optional[dict] = None

class ChatRequestSchema(Schema):
    message: str
    # Allow per-request overrides
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class ChatResponseSchema(Schema):
    session_id: UUID
    message: str
    role: str
    timestamp: datetime

class SessionCreateSchema(Schema):
    title: Optional[str] = "New Conversation"
    system_prompt: Optional[str] = "You are a helpful AI assistant."
    model: Optional[str] = None  # Uses default from settings
    
    # Sampling parameters
    temperature: Optional[float] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    repeat_penalty: Optional[float] = None
    seed: Optional[int] = None
    
    # Generation parameters
    num_predict: Optional[int] = None
    num_ctx: Optional[int] = None
    max_tokens: Optional[int] = None
    
    # Tool configuration
    tools_enabled: Optional[List[str]] = None  # e.g., ["calculator", "get_weather"]

class SessionListSchema(Schema):
    #Response schema for session list.
    id: UUID
    title: str
    model: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    show_in_history: bool
    # Optional: include message count or last message preview
    message_count: Optional[int] = None
    first_message: Optional[str] = None

class SessionHistoryQuerySchema(Schema):
    #Query parameters for filtering session history.
    show_in_history: Optional[bool] = None  # Filter by show_in_history
    is_active: Optional[bool] = None  # Filter by is_active
    limit: Optional[int] = 50  # Max sessions to return
    offset: Optional[int] = 0  # Pagination offset