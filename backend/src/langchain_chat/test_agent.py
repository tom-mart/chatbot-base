#!/usr/bin/env python
"""Test script for agent functionality"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from langchain_chat.models import ChatSession
from langchain_chat.services.agent_service import AgentService
from django.contrib.auth.models import User

print("=" * 60)
print("Testing Agent Implementation")
print("=" * 60)

# Get or create a test user
user, created = User.objects.get_or_create(
    username='test_agent_user',
    defaults={'email': 'test@example.com'}
)
if created:
    user.set_password('testpass123')
    user.save()
    print(f"✓ Created test user: {user.username}")
else:
    print(f"✓ Using existing test user: {user.username}")

# Test 1: Create session with calculator tool
print("\n" + "=" * 60)
print("Test 1: Calculator Tool")
print("=" * 60)
session1 = ChatSession.objects.create(
    user=user,
    title="Calculator Test",
    model="qwen2.5:latest",
    tools_enabled=["calculator"]
)
print(f"✓ Created session: {session1.title}")

try:
    service1 = AgentService(session1)
    result1 = service1.run("What is 25 * 4?")
    print(f"✓ Agent response: {result1}")
    print(f"✓ Expected: Should mention 100")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Create session with time tool
print("\n" + "=" * 60)
print("Test 2: Time Tool")
print("=" * 60)
session2 = ChatSession.objects.create(
    user=user,
    title="Time Test",
    model="qwen2.5:latest",
    tools_enabled=["get_current_time"]
)
print(f"✓ Created session: {session2.title}")

try:
    service2 = AgentService(session2)
    result2 = service2.run("What time is it?")
    print(f"✓ Agent response: {result2}")
    print(f"✓ Expected: Should mention current date/time")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Create session with multiple tools
print("\n" + "=" * 60)
print("Test 3: Multiple Tools")
print("=" * 60)
session3 = ChatSession.objects.create(
    user=user,
    title="Multi-Tool Test",
    model="qwen2.5:latest",
    tools_enabled=["calculator", "get_current_time"]
)
print(f"✓ Created session: {session3.title}")

try:
    service3 = AgentService(session3)
    result3 = service3.run("What time is it and what is 100 * 50?")
    print(f"✓ Agent response: {result3}")
    print(f"✓ Expected: Should mention time and 5000")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Session without tools (basic LLM)
print("\n" + "=" * 60)
print("Test 4: No Tools (Basic LLM)")
print("=" * 60)
session4 = ChatSession.objects.create(
    user=user,
    title="No Tools Test",
    model="qwen2.5:latest",
    tools_enabled=[]
)
print(f"✓ Created session: {session4.title}")

try:
    service4 = AgentService(session4)
    result4 = service4.run("Hello, how are you?")
    print(f"✓ Agent response: {result4}")
    print(f"✓ Expected: Should respond normally without tools")
except Exception as e:
    print(f"✗ Error: {e}")

# Check tool executions
print("\n" + "=" * 60)
print("Tool Execution Summary")
print("=" * 60)
from langchain_chat.models import ToolExecution
executions = ToolExecution.objects.all()
print(f"Total tool executions: {executions.count()}")
for execution in executions:
    print(f"  - {execution.tool_name}: {execution.status}")

print("\n" + "=" * 60)
print("Tests Complete!")
print("=" * 60)
