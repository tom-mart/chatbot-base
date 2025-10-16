# Ollama API Cheatsheet
Base URL: `http://localhost:11434/api`

## 1. Model Operations
### List Local Models
```bash
curl http://localhost:11434/api/tags
```

### Show Model Information
```bash
curl http://localhost:11434/api/show -d '{
  "model": "llama3.1"
}'
```

### Pull a Model
```bash
curl http://localhost:11434/api/pull -d '{
  "name": "llama3.1"
}'
```

### Delete a Model
```bash
curl -X DELETE http://localhost:11434/api/delete -d '{
  "name": "llama3.1"
}'
```

## 2. Generation Endpoints
### Generate Completions
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt": "Why is the sky blue?",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "num_predict": 100
  }
}'
```

### Chat Endpoint
```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.1",
  "messages": [
    { "role": "user", "content": "Hello" }
  ],
  "stream": false
}'
```

### Create Embeddings
```bash
curl http://localhost:11434/api/embeddings -d '{
  "model": "llama3.1",
  "prompt": "The sky is blue because"
}'
```

## 3. Advanced Parameters
Common generation options:
```json
{
  "temperature": 0.8,          // Creativity (0-1)
  "num_predict": 128,           // Max tokens to generate
  "top_k": 40,                  // Top k sampling
  "top_p": 0.9,                 // Nucleus sampling
  "repeat_penalty": 1.1,        // Penalize repetition
  "seed": 42,                   // RNG seed
  "stop": ["\n", "user:"]       // Stop sequences
}
```

## 4. Python Client Example
```python
from ollama import Client

client = Client(host='http://localhost:11434')

# List models
models = client.list()

# Generate text
response = client.generate(model='llama3.1', prompt='Why is the sky blue?')
print(response['response'])

# Chat conversation
chat_response = client.chat(model='llama3.1', messages=[
    {'role': 'user', 'content': 'Hello!'},
    {'role': 'assistant', 'content': 'Hi there!'},
    {'role': 'user', 'content': 'Explain quantum physics simply'}
])
print(chat_response['message']['content'])

# Create embeddings
embedding = client.embeddings(model='llama3.1', prompt='Scientific text')
print(embedding['embedding'])
```

## 5. Response Formats
**Generate Endpoint Response:**
```json
{
  "model": "llama3.1",
  "created_at": "2025-10-13T09:30:00Z",
  "response": "The sky appears blue due to Rayleigh scattering...",
  "done": true
}
```

**Chat Endpoint Response:**
```json
{
  "model": "llama3.1",
  "created_at": "2025-10-13T09:30:00Z",
  "message": {
    "role": "assistant",
    "content": "Quantum physics studies subatomic particles..."
  },
  "done": true
}
```

## 6. Tips & Notes
1. Use `"stream": true` for real-time token streaming
2. For custom models, include `"modelfile": "FROM llama3\n..."` in create requests
3. Set `OLLAMA_HOST` environment variable to change binding address
4. Use `OLLAMA_KEEP_ALIVE` to control how long models stay loaded in memory
