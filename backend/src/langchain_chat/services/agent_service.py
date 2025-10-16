from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from django.conf import settings
from ..models import ChatSession, Message, AgentStep, ToolExecution
from ..tools.registry import get_registry
from django.utils import timezone
import logging
import json

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, session: ChatSession):
        self.session = session
        self.llm = self._initialize_llm()
        self.registry = get_registry()
    
    def _initialize_llm(self) -> ChatOllama:
        """Initialize LLM with all session parameters."""
        kwargs = {
            'model': self.session.model,
            'base_url': settings.OLLAMA_BASE_URL,
            'temperature': self.session.temperature or 0.7,
        }
        
        # Add optional parameters if set
        if self.session.top_k is not None:
            kwargs['top_k'] = self.session.top_k
        if self.session.top_p is not None:
            kwargs['top_p'] = self.session.top_p
        if self.session.repeat_penalty is not None:
            kwargs['repeat_penalty'] = self.session.repeat_penalty
        if self.session.seed is not None:
            kwargs['seed'] = self.session.seed
        if self.session.num_predict is not None:
            kwargs['num_predict'] = self.session.num_predict
        if self.session.num_ctx is not None:
            kwargs['num_ctx'] = self.session.num_ctx
        
        return ChatOllama(**kwargs)
    
    def run(self, user_input: str, max_tools: int = 10) -> str:
        """
        Run agent with tools (blocking).
        
        Args:
            user_input: User's question
            max_tools: Maximum tools to give agent (prevents context overload)
        """
        # Get relevant tools using semantic search
        if self.session.tools_enabled:
            # User specified which tools to use
            tools = self.registry.get_tools(self.session.tools_enabled)
        else:
            # Auto-select relevant tools based on query
            tools = self.registry.get_relevant_tools(
                query=user_input,
                max_tools=max_tools
            )
        
        logger.info(f"Using {len(tools)} tools: {[t.name for t in tools]}")
        
        if not tools:
            # No tools, use basic LLM
            return self.llm.invoke(user_input).content
        
        executor = self._create_executor(tools)
        
        try:
            result = executor.invoke({"input": user_input})
            self._save_steps(result.get('intermediate_steps', []), user_input)
            return result["output"]
        except Exception as e:
            logger.error(f"Agent failed: {e}", exc_info=True)
            return f"I encountered an error: {str(e)}"
    
    def stream(self, user_input: str, max_tools: int = 10):
        """Stream agent responses with tool events (for SSE)."""
        # Get relevant tools
        if self.session.tools_enabled:
            tools = self.registry.get_tools(self.session.tools_enabled)
        else:
            tools = self.registry.get_relevant_tools(
                query=user_input,
                max_tools=max_tools
            )
        
        if not tools:
            # No tools, stream basic LLM
            for chunk in self.llm.stream(user_input):
                if chunk.content:
                    yield {"type": "token", "content": chunk.content}
            return
        
        executor = self._create_executor(tools)
        
        try:
            # For streaming with tools, we need to use a different approach
            # Since astream_events is async, we'll use the blocking version
            # and yield the final result in chunks
            result = executor.invoke({"input": user_input})
            
            # Save steps
            self._save_steps(result.get('intermediate_steps', []), user_input)
            
            # Stream the output
            output = result["output"]
            # Split into words for streaming effect
            words = output.split()
            for i, word in enumerate(words):
                if i < len(words) - 1:
                    yield {"type": "token", "content": word + " "}
                else:
                    yield {"type": "token", "content": word}
        
        except Exception as e:
            logger.error(f"Streaming failed: {e}", exc_info=True)
            yield {"type": "error", "message": str(e)}
    
    def _create_executor(self, tools):
        """Create AgentExecutor with ReAct pattern."""
        prompt = PromptTemplate.from_template("""Answer the following questions as best you can. You have access to the following tools:

{{tools}}

CRITICAL: You MUST use tools to answer questions. Do NOT explain how to find information - USE THE TOOLS DIRECTLY!

Examples:
- Question: "What time is it?" → Action: get_current_time (DO NOT explain timezones!)
- Question: "What is 25 * 4?" → Action: calculator, Action Input: "25 * 4" (DO NOT calculate in your head!)
- Question: "Square root of 81?" → Action: calculator, Action Input: "81 ** 0.5" (USE THE TOOL!)

Use the following format:

Question: the input question you must answer
Thought: I need to use a tool to get the answer
Action: the action to take, should be one of [{{tool_names}}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT: Always use tools when available. Never explain how to find information - just use the tool and give the result!

Begin!

Question: {{input}}
Thought:{{agent_scratchpad}}""".format(system_prompt=self.session.system_prompt))
        
        agent = create_react_agent(self.llm, tools, prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=getattr(settings, 'AGENT_VERBOSE', True),
            max_iterations=getattr(settings, 'AGENT_MAX_ITERATIONS', 5),
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
    
    def _save_steps(self, steps, user_input):
        """Save agent steps to database for debugging."""
        if not steps:
            return
        
        # Find the last AI message for this session
        last_message = Message.objects.filter(
            session=self.session,
            role='ai'
        ).order_by('-created_at').first()
        
        if not last_message:
            # Create a placeholder message
            last_message = Message.objects.create(
                session=self.session,
                role='ai',
                content=f"Processing: {user_input}"
            )
        
        for i, (action, observation) in enumerate(steps, 1):
            AgentStep.objects.create(
                session=self.session,
                message=last_message,
                step_number=i,
                thought=f"Using {action.tool}",
                action=action.tool,
                action_input=str(action.tool_input),
                observation=str(observation)
            )
            
            ToolExecution.objects.create(
                session=self.session,
                message=last_message,
                tool_name=action.tool,
                tool_input=action.tool_input if isinstance(action.tool_input, dict) else {"input": str(action.tool_input)},
                tool_output={'result': str(observation)},
                status='success',
                completed_at=timezone.now()
            )
