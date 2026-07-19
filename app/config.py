import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.0-flash"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    MAX_TOKENS: int = 700   # max tokens Gemini returns per answer
    HALLUCINATION_CHECK_MAX_TOKENS: int = 10  # only need YES or NO  Hallucination checker
    TEMPERATURE: float = 0.1 #Reality factor 


    # RAG retrieval (ChromaDB)
    RETRIEVAL_K: int = 2  # how many chunks to retrieve per query

    # Chunking
    CHUNK_SIZE: int =  512   # characters per chunk
    CHUNK_OVERLAP: int = 100 # overlap between chunks

    # Memory (RunnableWithMessageHistory + trim_messages)
    MEMORY_MAX_TOKEN_LIMIT: int = 1500  # trim any message over this token

    # ChromaDB
    CHROMA_COLLECTION_NAME: str = "finance_docs"
    
    # Error checking for Connection to GEMINI API
    @classmethod
    def validate(cls) -> None:
        if not cls.GOOGLE_API_KEY:
            raise EnvironmentError(
                "GOOGLE_API_KEY is not set. Add it to your .env file or Render dashboard."
            )