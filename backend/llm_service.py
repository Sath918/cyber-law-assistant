import os
import traceback

from dotenv import load_dotenv
from groq import Groq

from backend.rag_pipeline import retrieve_user_context

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# =========================================================
# API KEYS
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# =========================================================
# GROQ CLIENT
# =========================================================

client = None

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)

# =========================================================
# SYSTEM PROMPT
# =========================================================

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

# =========================================================
# LIMIT RESPONSE LENGTH
# =========================================================

def limit_response(text, max_words=250):

    words = text.split()

    if len(words) <= max_words:
        return text

    limited = " ".join(words[:max_words])

    last_dot = limited.rfind('.')

    if last_dot > len(limited) * 0.5:
        return limited[:last_dot + 1]

    return limited + "..."

# =========================================================
# ENHANCE RESPONSE STYLE
# =========================================================

def enhance_response_style(text):

    text = text.strip()

    replacements = {
        "Section": "⚖️ Section",
        "Punishment": "🚨 Punishment",
        "Safety Tips": "🛡️ Safety Tips",
        "Steps": "✅ Steps",
        "Prevention": "🛡️ Prevention",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text

# =========================================================
# CYBER QUERY DETECTION
# =========================================================

def is_cyber_related_query(message):

    cyber_keywords = [
        "hack", "hacked", "fraud", "cyber",
        "otp", "scam", "bank", "phishing",
        "instagram", "whatsapp", "facebook",
        "crime", "privacy", "it act",
        "section", "malware", "virus",
        "cyberbullying", "password",
        "identity theft", "data leak"
    ]

    message = message.lower()

    return any(
        keyword in message
        for keyword in cyber_keywords
    )

# =========================================================
# MAIN RESPONSE FUNCTION
# =========================================================

def generate_ai_response(
    user_message,
    language_mode='en',
    history=None,
    user_id=None
):

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

def generate_ai_response_stream(
    user_message,
    language_mode='en',
    history=None,
    user_id=None
):

    # =====================================================
    # LANGUAGE SETTINGS
    # =====================================================

    if language_mode == 'ta':

        lang_instructions = """
Reply only in Tamil.
Use clear and natural Tamil.
Keep the response user-friendly and easy to understand.
"""

    elif language_mode == 'tg':

        lang_instructions = """
Reply only in Tanglish (Tamil written in English letters).

Use natural conversational Tanglish commonly used by Tamil speakers.

Examples:
- "Idhu cyber crime category ku varum."
- "Neenga immediately complaint submit panna vendum."

Avoid pure English unless technical terms are required.
"""

    else:

        lang_instructions = """
Reply only in simple professional English.
Keep responses natural, clear, and user-friendly.
"""

    # =====================================================
    # CYBER DETECTION
    # =====================================================

    is_cyber = is_cyber_related_query(user_message)

    # =====================================================
    # RAG CONTEXT
    # =====================================================

    try:

        context = retrieve_user_context(
            user_id,
            user_message,
            k=3
        )

        context = context[:2500]

    except Exception as e:

        print("RAG ERROR:")
        traceback.print_exc()

        context = ""

    # =====================================================
    # CHAT HISTORY
    # =====================================================

    history_text = ""

    if history:

        recent_history = history[-6:]

        for chat in recent_history:

            user_msg = chat.get("message", "")
            bot_msg = chat.get("response", "")

            history_text += f"""

User: {user_msg}

Assistant: {bot_msg}

"""

    # =====================================================
    # SYSTEM INSTRUCTION
    # =====================================================

    system_instruction = f"""
{SYSTEM_PROMPT_BASE}

{lang_instructions}

Context Information:
{context if context else "Use general cyber law and cybersecurity knowledge."}

Conversation History:
{history_text}
"""

    # =====================================================
    # NON-CYBER HANDLING
    # =====================================================

    if not is_cyber:

        system_instruction += """

The user's question may not be directly related to cyber law.

Respond politely and briefly.
Then intelligently redirect toward cyber awareness or cybersecurity topics if suitable.
"""

    # =====================================================
    # ENHANCED USER MESSAGE
    # =====================================================

    enhanced_user_message = f"""
User Query:
{user_message}

Instructions:
- Give practical and intelligent response
- Mention cyber law sections if relevant
- Avoid robotic replies
- Be conversational and human-like
"""

    # =====================================================
    # GROQ RESPONSE
    # =====================================================

    if client:

        try:

            completion = client.chat.completions.create(

                model="llama-3.3-70b-versatile",

                messages=[

                    {
                        "role": "system",
                        "content": system_instruction
                    },

                    {
                        "role": "user",
                        "content": enhanced_user_message
                    }
                ],

                temperature=0.5,
                top_p=0.9,
                max_tokens=1024,
                stream=True
            )

            collected_response = ""

            for chunk in completion:

                content = chunk.choices[0].delta.content

                if content:

                    collected_response += content

                    styled_content = enhance_response_style(
                        content
                    )

                    yield styled_content

            return

        except Exception as e:

            print("GROQ ERROR:")
            traceback.print_exc()

    # =====================================================
    # GEMINI FALLBACK
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
                "\n\n" +
                enhanced_user_message,
                stream=True
            )

            for chunk in response:

                if chunk.text:

                    styled_text = enhance_response_style(
                        chunk.text
                    )

                    yield styled_text

            return

        except Exception as e:

            print("GEMINI ERROR:")
            traceback.print_exc()

    # =====================================================
    # SMART FALLBACK RESPONSE
    # =====================================================

    fallback_response = f"""
⚠️ AI services are currently unavailable.

However, based on available cyber law knowledge:

{context if context else "Please try again after some time."}

🛡️ Safety Tip:
Always avoid sharing OTPs, passwords, and personal banking details online.
"""

    yield fallback_response