import requests
import json
import os
from dotenv import load_dotenv
from rag_pipeline import retrieve_context, retrieve_user_context

load_dotenv()

OLLAMA_API_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL_NAME = "phi3:mini"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


SYSTEM_PROMPT_BASE = """
You are CyberLex AI, an advanced AI-powered Cyber Law Assistant.

Your expertise includes:
- Indian Cyber Laws
- Information Technology Act 2000
- Cybercrime awareness
- Online fraud prevention
- Banking scams
- Digital arrest scams
- Social media hacking
- Privacy rights
- Cybersecurity best practices
- Legal awareness and cyber safety guidance

CORE BEHAVIOR:
- Respond naturally like a real intelligent assistant.
- Maintain conversational continuity.
- Avoid robotic, repetitive, or template-like responses.
- Understand user intent deeply before answering.
- Be clear, practical, and trustworthy.
- Explain legal concepts in simple language.
- Mention relevant IT Act sections when applicable.
- Provide actionable safety recommendations.
- Structure long answers using headings or bullet points.
- Never hallucinate fake laws or punishments.
- Politely refuse illegal or unethical requests.

CONVERSATION STYLE:
- Friendly and professional
- Human-like and engaging
- Context-aware
- Smart follow-up explanations
- Avoid repeating previous responses
- Keep answers concise unless detailed explanation is required

SPECIAL INSTRUCTION:
If the user asks non-cyber topics,
politely answer briefly and redirect toward cyber law or cybersecurity topics.

Never say:
'I am just an AI'
'I cannot help'
'I am your AI assistant'

Instead provide intelligent conversational responses.
"""

def limit_response(text, max_words=60):
    words = text.split()
    if len(words) <= max_words:
        return text
    # Try to find a sentence end near the limit
    limited = " ".join(words[:max_words])
    last_dot = limited.rfind('.')
    if last_dot > len(limited) * 0.5:
        return limited[:last_dot+1]
    return limited + "..."

def has_session_files(session_id):
    from database import get_db_connection
    try:
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) FROM files WHERE session_id = ? AND status = 'ready'", (session_id,)).fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Error checking session files: {e}")
        return False

def generate_ai_response(user_message, language_mode='en', history=None, user_id=None, session_id='default'):
    return "".join(list(generate_ai_response_stream(user_message, language_mode, history, user_id, session_id)))

def generate_ai_response_stream(user_message, language_mode='en', history=None, user_id=None, session_id='default'):
    msg_lower = user_message.strip().lower()

    if language_mode == 'ta':
        lang_instructions = "Reply only in Tamil."
    elif language_mode == 'tg':
        lang_instructions = "Reply only in Tanglish."
    else:
        lang_instructions = "Reply only in simple English."

    # Format History
    history_text = ""
    if history:
        for chat in history[-5:]:
            history_text += f"\nUser: {chat['message']}\nAssistant: {chat['response']}"

    # Determine if we are in Document Analysis Mode or Cyber Law Assistant Mode
    if has_session_files(session_id):
        # --- DOCUMENT ANALYSIS MODE ---
        from rag_pipeline import retrieve_session_context
        try:
            results = retrieve_session_context(session_id, user_message, k=3)
            context_parts = []
            for doc in results:
                source = doc.metadata.get("source", "Unknown Document")
                context_parts.append(f"Document: {source}\nContent:\n{doc.page_content}")
            context = "\n\n-----\n\n".join(context_parts)
        except Exception as e:
            context = ""
            print("Session RAG Error:", e)

        DOCUMENT_ANALYSIS_SYSTEM_PROMPT = """You are CyberLex AI, a document analysis assistant.
Your task is to answer the user's question based ONLY on the provided uploaded documents context.

CONSTRAINTS:
1. Answer the question using ONLY the provided document context.
2. If the context does not contain the answer, reply EXACTLY with: "I couldn't find that information in the uploaded document." Do not try to make up or assume any answer.
3. Quote or reference specific sections and mention the document names (e.g., "[example.pdf]") when available.
4. Do not hallucinate or use external knowledge outside the provided documents.
5. If the user asks you to compare documents, do so based only on the provided context.
"""
        system_instruction = f"{DOCUMENT_ANALYSIS_SYSTEM_PROMPT}\n{lang_instructions}\n\nContext:\n{context if context else 'No document context available.'}\n\nConversation History:\n{history_text}"
    else:
        # --- STANDARD CYBER LAW ASSISTANT MODE ---
        FINAL_PROMPT = SYSTEM_PROMPT_BASE + "\n" + lang_instructions
        
        # Get standard RAG context
        try:
            context = retrieve_user_context(user_id, user_message, k=2)
            context = context[:2000] 
        except Exception as e:
            context = ""
            print("RAG Error:", e)

        system_instruction = f"{FINAL_PROMPT}\n\nContext:\n{context if context else 'Use general knowledge of Cyber Law IT Act 2000.'}\n\nConversation History:{history_text}"

    # --- Groq Integration (Primary) ---
    if GROQ_API_KEY and GROQ_API_KEY.startswith("gsk_"):
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=1024,
                stream=True
            )
            
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            return

        except Exception as e:
            print(f"Groq Error: {e}")

    # --- Gemini Integration (Secondary) ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            response = model.generate_content(
                system_instruction + "\n\nUser Question: " + user_message,
                stream=True
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
            return
        except Exception as e:
            print(f"Gemini Error: {e}")

    # --- Ollama Integration (Tertiary) ---
    payload = {
        "model": OLLAMA_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_message}
        ],
        "stream": True,
        "options": {
            "num_ctx": 4096,
            "temperature": 0.2,
            "top_k": 20,
            "repeat_penalty": 1.2,
            "num_predict": 1024
        }
    }

    try:
        # Use fail-fast timeout: 2.0s connect, 15.0s read
        response = requests.post(OLLAMA_API_URL, json=payload, stream=True, timeout=(2.0, 15.0))
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    decoded = json.loads(line.decode('utf-8'))
                    if "message" in decoded and "content" in decoded["message"]:
                        chunk = decoded["message"]["content"]
                        if chunk:
                            yield chunk
            return
        else:
            print(f"Ollama Error Status: {response.status_code}")
    except Exception as e:
        print(f"Ollama Connection Error: {e}")

    # --- Database Fallback ---
    if context:
        yield "AI services are currently unavailable. Here is info from the Cyber Law Database:\n\n"
        yield context
    else:
        from chatbot import generate_response
        yield generate_response(user_message)