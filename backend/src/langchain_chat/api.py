from ninja import Router
from ninja_jwt.authentication import JWTAuth
from uuid import UUID
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.http import StreamingHttpResponse
from .models import ChatSession, Message
from .schemas import MessageSchema, ChatSessionSchema, ChatRequestSchema, ChatResponseSchema, SessionCreateSchema, SessionListSchema, SessionHistoryQuerySchema
from .services.langchain_service import LangchainService
from .services.memory_service import DjangoMessageHistory
from .services.agent_service import AgentService
from typing import List
import json
import logging

logger = logging.getLogger(__name__)
router = Router(tags=['Langchain Chat'], auth=JWTAuth())

@router.post("/sessions", response=ChatSessionSchema)
def create_session(request, payload: SessionCreateSchema):
    #Create a new chat session with full LLM configuration.
    session = ChatSession.objects.create(
        user=request.auth,  # Required - from JWT authentication
        title=payload.title,
        model=payload.model or settings.OLLAMA_DEFAULT_MODEL,
        system_prompt=payload.system_prompt,
        # LLM parameters
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        top_k=payload.top_k,
        top_p=payload.top_p,
        repeat_penalty=payload.repeat_penalty,
        seed=payload.seed,
        num_predict=payload.num_predict,
        num_ctx=payload.num_ctx,
        # Agent configuration
        tools_enabled=payload.tools_enabled or []
    )
    
    # Add initial system message
    Message.objects.create(
        session=session,
        role='system',
        content=payload.system_prompt
    )
    
    return session

@router.post("/sessions/{session_id}/chat", response=ChatResponseSchema)
def chat(request, session_id: UUID, payload: ChatRequestSchema):
    # Send a message and get AI response.
    # Get session - filtered by user for security
    session = get_object_or_404(ChatSession, id=session_id, user=request.auth)
    
    # Save user message
    Message.objects.create(
        session=session,
        role='human',
        content=payload.message
    )
    
    # Get conversation history
    memory = DjangoMessageHistory(session_id=str(session_id))
    messages = [
        {'role': msg.type, 'content': msg.content}
        for msg in memory.messages
    ]
    
    # Use per-request overrides if provided, otherwise use session defaults
    temperature = payload.temperature if payload.temperature is not None else session.temperature
    max_tokens = payload.max_tokens if payload.max_tokens is not None else session.max_tokens
    
    # Always use agent (it will auto-select tools or use none)
    agent_service = AgentService(session)
    response_content = agent_service.run(payload.message)
    
    # Save AI response
    ai_message = Message.objects.create(
        session=session,
        role='ai',
        content=response_content,
        model=session.model
    )
    
    return {
        'session_id': session.id,
        'message': response_content,
        'role': 'ai',
        'timestamp': ai_message.created_at
    }

@router.post("/sessions/{session_id}/chat/stream")
def chat_stream(request, session_id: UUID, payload: ChatRequestSchema):
    # Stream chat responses token by token using SSE (Server-Sent Events).
    # Get session - filtered by user for security
    session = get_object_or_404(ChatSession, id=session_id, user=request.auth)
    
    # Save user message
    user_msg = Message.objects.create(
        session=session,
        role='human',
        content=payload.message
    )
    
    # Get conversation history
    memory = DjangoMessageHistory(session_id=str(session_id))
    messages = [
        {'role': msg.type, 'content': msg.content}
        for msg in memory.messages
    ]
    
    # Use per-request overrides if provided
    temperature = payload.temperature if payload.temperature is not None else session.temperature
    
    def event_stream():
        #Generator for SSE events.
        try:
            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'session_id': str(session_id)})}\n\n"
            
            full_response = ""
            
            # Always use agent (it will auto-select tools or use none)
            agent_service = AgentService(session)
            for event in agent_service.stream(payload.message):
                if event.get('type') == 'token':
                    full_response += event.get('content', '')
                    yield f"data: {json.dumps({'type': 'content', 'content': event.get('content', '')})}\n\n"
                elif event.get('type') == 'error':
                    yield f"data: {json.dumps(event)}\n\n"
                    return
            
            # Save AI response
            ai_message = Message.objects.create(
                session=session,
                role='ai',
                content=full_response,
                model=session.model
            )
            
            # Send end event with final message
            yield f"data: {json.dumps({'type': 'end', 'message': {'id': str(ai_message.id), 'content': full_response, 'created_at': ai_message.created_at.isoformat()}})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response

@router.get("/sessions/{session_id}", response=ChatSessionSchema)
def get_session(request, session_id: UUID):
    #Get session details - user can only access their own sessions.
    return get_object_or_404(ChatSession, id=session_id, user=request.auth)

@router.delete("/sessions/{session_id}")
def delete_session(request, session_id: UUID):
    #Delete a session - user can only delete their own sessions.
    session = get_object_or_404(ChatSession, id=session_id, user=request.auth)
    session.delete()
    return {"success": True}

@router.get("/sessions/{session_id}/messages", response=List[MessageSchema])
def get_session_messages(request, session_id: UUID):
    #Get all messages for a session.
    session = get_object_or_404(ChatSession, id=session_id, user=request.auth)
    return session.messages.all()

@router.get("/sessions", response=List[SessionListSchema])
def list_sessions(
    request,
    show_in_history: bool = None,
    is_active: bool = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Get user's session history with optional filtering.
    Returns sessions ordered by most recently updated first.
    """
    from django.db.models import Count
    
    # Start with user's sessions only
    queryset = ChatSession.objects.filter(user=request.auth)
    
    # Apply filters if provided
    if show_in_history is not None:
        queryset = queryset.filter(show_in_history=show_in_history)
    
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    
    # Explicitly order by most recent first
    queryset = queryset.order_by('-updated_at')
    
    # Annotate with message count
    queryset = queryset.annotate(message_count=Count('messages'))
    
    # Apply pagination
    sessions = list(queryset[offset:offset + limit])
    
    # Add first message to each session
    for session in sessions:
        first_msg = session.messages.filter(role='human').order_by('created_at').first()
        session.first_message = first_msg.content[:100] if first_msg else None
    
    return sessions

@router.patch("/sessions/{session_id}/visibility")
def update_session_visibility(request, session_id: UUID, show_in_history: bool):
    session = get_object_or_404(ChatSession, id=session_id, user=request.auth)
    session.show_in_history = show_in_history
    session.save(update_fields=['show_in_history', 'updated_at'])
    
    return {"success": True, "show_in_history": session.show_in_history}

@router.get("/models")
def list_models(request):
    #Get list of available Ollama models.
    from ollama_service.ollama_client import OllamaClient
    
    try:
        client = OllamaClient()
        models_response = client.client.list()
        
        # Extract model names from the response
        models = []
        if hasattr(models_response, 'models'):
            models = [
                {
                    'name': model.model,
                    'size': getattr(model, 'size', None),
                    'modified_at': getattr(model, 'modified_at', None)
                }
                for model in models_response.models
            ]
        
        return {'models': models}
    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        return {'models': [], 'error': str(e)}