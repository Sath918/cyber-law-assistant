import os
from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS

# Conditional import to avoid loading PyTorch/Transformers on Render
HuggingFaceEmbeddings = None
if not os.getenv("RENDER"):
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except ImportError:
        pass



DATASET_PATH = os.path.join(os.path.dirname(__file__), 'Cyberlaw_dataset.pdf')
FAISS_PATH = os.path.join(os.path.dirname(__file__), 'faiss_index')

class APIEmbeddings(Embeddings):
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        
        self.client_type = None
        if self.gemini_key and self.gemini_key != "your_gemini_api_key_here":
            self.client_type = "gemini"
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
        elif self.groq_key and self.groq_key.startswith("gsk_"):
            self.client_type = "groq"
            from groq import Groq
            self.groq_client = Groq(api_key=self.groq_key)
        else:
            self.client_type = "mock"
            print("WARNING: No valid GEMINI_API_KEY or GROQ_API_KEY found. Using mock embeddings (semantic search will not work).")

    def embed_documents(self, texts):
        if not texts:
            return []
        
        if self.client_type == "gemini":
            import google.generativeai as genai
            try:
                response = genai.embed_content(
                    model="models/text-embedding-004",
                    content=texts,
                    task_type="retrieval_document"
                )
                return response['embedding']
            except Exception as e:
                print("Gemini embed documents error, falling back to individual calls:", e)
                embeddings = []
                for text in texts:
                    try:
                        res = genai.embed_content(
                            model="models/text-embedding-004",
                            content=text,
                            task_type="retrieval_document"
                        )
                        embeddings.append(res['embedding'])
                    except Exception as inner_e:
                        print("Gemini individual embed error:", inner_e)
                        embeddings.append([0.0] * 768)
                return embeddings
                
        elif self.client_type == "groq":
            try:
                response = self.groq_client.embeddings.create(
                    model="nomic-embed-text-v1.5",
                    input=texts
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                print("Groq embed documents error, falling back to individual calls:", e)
                embeddings = []
                for text in texts:
                    try:
                        res = self.groq_client.embeddings.create(
                            model="nomic-embed-text-v1.5",
                            input=text
                        )
                        embeddings.append(res.data[0].embedding)
                    except Exception as inner_e:
                        print("Groq individual embed error:", inner_e)
                        embeddings.append([0.0] * 768)
                return embeddings
        else:
            return [[0.0] * 768 for _ in texts]

    def embed_query(self, text):
        if self.client_type == "gemini":
            import google.generativeai as genai
            try:
                response = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="retrieval_query"
                )
                return response['embedding']
            except Exception as e:
                print("Gemini embed query error:", e)
                return [0.0] * 768
        elif self.client_type == "groq":
            try:
                response = self.groq_client.embeddings.create(
                    model="nomic-embed-text-v1.5",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                print("Groq embed query error:", e)
                return [0.0] * 768
        else:
            return [0.0] * 768

_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is not None:
        return _embeddings
        
    gemini_key = os.getenv("GEMINI_API_KEY")
    if os.getenv("RENDER") or (gemini_key and gemini_key != "your_gemini_api_key_here"):
        _embeddings = APIEmbeddings()
    elif HuggingFaceEmbeddings is not None:
        print("Using local HuggingFaceEmbeddings (all-MiniLM-L6-v2)...")
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    else:
        print("WARNING: No valid API keys and HuggingFaceEmbeddings not available. Using mock embeddings.")
        _embeddings = APIEmbeddings()
        
    return _embeddings

def build_vector_store():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset {DATASET_PATH} not found. Please run build_dataset.py first.")
    
    # Load
    loader = PyPDFLoader(DATASET_PATH)
    docs = loader.load()
    
    # Chunk
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len,
    )
    chunks = text_splitter.split_documents(docs)
    
    # Embed & Store
    embeddings = get_embeddings()
    print("Building FAISS vector store... This might take a moment to download the embedding model initial run.")
    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings
    )
    vector_store.save_local(FAISS_PATH)
    print("Vector store successfully created and persisted.")
    return vector_store

_vector_store = None

def get_vector_store():
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    # Load existing or build
    if os.path.exists(os.path.join(FAISS_PATH, "index.faiss")):
        embeddings = get_embeddings()
        try:
            store = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
            # Verify dimension consistency
            test_emb = embeddings.embed_query("test")
            if store.index.d == len(test_emb):
                _vector_store = store
                return _vector_store
            else:
                print(f"FAISS index dimension ({store.index.d}) mismatch with embedding model ({len(test_emb)}). Rebuilding vector store...")
        except Exception as e:
            print(f"Failed to load existing FAISS index: {e}. Rebuilding vector store...")
            
    _vector_store = build_vector_store()
    return _vector_store

def retrieve_context(query, k=3):
    try:
        store = get_vector_store()
        results = store.similarity_search(query, k=k)
        context = "\n-----\n".join([doc.page_content for doc in results])
        return context
    except Exception as e:
        print(f"Error retrieving global context: {e}")
        return ""

def retrieve_global_context_with_score(query, k=3):
    try:
        store = get_vector_store()
        # Returns list of (Document, score)
        results = store.similarity_search_with_score(query, k=k)
        return results
    except Exception as e:
        print(f"Error retrieving global context with score: {e}")
        return []

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
import hashlib
import re
import shutil
from langchain_core.documents import Document
from database import get_db_connection

def compute_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def clean_text(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = '\n'.join([line.strip() for line in text.split('\n')])
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_text_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf':
        loader = PyPDFLoader(filepath)
        docs = loader.load()
        return "\n".join([doc.page_content for doc in docs])
    elif ext == '.docx':
        loader = Docx2txtLoader(filepath)
        docs = loader.load()
        return "\n".join([doc.page_content for doc in docs])
    elif ext == '.txt':
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def get_file_cache_path(file_hash):
    base_dir = os.path.dirname(__file__)
    cache_dir = os.path.join(base_dir, 'file_cache')
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f'file_{file_hash}')

def get_session_faiss_path(session_id):
    base_dir = os.path.dirname(__file__)
    user_faiss_dir = os.path.join(base_dir, 'user_indices')
    os.makedirs(user_faiss_dir, exist_ok=True)
    return os.path.join(user_faiss_dir, f'session_{session_id}')

def process_session_document(user_id, session_id, filepath, filename):
    try:
        file_hash = compute_file_hash(filepath)
        cache_path = get_file_cache_path(file_hash)
        
        # Check cache
        cache_exists = os.path.exists(cache_path)
        
        if not cache_exists:
            print(f"File index cache miss for hash {file_hash}. Extracting text...")
            raw_text = extract_text_from_file(filepath)
            cleaned_text = clean_text(raw_text)
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=600,
                chunk_overlap=100,
                length_function=len,
            )
            split_texts = text_splitter.split_text(cleaned_text)
            
            # Create LangChain documents with filename metadata
            chunks = [
                Document(page_content=chunk, metadata={"source": filename})
                for chunk in split_texts
            ]
            
            if not chunks:
                chunks = [Document(page_content=f"Empty file: {filename}", metadata={"source": filename})]
            
            embeddings = get_embeddings()
            vector_store = FAISS.from_documents(chunks, embeddings)
            vector_store.save_local(cache_path)
            print(f"Successfully cached FAISS index for file {filename} at {cache_path}")
            
        # Update database with hash and mark ready
        conn = get_db_connection()
        conn.execute('UPDATE files SET file_hash = ?, status = ? WHERE filepath = ?', (file_hash, 'ready', filepath))
        conn.commit()
        conn.close()
        
        # Rebuild session index
        rebuild_session_index(session_id)
        return True, file_hash
    except Exception as e:
        print(f"Error processing session document: {e}")
        try:
            conn = get_db_connection()
            conn.execute("UPDATE files SET status = 'error' WHERE filepath = ?", (filepath,))
            conn.commit()
            conn.close()
        except Exception as db_err:
            print(f"Error updating file status to error: {db_err}")
        return False, str(e)

def rebuild_session_index(session_id):
    try:
        session_path = get_session_faiss_path(session_id)
        
        conn = get_db_connection()
        files = conn.execute("SELECT file_hash, filename FROM files WHERE session_id = ? AND status = 'ready'", (session_id,)).fetchall()
        conn.close()
        
        if not files:
            # Delete session index if no active files
            if os.path.exists(session_path):
                shutil.rmtree(session_path)
            print(f"Session index cleared for session {session_id}")
            return True
            
        embeddings = get_embeddings()
        merged_store = None
        
        for file_row in files:
            f_hash = file_row['file_hash']
            cache_path = get_file_cache_path(f_hash)
            
            if os.path.exists(cache_path):
                db = FAISS.load_local(cache_path, embeddings, allow_dangerous_deserialization=True)
                if merged_store is None:
                    merged_store = db
                else:
                    merged_store.merge_from(db)
                    
        if merged_store:
            merged_store.save_local(session_path)
            print(f"Successfully rebuilt session FAISS index at {session_path} with {len(files)} files.")
            return True
        else:
            if os.path.exists(session_path):
                shutil.rmtree(session_path)
            return False
    except Exception as e:
        print(f"Error rebuilding session index: {e}")
        return False

def retrieve_session_context(session_id, query, k=3):
    try:
        session_path = get_session_faiss_path(session_id)
        if os.path.exists(session_path):
            embeddings = get_embeddings()
            store = FAISS.load_local(session_path, embeddings, allow_dangerous_deserialization=True)
            results = store.similarity_search(query, k=k)
            return results
        return []
    except Exception as e:
        print(f"Error retrieving session context: {e}")
        return []

def retrieve_session_context_with_score(session_id, query, k=3):
    try:
        session_path = get_session_faiss_path(session_id)
        if os.path.exists(session_path):
            embeddings = get_embeddings()
            store = FAISS.load_local(session_path, embeddings, allow_dangerous_deserialization=True)
            # Returns list of (Document, score)
            results = store.similarity_search_with_score(query, k=k)
            return results
        return []
    except Exception as e:
        print(f"Error retrieving session context with score: {e}")
        return []

def get_user_faiss_path(user_id):
    base_dir = os.path.dirname(__file__)
    user_faiss_dir = os.path.join(base_dir, 'user_indices')
    os.makedirs(user_faiss_dir, exist_ok=True)
    return os.path.join(user_faiss_dir, f'user_{user_id}')

def add_document_to_user_index(user_id, filepath):
    filename = os.path.basename(filepath)
    success, _ = process_session_document(user_id, "default", filepath, filename)
    return success

def retrieve_user_context(user_id, query, k=2):
    global_context = retrieve_context(query, k=k)
    user_context = ""
    
    session_path = get_session_faiss_path("default")
    if os.path.exists(session_path):
        try:
            embeddings = get_embeddings()
            store = FAISS.load_local(session_path, embeddings, allow_dangerous_deserialization=True)
            results = store.similarity_search(query, k=k)
            if results:
                user_context = "USER UPLOADED DOCUMENTS:\n" + "\n-----\n".join([doc.page_content for doc in results])
        except Exception as e:
            print(f"Error retrieving legacy user context: {e}")
            
    combined_context = global_context
    if user_context:
        combined_context = user_context + "\n\nGLOBAL CYBER LAW DATABASE:\n" + global_context
        
    return combined_context
