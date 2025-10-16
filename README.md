# 🤖 AI Chatbot Base - Production-Ready Foundation

A modern, scalable chatbot application built with **Django**, **Next.js**, and **LangChain**. This project provides a solid foundation for building complex AI-powered conversational applications with tool integration, streaming responses, and intelligent agent capabilities.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-15.5.4-black.svg)
![Django](https://img.shields.io/badge/django-5.2+-green.svg)

---

## ✨ Features

### 🎯 Core Capabilities
- **Multi-Session Chat Management** - Create and manage multiple conversation sessions with independent contexts
- **Real-time Streaming** - Server-Sent Events (SSE) for token-by-token response streaming
- **JWT Authentication** - Secure user authentication with access/refresh token flow
- **LangChain Integration** - Powered by LangChain for advanced AI capabilities
- **Ollama Support** - Local LLM deployment using Ollama models

### 🛠️ Advanced Features
- **Intelligent Agent System** - ReAct pattern implementation with tool calling
- **Tool Registry** - Auto-discovering tool system with semantic search via ChromaDB
- **Scalable Architecture** - Built to handle 100+ tools without context overload
- **Conversation Memory** - Persistent chat history with Django ORM
- **Configurable LLM Parameters** - Fine-tune temperature, top_k, top_p, and more per session
- **Tool Execution Tracking** - Debug and monitor tool usage with detailed logging
- **Agent Step Tracking** - Transparency into agent reasoning and decision-making

### 🎨 Frontend Features
- **Modern UI** - Built with Next.js 15, React 19, and TailwindCSS
- **DaisyUI Components** - Beautiful, accessible UI components
- **Markdown Support** - Rich message rendering with react-markdown
- **Responsive Design** - Mobile-first, works on all devices
- **Dark/Light Mode** - Theme support out of the box

---

## 🏗️ Architecture

```
chatbot/
├── backend/                    # Django REST API
│   └── src/
│       ├── core/              # Django project settings
│       ├── langchain_chat/    # Main chat application
│       │   ├── api.py         # REST endpoints
│       │   ├── models.py      # Database models
│       │   ├── services/      # Business logic
│       │   │   ├── agent_service.py      # Agent orchestration
│       │   │   ├── langchain_service.py  # LangChain integration
│       │   │   └── memory_service.py     # Conversation memory
│       │   └── tools/         # Tool implementations
│       │       ├── registry.py           # Auto-discovery system
│       │       ├── math/                 # Math tools
│       │       ├── time/                 # Time tools
│       │       └── weather/              # Weather tools
│       ├── ollama_service/    # Ollama client wrapper
│       ├── notifications/     # Push notifications (future)
│       └── files/            # File handling (future)
│
└── frontend/                  # Next.js application
    └── src/
        ├── app/              # Next.js 15 app router
        ├── components/       # React components
        ├── contexts/         # React contexts (Auth, etc.)
        └── lib/             # Utilities and API client
```

### Tech Stack

**Backend:**
- Django 5.2+ with Django Ninja (FastAPI-style)
- LangChain + LangGraph for agent orchestration
- ChromaDB for semantic tool search
- Ollama for local LLM inference
- Celery + Redis (for async tasks)
- SQLite (development) / PostgreSQL (production ready)

**Frontend:**
- Next.js 15.5.4 (App Router)
- React 19
- TypeScript
- TailwindCSS + DaisyUI
- Server-Sent Events for streaming

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Ollama installed and running ([Install Ollama](https://ollama.ai))

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend/src
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .env
   source .env/bin/activate  # On Windows: .env\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   # Create .env file in backend/ directory
   echo "OLLAMA_DEFAULT_MODEL=qwen3" > ../.env
   echo "OLLAMA_BASE_URL=http://localhost:11434" >> ../.env
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server:**
   ```bash
   python manage.py runserver
   ```

   Backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local if needed (optional for development)
   ```

4. **Start development server:**
   ```bash
   npm run dev
   ```

   Frontend will be available at `http://localhost:3000`

### Pull Ollama Model

```bash
ollama pull qwen3
# Or use any other model: llama3.2, mistral, etc.
```

---

## 📚 API Documentation

### Authentication

**Obtain JWT Token:**
```bash
POST /api/token/pair
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Chat Endpoints

All chat endpoints require JWT authentication:
```
Authorization: Bearer <access_token>
```

#### Create Session
```bash
POST /api/langchain-chat/sessions
Content-Type: application/json

{
  "title": "My Conversation",
  "model": "qwen3",
  "system_prompt": "You are a helpful assistant.",
  "temperature": 0.7,
  "tools_enabled": ["calculator", "get_current_time"]
}
```

#### Send Message (Blocking)
```bash
POST /api/langchain-chat/sessions/{session_id}/chat
Content-Type: application/json

{
  "message": "What is 25 * 4?"
}
```

#### Send Message (Streaming)
```bash
POST /api/langchain-chat/sessions/{session_id}/chat/stream
Content-Type: application/json

{
  "message": "Tell me a story"
}
```

#### List Sessions
```bash
GET /api/langchain-chat/sessions?limit=50&offset=0
```

#### Get Session Messages
```bash
GET /api/langchain-chat/sessions/{session_id}/messages
```

#### List Available Models
```bash
GET /api/langchain-chat/models
```

---

## 🔧 Configuration

### LLM Parameters (Per Session)

Configure these when creating a session:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | `qwen3` | Ollama model name |
| `temperature` | float | `0.7` | Randomness (0.0-1.0) |
| `max_tokens` | int | `2000` | Max response length |
| `top_k` | int | `40` | Top-k sampling |
| `top_p` | float | `0.9` | Nucleus sampling |
| `repeat_penalty` | float | `1.1` | Repetition penalty |
| `seed` | int | `null` | Random seed for reproducibility |
| `num_predict` | int | `null` | Max tokens to generate |
| `num_ctx` | int | `null` | Context window size |

### Agent Configuration

Set in `backend/src/core/settings.py`:

```python
# Agent behavior
AGENT_VERBOSE = True  # Enable detailed logging
AGENT_MAX_ITERATIONS = 5  # Max tool calls per query
MAX_CONTEXT_MESSAGES = 10  # Conversation history limit
```

### Environment Variables

**Backend (.env):**
```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=qwen3

# Agent Settings
AGENT_VERBOSE=true
AGENT_MAX_ITERATIONS=5
MAX_CONTEXT_MESSAGES=10

# LangChain (Optional)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
```

**Frontend (.env.local):**
```bash
# API URL (optional, uses relative URLs by default)
NEXT_PUBLIC_API_URL=
```

---

## 🛠️ Building Custom Tools

### 1. Create Tool File

Create a new file in `backend/src/langchain_chat/tools/<category>/`:

```python
# backend/src/langchain_chat/tools/weather/weather_tool.py
from langchain_core.tools import BaseTool
from typing import Optional

class WeatherTool(BaseTool):
    name: str = "get_weather"
    description: str = "Get current weather for a location. Input should be a city name."
    
    def _run(self, location: str) -> str:
        """Get weather for location."""
        # Your implementation here
        return f"Weather in {location}: Sunny, 72°F"
    
    async def _arun(self, location: str) -> str:
        """Async version."""
        return self._run(location)

# Create instance for auto-discovery
get_weather = WeatherTool()
```

### 2. Tool Auto-Discovery

The tool registry automatically discovers all tools in subdirectories. No registration needed!

### 3. Use in Session

```python
session = ChatSession.objects.create(
    user=user,
    title="Weather Chat",
    tools_enabled=["get_weather"]  # Enable your tool
)
```

### 4. Semantic Tool Selection

Leave `tools_enabled` empty for automatic tool selection:

```python
session = ChatSession.objects.create(
    user=user,
    title="Smart Chat",
    tools_enabled=[]  # Agent auto-selects relevant tools
)
```

The agent uses ChromaDB to semantically match tools to queries!

---

## 🧪 Testing

### Test Agent System

```bash
cd backend/src
python test_agent.py
```

This tests:
- Calculator tool
- Time tool
- Multiple tools
- Basic LLM (no tools)

### Manual Testing

```bash
# Test authentication
curl -X POST http://localhost:8000/api/token/pair \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Test chat
curl -X POST http://localhost:8000/api/langchain-chat/sessions/{session_id}/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is 5 * 5?"}'
```

---

## 📊 Database Models

### ChatSession
Stores conversation sessions with LLM configuration:
- User association
- Model selection
- System prompt
- LLM parameters (temperature, top_k, etc.)
- Enabled tools
- Metadata and tracking

### Message
Individual messages in conversations:
- Role (human/ai/system/tool)
- Content
- Token counts
- Tool calls
- Parent-child relationships (branching)
- User feedback

### ToolExecution
Tracks tool usage for debugging:
- Tool name and inputs
- Outputs and status
- Execution time
- Error handling

### AgentStep
Records agent reasoning:
- Step-by-step thoughts
- Actions taken
- Observations
- Debugging transparency

---

## 🚢 Production Deployment

### Backend

1. **Update settings:**
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['your-domain.com']
   SECRET_KEY = 'your-secure-secret-key'
   ```

2. **Use PostgreSQL:**
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'chatbot_db',
           'USER': 'chatbot_user',
           'PASSWORD': 'secure_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

3. **Collect static files:**
   ```bash
   python manage.py collectstatic
   ```

4. **Use Gunicorn:**
   ```bash
   gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
   ```

### Frontend

1. **Build for production:**
   ```bash
   npm run build
   ```

2. **Start production server:**
   ```bash
   npm start
   ```

3. **Or use with Nginx:**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
       
       location /api/ {
           proxy_pass http://localhost:8000;
       }
   }
   ```

---

## 🔐 Security Considerations

- **JWT Tokens:** Access tokens expire after 1 day, refresh tokens after 7 days
- **CORS:** Configure `ALLOWED_HOSTS` and CORS settings in production
- **Secret Key:** Use strong, unique secret keys
- **Environment Variables:** Never commit `.env` files
- **User Authentication:** All chat endpoints require authentication
- **SQL Injection:** Protected by Django ORM
- **XSS:** Protected by React's automatic escaping

---

## 🎯 Use Cases

This chatbot base is perfect for building:

- **Customer Support Bots** - With tool integration for ticket systems
- **Personal Assistants** - Calendar, email, task management tools
- **Educational Platforms** - Math, science, language learning
- **Data Analysis Bots** - Connect to databases and APIs
- **Code Assistants** - Execute code, search documentation
- **Research Tools** - Web search, paper retrieval, summarization

---

## 🛣️ Roadmap

- [ ] RAG (Retrieval-Augmented Generation) support
- [ ] File upload and processing
- [ ] Voice input/output
- [ ] Multi-modal support (images, PDFs)
- [ ] Conversation branching UI
- [ ] Tool marketplace
- [ ] Docker compose setup
- [ ] Kubernetes deployment configs
- [ ] WebSocket support
- [ ] Multi-language support

---

## 🤝 Contributing

Contributions are welcome! This is a base project designed to be extended.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **LangChain** - For the powerful agent framework
- **Ollama** - For local LLM inference
- **Django** - For the robust backend framework
- **Next.js** - For the modern React framework
- **ChromaDB** - For semantic search capabilities

---

## 📧 Support

For questions and support:
- Open an issue on GitHub
- Check existing documentation
- Review the code examples

---

## ⚡ Performance Tips

1. **Tool Selection:** Use semantic search to limit tools passed to agent (max 10-15)
2. **Context Window:** Adjust `MAX_CONTEXT_MESSAGES` based on your model
3. **Streaming:** Use streaming endpoints for better UX
4. **Caching:** Implement Redis caching for frequent queries
5. **Model Selection:** Choose appropriate model size for your use case

---

**Built with ❤️ for the AI community**

Start building your next AI-powered application today! 🚀
