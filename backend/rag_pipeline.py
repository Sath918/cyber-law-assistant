import os
import traceback

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from langchain_community.vectorstores import FAISS

from langchain_huggingface import HuggingFaceEmbeddings

# =========================================================
# PATH CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(__file__)

DATASET_PATH = os.path.join(
    BASE_DIR,
    'Cyberlaw_dataset.pdf'
)

FAISS_PATH = os.path.join(
    BASE_DIR,
    'faiss_index'
)

USER_INDEX_DIR = os.path.join(
    BASE_DIR,
    'user_indices'
)

os.makedirs(USER_INDEX_DIR, exist_ok=True)

# =========================================================
# GLOBAL VARIABLES
# =========================================================

_embeddings = None
_vector_store = None

# =========================================================
# EMBEDDING MODEL
# =========================================================

def get_embeddings():

    global _embeddings

    if _embeddings is None:

        print("Loading embedding model...")

        _embeddings = HuggingFaceEmbeddings(

            model_name="sentence-transformers/all-MiniLM-L6-v2",

            model_kwargs={
                "device": "cpu"
            },

            encode_kwargs={
                "normalize_embeddings": True
            }
        )

    return _embeddings

# =========================================================
# TEXT SPLITTER
# =========================================================

def get_text_splitter():

    return RecursiveCharacterTextSplitter(

        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,

        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

# =========================================================
# BUILD MAIN VECTOR STORE
# =========================================================

def build_vector_store():

    try:

        if not os.path.exists(DATASET_PATH):

            raise FileNotFoundError(
                f"Dataset not found: {DATASET_PATH}"
            )

        print("Loading cyber law dataset...")

        loader = PyPDFLoader(DATASET_PATH)

        docs = loader.load()

        splitter = get_text_splitter()

        chunks = splitter.split_documents(docs)

        print(f"Created {len(chunks)} chunks")

        embeddings = get_embeddings()

        print("Building FAISS vector database...")

        vector_store = FAISS.from_documents(
            documents=chunks,
            embedding=embeddings
        )

        vector_store.save_local(FAISS_PATH)

        print("FAISS index successfully saved.")

        return vector_store

    except Exception as e:

        print("VECTOR STORE BUILD ERROR:")
        traceback.print_exc()

        return None

# =========================================================
# LOAD VECTOR STORE
# =========================================================

def get_vector_store():

    global _vector_store

    try:

        if _vector_store is not None:
            return _vector_store

        embeddings = get_embeddings()

        if os.path.exists(FAISS_PATH):

            print("Loading existing FAISS index...")

            _vector_store = FAISS.load_local(
                FAISS_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )

        else:

            print("FAISS index not found. Creating new index...")

            _vector_store = build_vector_store()

        return _vector_store

    except Exception as e:

        print("VECTOR STORE LOAD ERROR:")
        traceback.print_exc()

        return None

# =========================================================
# CLEAN CONTEXT
# =========================================================

def clean_context(text):

    if not text:
        return ""

    text = text.replace("\n", " ")

    text = " ".join(text.split())

    return text.strip()

# =========================================================
# GLOBAL CONTEXT RETRIEVAL
# =========================================================

def retrieve_context(query, k=3):

    try:

        store = get_vector_store()

        if store is None:
            return ""

        results = store.similarity_search_with_score(
            query,
            k=k
        )

        filtered_docs = []

        for doc, score in results:

            # Lower score = better similarity
            if score < 1.2:

                cleaned = clean_context(
                    doc.page_content
                )

                filtered_docs.append(cleaned)

        context = "\n\n".join(filtered_docs)

        return context[:4000]

    except Exception as e:

        print("GLOBAL CONTEXT ERROR:")
        traceback.print_exc()

        return ""

# =========================================================
# USER FAISS PATH
# =========================================================

def get_user_faiss_path(user_id):

    return os.path.join(
        USER_INDEX_DIR,
        f"user_{user_id}"
    )

# =========================================================
# DOCUMENT LOADER
# =========================================================

def get_document_loader(filepath):

    filepath = filepath.lower()

    if filepath.endswith(".pdf"):
        return PyPDFLoader(filepath)

    elif filepath.endswith(".docx"):
        return Docx2txtLoader(filepath)

    elif filepath.endswith(".txt"):
        return TextLoader(filepath)

    else:
        return None

# =========================================================
# ADD USER DOCUMENT TO INDEX
# =========================================================

def add_document_to_user_index(user_id, filepath):

    try:

        loader = get_document_loader(filepath)

        if loader is None:

            print(
                f"Unsupported document format: {filepath}"
            )

            return False

        print(f"Processing document: {filepath}")

        docs = loader.load()

        splitter = get_text_splitter()

        chunks = splitter.split_documents(docs)

        embeddings = get_embeddings()

        user_path = get_user_faiss_path(user_id)

        if os.path.exists(user_path):

            print("Loading existing user index...")

            vector_store = FAISS.load_local(
                user_path,
                embeddings,
                allow_dangerous_deserialization=True
            )

            vector_store.add_documents(chunks)

        else:

            print("Creating new user vector store...")

            vector_store = FAISS.from_documents(
                chunks,
                embeddings
            )

        vector_store.save_local(user_path)

        print(
            f"Successfully indexed document for user {user_id}"
        )

        return True

    except Exception as e:

        print("USER DOCUMENT INDEX ERROR:")
        traceback.print_exc()

        return False

# =========================================================
# USER + GLOBAL CONTEXT RETRIEVAL
# =========================================================

def retrieve_user_context(user_id, query, k=3):

    try:

        global_context = retrieve_context(
            query,
            k=k
        )

        user_context = ""

        if user_id:

            user_path = get_user_faiss_path(user_id)

            if os.path.exists(user_path):

                embeddings = get_embeddings()

                store = FAISS.load_local(
                    user_path,
                    embeddings,
                    allow_dangerous_deserialization=True
                )

                results = store.similarity_search_with_score(
                    query,
                    k=k
                )

                user_docs = []

                for doc, score in results:

                    if score < 1.2:

                        cleaned = clean_context(
                            doc.page_content
                        )

                        user_docs.append(cleaned)

                if user_docs:

                    user_context = (
                        "USER DOCUMENT CONTEXT:\n\n" +
                        "\n\n".join(user_docs)
                    )

        combined_context = ""

        if user_context:

            combined_context += user_context

        if global_context:

            combined_context += (
                "\n\nCYBER LAW KNOWLEDGE BASE:\n\n" +
                global_context
            )

        return combined_context[:5000]

    except Exception as e:

        print("USER CONTEXT ERROR:")
        traceback.print_exc()

        return ""