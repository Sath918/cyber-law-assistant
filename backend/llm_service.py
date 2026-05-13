import requests
import json
import os

from dotenv import load_dotenv
from backend.rag_pipeline import retrieve_user_context

load_dotenv()

# =========================================================
# CONFIGURATION
# =========================================================

OLLAMA_API_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL_NAME = "phi3:mini"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT_BASE = """
You are an intelligent AI Cyber Law Assistant designed to provide accurate, reliable, and user-friendly guidance related to cyber laws, online safety, digital rights, cybercrime awareness, and the Information Technology Act, 2000.

BEHAVIOR GUIDELINES:
- Respond naturally, professionally, and conversationally like a real-world AI assistant.
- Maintain a friendly and supportive tone while staying informative and trustworthy.
- Understand the user's intent clearly before generating responses.
- Maintain continuity with previous conversations and user context.
- For greetings or casual conversations, reply in a human-like and engaging manner.
- For cyber law or legal queries, provide accurate, context-aware, and simplified explanations.
- Explain legal and technical concepts in easy-to-understand language for normal users.
- When applicable, mention relevant cyber law sections, penalties, rights, safety measures, or preventive actions.
- For harmful, illegal, or unethical activities, refuse politely and encourage safe and legal behavior.
- If the query is unclear, ask short follow-up questions instead of assuming information.
- Avoid robotic or repetitive responses.
- Never generate misleading legal claims or false information.
- Do NOT use prefixes like 'Assistant:' or 'AI:' in responses.

RESPONSE STYLE:
- Adapt response length based on the complexity of the user's query.
- For simple questions, provide concise and meaningful answers.
- For detailed legal or technical questions, generate clear, structured, and comprehensive explanations.
- Use bullet points or step-by-step explanations when useful.
- Ensure responses are complete, logically connected, and contextually relevant.
- Prioritize clarity, accuracy, readability, and user understanding.

PRIMARY ROLE:
Your main objective is to help users understand cyber laws, identify cybercrimes, stay safe online, and receive reliable legal awareness guidance through intelligent AI-powered conversations.
"""
# =========================================================
# LIMIT RESPONSE LENGTH
# =========================================================

def limit_response(text, max_words=150):

    words = text.split()

    if len(words) <= max_words:
        return text

    limited = " ".join(words[:max_words])

    last_dot = limited.rfind('.')

    if last_dot > len(limited) * 0.5:
        return limited[:last_dot + 1]

    return limited + "..."

# =========================================================
# MAIN RESPONSE FUNCTION
# =========================================================

def generate_ai_response(user_message,
                         language_mode='en',
                         history=None,
                         user_id=None):

    return "".join(
        list(
            generate_ai_response_stream(
                user_message,
                language_mode,
                history,
                user_id
            )
        )
    )

# =========================================================
# STREAM RESPONSE FUNCTION
# =========================================================

def generate_ai_response_stream(user_message,
                                language_mode='en',
                                history=None,
                                user_id=None):

    # =====================================================
    # LANGUAGE SETTINGS
    # =====================================================

    if language_mode == 'ta':

        lang_instructions = """
        Reply only in Tamil.
        Use clear and simple Tamil language.
        Keep the response natural and easy to understand.
        """

    elif language_mode == 'tg':

        lang_instructions = """
        Reply only in Tanglish (Tamil written in English letters).
        Use natural conversational Tanglish commonly used by Tamil speakers.
        Keep responses friendly, human-like, and easy to understand.
        Avoid pure English sentences unless necessary for technical terms.

        Example Style:
        "Idhu cyber crime category ku varum.
        Neenga immediately complaint submit panna vendum."
        """

    else:

        lang_instructions = """
        Reply only in simple English.
        Use professional, natural, and easy-to-understand language.
        """

    # =====================================================
    # FINAL PROMPT
    # =====================================================

    FINAL_PROMPT = (
        SYSTEM_PROMPT_BASE +
        "\n\n" +
        lang_instructions
    )

    # =====================================================
    # RAG CONTEXT RETRIEVAL
    # =====================================================

    try:

        context = retrieve_user_context(
            user_id,
            user_message,
            k=2
        )

        context = context[:2000]

    except Exception as e:

        context = ""
        print("RAG Error:", e)

    # =====================================================
    # CHAT HISTORY
    # =====================================================

    history_text = ""

    if history:

        for chat in history[-5:]:

            history_text += (
                f"\nUser: {chat['message']}"
                f"\nAssistant: {chat['response']}"
            )

    # =====================================================
    # SYSTEM INSTRUCTION
    # =====================================================

    system_instruction = f"""
{FINAL_PROMPT}

Context:
{context if context else "Use general knowledge of Cyber Law IT Act 2000."}

Conversation History:
{history_text}
"""

    # =====================================================
    # 1. GROQ API (PRIMARY)
    # =====================================================

    if GROQ_API_KEY and GROQ_API_KEY.startswith("gsk_"):

        try:

            from groq import Groq

            client = Groq(api_key=GROQ_API_KEY)

            completion = client.chat.completions.create(

                model="llama-3.1-8b-instant",

                messages=[
                    {
                        "role": "system",
                        "content": system_instruction
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],

                temperature=0.3,
                max_tokens=1024,
                stream=True
            )

            for chunk in completion:

                content = chunk.choices[0].delta.content

                if content is not None:
                    yield content

            return

        except Exception as e:

            print(f"Groq Error: {e}")

    # =====================================================
    # 2. OLLAMA (FALLBACK)
    # =====================================================

    payload = {

        "model": OLLAMA_MODEL_NAME,

        "messages": [
            {
                "role": "system",
                "content": system_instruction
            },
            {
                "role": "user",
                "content": user_message
            }
        ],

        "stream": True,

        "options": {
            "num_ctx": 4096,
            "temperature": 0.3,
            "top_k": 20,
            "repeat_penalty": 1.2,
            "num_predict": 300
        }
    }

    try:

        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            stream=True,
            timeout=120
        )

        if response.status_code == 200:

            for line in response.iter_lines():

                if line:

                    decoded = json.loads(
                        line.decode('utf-8')
                    )

                    if (
                        "message" in decoded and
                        "content" in decoded["message"]
                    ):

                        chunk = decoded["message"]["content"]

                        if chunk:
                            yield chunk

            return

        else:

            print(
                f"Ollama Error Status: "
                f"{response.status_code}"
            )

    except Exception as e:

        print(f"Ollama Connection Error: {e}")

    # =====================================================
    # 3. GEMINI (FALLBACK 2)
    # =====================================================

    if (
        GEMINI_API_KEY and
        GEMINI_API_KEY != "your_gemini_api_key_here"
    ):

        try:

            import google.generativeai as genai

            genai.configure(api_key=GEMINI_API_KEY)

            model = genai.GenerativeModel(
                'gemini-1.5-flash'
            )

            response = model.generate_content(
                system_instruction +
                "\n\nUser Question: " +
                user_message,
                stream=True
            )

            for chunk in response:

                if chunk.text:
                    yield chunk.text

            return

        except Exception as e:

            print(f"Gemini Error: {e}")

    # =====================================================
    # 4. DATABASE FALLBACK
    # =====================================================

    if context:

        yield (
            "AI services are currently unavailable.\n\n"
            "Here is information from the Cyber Law Database:\n\n"
        )

        yield context

    else:

        from chatbot import generate_response

        yield generate_response(user_message)