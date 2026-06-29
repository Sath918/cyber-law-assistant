from llm_service import generate_ai_response
import os

# Temporarily unset GROQ_API_KEY to force Ollama
if "GROQ_API_KEY" in os.environ:
    del os.environ["GROQ_API_KEY"]
import llm_service
llm_service.GROQ_API_KEY = None

response = generate_ai_response("What is the punishment for cheating by personation?", language_mode="en")
print("Ollama Response:")
print(response)
