import requests
import json
import os
from dotenv import load_dotenv
import urllib.parse
import time

# Relative package imports
from .rag_pipeline import retrieve_context, retrieve_user_context, retrieve_global_context_with_score, retrieve_session_context_with_score

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
    from .database import get_db_connection
    try:
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) FROM files WHERE session_id = ? AND status = 'ready'", (session_id,)).fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Error checking session files: {e}")
        return False

def classify_intent(user_message, history=None, session_id='default'):
    msg_lower = user_message.strip().lower()
    
    # 1. Quick greetings / conversational keywords (Rule-based layer to eliminate latency)
    greetings = {"hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon", "good evening", "howdy", "whats up"}
    casual_phrases = {"how are you", "who are you", "what is your name", "what can you do", "help me", "thank you", "thanks", "bye", "goodbye"}
    
    # Clean message for check
    clean_msg = "".join(c for c in msg_lower if c.isalnum() or c.isspace()).strip()
    
    if clean_msg in greetings or any(phrase in clean_msg for phrase in casual_phrases):
        return "Casual Conversation"
        
    # 2. Image generation keywords
    image_keywords = {"generate an image", "create an image", "draw", "paint", "make an image", "generate a picture", "create a picture", "generate photo", "create photo", "draw a"}
    if any(keyword in msg_lower for keyword in image_keywords):
        return "Image Generation Request"

    # 3. LLM-based Classifier
    history_text = ""
    if history:
        for chat in history[-3:]:
            history_text += f"\nUser: {chat['message']}\nAssistant: {chat['response']}"

    system_prompt = """You are an intent classifier for CyberLex AI.
Analyze the user's message and the conversation history, and classify it into exactly one of these categories:
- Cyber Law Question (e.g. laws, Indian Information Technology Act, sections, cybercrime punishments, legal rights, filing complaints)
- Cyber Security Question (e.g. securing accounts, passwords, phishing safety, 2FA, malware, system protection advice)
- Uploaded Document Question (e.g. asking about uploaded files, documents, pdfs, txt files, summaries of files, contract contents)
- Image Generation Request (e.g. draw an image, create a picture, generate visual art)
- General Knowledge Question (e.g. trivia, cooking, programming help, history, geography, science, math - NOT about cyber law or cybersecurity)
- Casual Conversation (e.g. hi, bye, how are you, who made you, joke, chitchat)

Respond with ONLY the exact category name. Do not include any explanations, punctuation, or extra words.
Example: Cyber Law Question"""

    prompt = f"Conversation History:\n{history_text}\n\nUser Message: {user_message}\n\nIntent Category:"
    
    # Try Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if GROQ_API_KEY and GROQ_API_KEY.startswith("gsk_"):
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=20
            )
            val = completion.choices[0].message.content.strip()
            if val in {"Cyber Law Question", "Cyber Security Question", "Uploaded Document Question", "Image Generation Request", "General Knowledge Question", "Casual Conversation"}:
                return val
        except Exception as e:
            print("Groq classification error:", e)

    # Try Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                system_prompt + "\n\nUser Message: " + prompt,
                generation_config={"temperature": 0.0, "max_output_tokens": 20}
            )
            val = response.text.strip()
            if val in {"Cyber Law Question", "Cyber Security Question", "Uploaded Document Question", "Image Generation Request", "General Knowledge Question", "Casual Conversation"}:
                return val
        except Exception as e:
            print("Gemini classification error:", e)

    # Try Ollama
    try:
        payload = {
            "model": OLLAMA_MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 20}
        }
        res = requests.post(OLLAMA_API_URL, json=payload, timeout=10)
        if res.status_code == 200:
            decoded = res.json()
            val = decoded["message"]["content"].strip()
            if val in {"Cyber Law Question", "Cyber Security Question", "Uploaded Document Question", "Image Generation Request", "General Knowledge Question", "Casual Conversation"}:
                return val
    except Exception as e:
        print("Ollama classification error:", e)

    # Rule-based fallback
    has_files = has_session_files(session_id)
    if has_files and any(w in msg_lower for w in {"file", "document", "pdf", "docx", "text", "uploaded", "summary", "summarize"}):
        return "Uploaded Document Question"
    if any(w in msg_lower for w in {"section", "it act", "law", "punishment", "legal", "court", "complaint", "police", "fir", "fine", "arrest"}):
        return "Cyber Law Question"
    if any(w in msg_lower for w in {"protect", "secure", "hack", "scam", "phish", "spam", "password", "2fa", "mfa", "malware", "virus"}):
        return "Cyber Security Question"
        
    return "Cyber Law Question"

def handle_image_generation(user_message):
    system_prompt = """You are an art director helper. The user wants to generate an image.
Based on their message and context, write a single highly-detailed visual prompt for a Stable Diffusion image generator.
Describe the style (e.g. 3D render, futuristic neon, highly detailed digital art), lighting, subject, and scene.
Your output must be ONLY the prompt itself, without quotes, introductory text, or explanatory notes.
Example input: "draw a legal shield"
Example output: "a glowing neon cyber shield with scales of justice, futuristic cybersecurity digital art, dark background, 8k resolution"
"""
    img_prompt = ""
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if GROQ_API_KEY and GROQ_API_KEY.startswith("gsk_"):
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=60
            )
            img_prompt = completion.choices[0].message.content.strip()
        except:
            pass

    if not img_prompt:
        img_prompt = user_message.lower()
        for phrase in ["generate an image of", "create an image of", "draw a picture of", "draw", "paint", "generate", "create", "make a picture of"]:
            img_prompt = img_prompt.replace(phrase, "")
        img_prompt = img_prompt.strip() + ", detailed digital art, cyber theme"

    encoded_prompt = urllib.parse.quote(img_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=600&nologo=true&private=true"
    
    response_text = f"Here is the image you requested for **\"{user_message}\"**:\n\n"
    response_text += f"![Generated Image]({image_url})\n\n"
    response_text += f"> [!TIP]\n"
    response_text += f"> **Visual Prompt Used:** *{img_prompt}*\n"
    response_text += f"> You can click or download the image above."
    
    return response_text

def generate_llm_response_stream(user_message, system_instruction, context_text=None):
    # --- Ollama Integration (Primary) ---
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
        response = requests.post(OLLAMA_API_URL, json=payload, stream=True, timeout=30)
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

    # --- Groq Integration (Fallback) ---
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

    # --- Gemini Integration (Fallback 2) ---
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

    # --- Database Fallback ---
    if context_text:
        yield "AI services are currently unavailable. Here is info from the Cyber Law Database:\n\n"
        yield context_text
    else:
        from .chatbot import generate_response
        yield generate_response(user_message)

def generate_ai_response(user_message, language_mode='en', history=None, user_id=None, session_id='default'):
    # Consume the generator to return full string
    # Filter out status messages starting with $$status: and ending with $$
    full_response = []
    for chunk in generate_ai_response_stream(user_message, language_mode, history, user_id, session_id):
        if not (chunk.startswith("$$status:") and chunk.endswith("$$\n")):
            full_response.append(chunk)
    return "".join(full_response)

def generate_ai_response_stream(user_message, language_mode='en', history=None, user_id=None, session_id='default'):
    yield "$$status: Detecting user intent...$$\n"
    
    intent = classify_intent(user_message, history, session_id)
    has_files = has_session_files(session_id)
    
    if intent == "Image Generation Request":
        yield "$$status: Generating image prompt and rendering...$$\n"
        img_resp = handle_image_generation(user_message)
        for i in range(0, len(img_resp), 5):
            yield img_resp[i:i+5]
            time.sleep(0.01)
        return

    # Language support
    if language_mode == 'ta':
        lang_instructions = "Reply only in Tamil."
    elif language_mode == 'tg':
        lang_instructions = "Reply only in Tanglish (Tamil written in English script)."
    else:
        lang_instructions = "Reply only in simple English."

    # Format history
    history_text = ""
    if history:
        for chat in history[-5:]:
            history_text += f"\nUser: {chat['message']}\nAssistant: {chat['response']}"

    # Priority Order Routing
    if has_files:
        yield "$$status: Analyzing uploaded files...$$\n"
        # 1. Search session/uploaded documents index
        session_matches = retrieve_session_context_with_score(session_id, user_message, k=3)
        valid_session_matches = [doc for doc, score in session_matches if score < 1.35]
        
        if valid_session_matches:
            yield "$$status: Retrieving relevant document chunks...$$\n"
            context_parts = []
            for doc in valid_session_matches:
                source = doc.metadata.get("source", "Unknown Document")
                context_parts.append(f"Document [{source}]:\n{doc.page_content}")
            context_text = "\n\n-----\n\n".join(context_parts)
            
            system_prompt = f"""You are CyberLex AI, a document analysis assistant.
Your task is to answer the user's question based ONLY on the provided uploaded documents context.

CONSTRAINTS:
1. Answer the question using ONLY the provided document context. Do not make up or assume any answer.
2. If the context does not contain the answer, reply EXACTLY with: "I couldn't find that information in the uploaded document." Do not try to make up or assume any answer.
3. Quote or reference specific sections and mention the document names (e.g., "[example.pdf]") when available.
4. Do not hallucinate or use external knowledge outside the provided documents.
5. If the user asks you to compare documents, do so based only on the provided context.
"""
            system_instruction = f"{system_prompt}\n{lang_instructions}\n\nContext:\n{context_text}\n\nConversation History:\n{history_text}"
            
            yield "$$status: Generating response from uploaded files...$$\n"
            for chunk in generate_llm_response_stream(user_message, system_instruction, context_text):
                yield chunk
            return
        else:
            yield "$$status: Information not found in files. Searching Cyber Law Database...$$\n"
            # 2. Search Global Cyber Law Database
            global_matches = retrieve_global_context_with_score(user_message, k=3)
            valid_global_matches = [doc for doc, score in global_matches if score < 1.35]
            
            if valid_global_matches:
                yield "$$status: Retrieving matching sections...$$\n"
                context_text = "\n-----\n".join([doc.page_content for doc in valid_global_matches])
                
                system_prompt = f"""You are CyberLex AI, an advanced AI-powered Cyber Law and Cyber Security Assistant.
The user asked a question, but we could not find relevant information in their uploaded documents.
However, we found relevant information in the official Cyber Law Knowledge Base.
Please answer the question using the Cyber Law Knowledge Base context below.
State clearly at the beginning of your response that: "I couldn't find that information in your uploaded documents, but here is what the Cyber Law Database says:".
Explain legal concepts in simple language, mention relevant IT Act sections, and give safety guidance where appropriate.
Do not fabricate laws or punishments.
"""
                system_instruction = f"{system_prompt}\n{lang_instructions}\n\nContext:\n{context_text}\n\nConversation History:\n{history_text}"
                
                yield "$$status: Generating response...$$\n"
                for chunk in generate_llm_response_stream(user_message, system_instruction, context_text):
                    yield chunk
                return
            else:
                yield "$$status: Information not found. Bypassing RAG to LLM...$$\n"
                # 3. Fallback to general LLM knowledge
                system_prompt = f"""You are CyberLex AI, an advanced AI-powered Cyber Law and Cyber Security Assistant.
IMPORTANT: We could not find specific matches for this topic in either your uploaded files or our official Cyber Law database.
Therefore, you must answer the user's question using your general knowledge of Cyber Law, the Information Technology Act 2000, and cybersecurity practices.
At the very beginning or in a natural way within your response, clearly state that your answer is based on general knowledge rather than the project's curated database/files (e.g. "While this specific query isn't in your files or our curated database, here is the general legal guidance:").
Make the response accurate, conversational, and easy to understand.
Do not fabricate laws or punishments.
"""
                system_instruction = f"{system_prompt}\n{lang_instructions}\n\nConversation History:\n{history_text}"
                
                yield "$$status: Generating response using general knowledge...$$\n"
                for chunk in generate_llm_response_stream(user_message, system_instruction, None):
                    yield chunk
                return
    else:
        # Standard flow without session files
        if intent in {"Cyber Law Question", "Cyber Security Question"}:
            yield "$$status: Searching Cyber Law Knowledge Database...$$\n"
            global_matches = retrieve_global_context_with_score(user_message, k=3)
            valid_global_matches = [doc for doc, score in global_matches if score < 1.35]
            
            if valid_global_matches:
                yield "$$status: Retrieving matching sections...$$\n"
                context_text = "\n-----\n".join([doc.page_content for doc in valid_global_matches])
                
                system_prompt = f"""You are CyberLex AI, an advanced AI-powered Cyber Law and Cyber Security Assistant.
Your task is to answer the user's question accurately and conversationally, primarily relying on the curated Cyber Law database context below.
Use simple, easy-to-understand English. Avoid complex legal jargon unless necessary.
Mention relevant IT Act sections and include practical safety recommendations when appropriate.
List document sources or sections (e.g., citing sections of the IT Act or mentioning dataset references) at the bottom under a '**Sources:**' section.
Do not fabricate laws or punishments.
"""
                system_instruction = f"{system_prompt}\n{lang_instructions}\n\nContext:\n{context_text}\n\nConversation History:\n{history_text}"
                
                yield "$$status: Generating response...$$\n"
                for chunk in generate_llm_response_stream(user_message, system_instruction, context_text):
                    yield chunk
                return
            else:
                yield "$$status: No database entry found. Using general knowledge...$$\n"
                system_prompt = f"""You are CyberLex AI, an advanced AI-powered Cyber Law and Cyber Security Assistant.
IMPORTANT: We could not find specific matches for this topic in our official Cyber Law database.
Therefore, you must answer the user's question using your general knowledge of Cyber Law, the Information Technology Act 2000, and cybersecurity practices.
At the very beginning or in a natural way within your response, clearly state that your answer is based on general knowledge rather than the project's database (e.g. "While this specific query isn't in our curated database, here is the general legal guidance:").
Make the response accurate, conversational, and easy to understand.
Do not fabricate laws or punishments.
"""
                system_instruction = f"{system_prompt}\n{lang_instructions}\n\nConversation History:\n{history_text}"
                
                yield "$$status: Generating response using general knowledge...$$\n"
                for chunk in generate_llm_response_stream(user_message, system_instruction, None):
                    yield chunk
                return
        elif intent == "General Knowledge Question":
            yield "$$status: Analyzing general knowledge...$$\n"
            system_prompt = f"""You are CyberLex AI, an advanced AI-powered Cyber Law and Cyber Security Assistant.
The user is asking a general knowledge question unrelated to cyber law or cybersecurity.
Politely answer the question briefly using your general knowledge, clearly stating that this is based on general knowledge rather than the cyber law database.
Then, gently redirect the user towards cyber law, IT Act 2000, or cybersecurity topics.
"""
            system_instruction = f"{system_prompt}\n{lang_instructions}\n\nConversation History:\n{history_text}"
            
            yield "$$status: Generating response...$$\n"
            for chunk in generate_llm_response_stream(user_message, system_instruction, None):
                yield chunk
            return
        else: # Casual Conversation / greetings
            yield "$$status: Processing greeting...$$\n"
            system_prompt = f"""You are CyberLex AI, an advanced AI-powered Cyber Law and Cyber Security Assistant.
Engage in friendly and professional casual conversation.
Politely answer the user, and if appropriate, remind them that you are here to assist with cyber laws, IT Act 2000, online fraud prevention, and cybersecurity best practices.
"""
            system_instruction = f"{SYSTEM_PROMPT_BASE}\n{system_prompt}\n{lang_instructions}\n\nConversation History:\n{history_text}"
            
            yield "$$status: Generating response...$$\n"
            for chunk in generate_llm_response_stream(user_message, system_instruction, None):
                yield chunk
            return
