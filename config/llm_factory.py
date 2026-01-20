from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.language_models.chat_models import BaseChatModel
from config.settings import settings

class LLMFactory:
    @staticmethod
    def create_llm(provider: str = None, model: str = None, temperature: float = None) -> BaseChatModel:
        provider = provider or settings.LLM_PROVIDER
        temperature = temperature if temperature is not None else settings.TEMPERATURE
        
        if provider == "openai":
            # Se não passar modelo, usa o default do settings
            target_model = model or settings.OPENAI_MODEL
            return ChatOpenAI(
                model=target_model,
                api_key=settings.OPENAI_API_KEY,
                temperature=temperature,
                max_tokens=settings.MAX_TOKENS
            )
        
        elif provider == "groq":
            target_model = model or settings.GROQ_MODEL
            return ChatGroq(
                model=target_model,
                api_key=settings.GROQ_API_KEY,
                temperature=temperature,
                max_tokens=settings.MAX_TOKENS
            )
        
        else:
            raise ValueError(f"Provider '{provider}' não suportado. Use 'openai' ou 'groq'")
    
    @staticmethod
    def get_provider_info() -> dict:
        """Retorna informações sobre o provider atual"""
        return {
            "provider": settings.LLM_PROVIDER,
            "model": settings.OPENAI_MODEL if settings.LLM_PROVIDER == "openai" else settings.GROQ_MODEL,
            "temperature": settings.TEMPERATURE,
            "max_tokens": settings.MAX_TOKENS
        }

llm_factory = LLMFactory()