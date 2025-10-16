from django.db import models
from django.contrib.auth.models import User
import uuid

class ChatSession(models.Model):
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, default="New Conversation")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # LLM Configuration
    model = models.CharField(max_length=100, default="qwen3")
    system_prompt = models.TextField(blank=True, default="You are an Intelligent AI assistant.")
    temperature = models.FloatField(null=True, blank=True, help_text="Temperature (default: 0.8 by Ollama)")
    max_tokens = models.IntegerField(default=2000, null=True, blank=True)
    top_k = models.IntegerField(null=True, blank=True, help_text="Top-k sampling (default: 40)")
    top_p = models.FloatField(null=True, blank=True, help_text="Top-p sampling (default: 0.9)")
    repeat_penalty = models.FloatField(null=True, blank=True, help_text="Repeat penalty (default: 1.1)")
    seed = models.IntegerField(null=True, blank=True, help_text="Random seed for reproducibility")
    num_predict = models.IntegerField(null=True, blank=True, help_text="Max tokens to generate")
    num_ctx = models.IntegerField(null=True, blank=True, help_text="Context window size")
    
    # Agent Configuration
    tools_enabled = models.JSONField(default=list, blank=True)  # List of enabled tool names
    rag_enabled = models.BooleanField(default=False)
    rag_sources = models.JSONField(default=list, blank=True)  # Document IDs or collection names
    
    # Metadata & Tracking
    metadata = models.JSONField(default=dict, blank=True)
    total_tokens = models.IntegerField(default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    show_in_history = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} ({self.id})"
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['user', '-created_at']),
        ]

class Message(models.Model):
    ROLE_CHOICES = [
        ('human', 'Human'),
        ('ai', 'AI'),
        ('system', 'System'),
        ('function', 'Function'),  # For tool responses
        ('tool', 'Tool'),  # For tool calls
    ]
    
    FINISH_REASON_CHOICES = [
        ('stop', 'Stop'),
        ('length', 'Length'),
        ('tool_calls', 'Tool Calls'),
        ('content_filter', 'Content Filter'),
        ('error', 'Error'),
    ]
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # LLM Metadata
    model = models.CharField(max_length=100, blank=True)
    token_count = models.IntegerField(default=0)
    finish_reason = models.CharField(max_length=20, choices=FINISH_REASON_CHOICES, blank=True)
    
    # Tool/Function Calling
    tool_calls = models.JSONField(default=list, blank=True)  # List of tool invocations
    tool_call_id = models.CharField(max_length=100, blank=True)  # For function responses
    
    # Conversation Structure
    parent_message = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='children'
    )  # For branching conversations
    
    # User Feedback
    feedback = models.IntegerField(
        null=True, 
        blank=True,
        choices=[(1, 'Positive'), (-1, 'Negative')]
    )
    feedback_comment = models.TextField(blank=True)
    
    # Error Handling
    error = models.TextField(blank=True)
    
    # Additional Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"{self.role}: {preview}"
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['tool_call_id']),
        ]

class ToolExecution(models.Model):
    """Track individual tool/function executions for debugging and analytics."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='tool_executions')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='tool_executions')
    
    # Tool Details
    tool_name = models.CharField(max_length=100)
    tool_input = models.JSONField()
    tool_output = models.JSONField(null=True, blank=True)
    
    # Execution Metadata
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('success', 'Success'),
            ('error', 'Error'),
        ],
        default='pending'
    )
    error = models.TextField(blank=True)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.tool_name} - {self.status}"
    
    class Meta:
        ordering = ['started_at']

class AgentStep(models.Model):
    #Track agent reasoning steps for transparency and debugging.
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='agent_steps')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='agent_steps')
    
    step_number = models.IntegerField()
    thought = models.TextField()  # Agent's reasoning
    action = models.CharField(max_length=100, blank=True)  # Tool/action taken
    action_input = models.JSONField(null=True, blank=True)
    observation = models.TextField(blank=True)  # Result of action
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Step {self.step_number}: {self.action or 'thinking'}"
    
    class Meta:
        ordering = ['step_number']
        unique_together = ['message', 'step_number']