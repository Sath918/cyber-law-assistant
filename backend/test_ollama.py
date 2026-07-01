import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app.llm_service import generate_ai_response

# Temporarily unset GROQ_API_KEY to force Ollama
if "GROQ_API_KEY" in os.environ:
    del os.environ["GROQ_API_KEY"]
from app import llm_service
llm_service.GROQ_API_KEY = None

response = generate_ai_response("What is the punishment for cheating by personation?", language_mode="en")
print("Ollama Response:")
print(response)
