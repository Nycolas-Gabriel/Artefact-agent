from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.language_models.chat_models import BaseChatModel
from config.settings import settings

class LLMFactory:
    """Factory para criar instâncias de LLM baseado no provider configurado"""
    
    @staticmethod
    def create_llm(provider: str = None, temperature: float = None) -> BaseChatModel:
        """
        Cria uma instância de LLM baseado no provider
        
        Args:
            provider: 'openai' ou 'groq'. Se None, usa settings.LLM_PROVIDER
            temperature: Temperatura do modelo. Se None, usa settings.TEMPERATURE
            
        Returns:
            Instância de ChatModel configurada
        """
        provider = provider or settings.LLM_PROVIDER
        temperature = temperature if temperature is not None else settings.TEMPERATURE
        
        if provider == "openai":
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                temperature=temperature,
                max_tokens=settings.MAX_TOKENS,
                request_timeout=60
            )
        
        elif provider == "groq":
            return ChatGroq(
                model=settings.GROQ_MODEL,
                api_key=settings.GROQ_API_KEY,
                temperature=temperature,
                max_tokens=settings.MAX_TOKENS,
                request_timeout=60
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