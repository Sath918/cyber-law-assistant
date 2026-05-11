import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

DATASET_PATH = os.path.join(os.path.dirname(__file__), 'Cyberlaw_dataset.pdf')
FAISS_PATH = os.path.join(os.path.dirname(__file__), 'faiss_index')

# Use sentence transformers directly to avoid external API calls
# Provide an embedding model (all-MiniLM-L6-v2 is small and fast)
_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
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
    if os.path.exists(FAISS_PATH):
        embeddings = get_embeddings()
        _vector_store = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
        return _vector_store
    else:
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

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader

def get_user_faiss_path(user_id):
    base_dir = os.path.dirname(__file__)
    user_faiss_dir = os.path.join(base_dir, 'user_indices')
    os.makedirs(user_faiss_dir, exist_ok=True)
    return os.path.join(user_faiss_dir, f'user_{user_id}')

def add_document_to_user_index(user_id, filepath):
    try:
        if filepath.lower().endswith('.pdf'):
            loader = PyPDFLoader(filepath)
        elif filepath.lower().endswith('.docx'):
            loader = Docx2txtLoader(filepath)
        else:
            print(f"Unsupported file format for RAG: {filepath}")
            return False

        docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=len,
        )
        chunks = text_splitter.split_documents(docs)
        
        embeddings = get_embeddings()
        user_path = get_user_faiss_path(user_id)
        
        if os.path.exists(user_path):
            # Load existing and add new docs
            vector_store = FAISS.load_local(user_path, embeddings, allow_dangerous_deserialization=True)
            vector_store.add_documents(chunks)
        else:
            # Create new index for user
            vector_store = FAISS.from_documents(chunks, embeddings)
            
        vector_store.save_local(user_path)
        print(f"Successfully processed and stored document for user {user_id}")
        return True
    except Exception as e:
        print(f"Error processing document for user {user_id}: {e}")
        return False

def retrieve_user_context(user_id, query, k=2):
    global_context = retrieve_context(query, k=k)
    user_context = ""
    
    if user_id:
        try:
            user_path = get_user_faiss_path(user_id)
            if os.path.exists(user_path):
                embeddings = get_embeddings()
                store = FAISS.load_local(user_path, embeddings, allow_dangerous_deserialization=True)
                results = store.similarity_search(query, k=k)
                if results:
                    user_context = "USER UPLOADED DOCUMENTS:\n" + "\n-----\n".join([doc.page_content for doc in results])
        except Exception as e:
            print(f"Error retrieving user context: {e}")
            
    combined_context = global_context
    if user_context:
        combined_context = user_context + "\n\nGLOBAL CYBER LAW DATABASE:\n" + global_context
        
    return combined_context
