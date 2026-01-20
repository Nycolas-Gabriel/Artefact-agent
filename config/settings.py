import os
from dotenv import load_dotenv
from typing import Literal

load_dotenv()

class Settings:
    """Configurações centralizadas da aplicação"""
    
    # LLM Provider
    LLM_PROVIDER: Literal["openai", "groq"] = os.getenv("LLM_PROVIDER", "groq")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    
    # Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # Vector Store
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "./vector_store")
    
    # Model Parameters
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Paths
    DOCS_PATH: str = "./docs"
    PROMPTS_PATH: str = "./prompts"
    
    @classmethod
    def validate(cls):
        """Valida as configurações necessárias"""
        errors = []
        
        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY não configurada para provider OpenAI")
        
        if cls.LLM_PROVIDER == "groq" and not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY não configurada para provider Groq")
        
        if errors:
            raise ValueError("\n".join(errors))
        
        return True

settings = Settings()