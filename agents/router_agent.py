from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from config.llm_factory import llm_factory
from prompts.system_prompts import get_router_prompt
from utils.toon_converter import TOONConverter, TOONPromptBuilder
import json

class RouterOutput(BaseModel):
    """Schema para saída estruturada do Router"""
    category: Literal["CALCULATOR", "RAG", "DATETIME", "DIRECT"] = Field(
        description="Categoria da pergunta"
    )
    confidence: float = Field(
        description="Confiança na classificação (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Breve explicação da decisão"
    )

class RouterAgent:
    """
    Router Agent que classifica a pergunta do usuário usando JSON→TOON→JSON
    """
    
    def __init__(self, provider: str = None, use_toon: bool = True):
        """
        Inicializa o Router Agent
        
        Args:
            provider: 'openai' ou 'groq'. Se None, usa configuração padrão
            use_toon: Se True, usa conversão JSON→TOON (recomendado)
        """
        # Usa temperatura 0 para decisões consistentes
        self.llm = llm_factory.create_llm(provider, temperature=0)
        self.prompt = get_router_prompt()
        self.use_toon = use_toon
        self.parser = JsonOutputParser(pydantic_object=RouterOutput)
        
        print(f"[ROUTER] ✓ Router Agent inicializado (TOON: {use_toon})")
    
    def route(self, user_query: str) -> Literal["CALCULATOR", "RAG", "DATETIME", "DIRECT"]:
        """
        Analisa a query do usuário e retorna a categoria apropriada
        
        Args:
            user_query: Pergunta do usuário
            
        Returns:
            Uma das categorias: CALCULATOR, RAG, DATETIME, DIRECT
        """
        try:
            if self.use_toon:
                return self._route_with_toon(user_query)
            else:
                return self._route_simple(user_query)
                
        except Exception as e:
            print(f"[ROUTER] ✗ Erro ao rotear: {str(e)}")
            return "DIRECT"
    
    def _route_with_toon(self, user_query: str) -> str:
        """
        Roteamento usando JSON→TOON→JSON (otimizado)
        """
        # 1. Dados em JSON (trabalhamos programaticamente)
        input_data = {
            "query": user_query,
            "task": "classify_query"
        }
        
        output_schema = {
            "category": "string (CALCULATOR|RAG|DATETIME|DIRECT)",
            "confidence": "float (0.0-1.0)",
            "reasoning": "string (brief explanation)"
        }
        
        # 2. Converte para TOON antes de enviar para LLM
        toon_prompt = TOONPromptBuilder.build_structured_prompt(
            task=self.prompt,
            input_data=input_data,
            output_schema=output_schema,
            examples=[
                {
                    "input": {"query": "Calculate 128 * 46"},
                    "output": {
                        "category": "CALCULATOR",
                        "confidence": 0.98,
                        "reasoning": "Mathematical operation detected"
                    }
                },
                {
                    "input": {"query": "Tell me about LLMs"},
                    "output": {
                        "category": "RAG",
                        "confidence": 0.95,
                        "reasoning": "Technical topic in knowledge base"
                    }
                },
                {
                    "input": {"query": "What time is it?"},
                    "output": {
                        "category": "DATETIME",
                        "confidence": 0.99,
                        "reasoning": "Temporal information request"
                    }
                },
                {
                    "input": {"query": "Who was Einstein?"},
                    "output": {
                        "category": "DIRECT",
                        "confidence": 0.90,
                        "reasoning": "General knowledge question"
                    }
                }
            ]
        )
        
        # 3. Envia TOON para LLM
        messages = [HumanMessage(content=toon_prompt)]
        response = self.llm.invoke(messages)
        
        # 4. Converte resposta de volta para JSON
        try:
            # Tenta parsear JSON da resposta
            response_text = response.content.strip()
            
            # Remove markdown code blocks se existirem
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            category = result.get("category", "DIRECT")
            confidence = result.get("confidence", 0.0)
            reasoning = result.get("reasoning", "")
            
            print(f"[ROUTER] Query: '{user_query[:50]}...'")
            print(f"[ROUTER]   → {category} (confidence: {confidence:.2f})")
            print(f"[ROUTER]   → Reasoning: {reasoning}")
            
            return category
            
        except json.JSONDecodeError as e:
            print(f"[ROUTER] ⚠️ Erro ao parsear JSON: {e}")
            print(f"[ROUTER] Resposta bruta: {response.content[:200]}")
            return self._extract_category_fallback(response.content)
    
    def _route_simple(self, user_query: str) -> str:
        """
        Roteamento simples sem TOON (fallback)
        """
        messages = [
            SystemMessage(content=self.prompt),
            HumanMessage(content=f"Pergunta: {user_query}")
        ]
        
        response = self.llm.invoke(messages)
        category = response.content.strip().upper()
        
        valid_categories = {"CALCULATOR", "RAG", "DATETIME", "DIRECT"}
        
        if category in valid_categories:
            print(f"[ROUTER] Query: '{user_query[:50]}...' → {category}")
            return category
        else:
            return self._extract_category_fallback(category)
    
    def _extract_category_fallback(self, text: str) -> str:
        """
        Extrai categoria do texto quando parsing JSON falha
        """
        text_upper = text.upper()
        valid_categories = ["CALCULATOR", "RAG", "DATETIME", "DIRECT"]
        
        for cat in valid_categories:
            if cat in text_upper:
                print(f"[ROUTER] ⚠️ Extraído '{cat}' via fallback")
                return cat
        
        print(f"[ROUTER] ⚠️ Usando DIRECT como fallback final")
        return "DIRECT"
    
    def explain_routing(self, user_query: str) -> dict:
        """
        Retorna a decisão de roteamento com explicação
        
        Args:
            user_query: Pergunta do usuário
            
        Returns:
            Dict com 'category', 'query', 'explanation'
        """
        category = self.route(user_query)
        
        explanations = {
            "CALCULATOR": "Detectei uma operação matemática na sua pergunta.",
            "RAG": "Vou buscar informações na base de conhecimento sobre esse tópico.",
            "DATETIME": "Vou consultar informações de data/hora.",
            "DIRECT": "Vou responder usando meu conhecimento geral."
        }
        
        return {
            "category": category,
            "query": user_query,
            "explanation": explanations.get(category, "Processando sua pergunta..."),
            "using_toon": self.use_toon
        }

if __name__ == "__main__":
    # Testes do router
    router = RouterAgent()
    
    test_queries = [
        "Quanto é 128 vezes 46?",
        "Me fale sobre LLMs",
        "Que horas são?",
        "Quem foi Albert Einstein?",
        "Qual sua experiência com Python?",
        "Calcule a raiz quadrada de 144",
        "O que são embeddings?",
        "Olá, como vai?",
        "Quantos dias entre 2024-01-01 e 2024-12-31?"
    ]
    
    print("\n" + "="*60)
    print("TESTANDO ROUTER AGENT")
    print("="*60 + "\n")
    
    for query in test_queries:
        result = router.explain_routing(query)
        print(f"Query: {query}")
        print(f"  → Categoria: {result['category']}")
        print(f"  → Explicação: {result['explanation']}\n")