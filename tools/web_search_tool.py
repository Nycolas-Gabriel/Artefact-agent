from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import requests
import os
from datetime import datetime
import time

# --- 1. DEFINIÇÃO DOS SCHEMAS (Devem vir primeiro) ---

class WebSearchInput(BaseModel):
    query: str = Field(description="Consulta de pesquisa para buscar na web")
    num_results: int = Field(default=5, description="Número de resultados a retornar (1-10)")

class SerpAPISearchInput(BaseModel):
    query: str = Field(description="Consulta de pesquisa")
    num_results: int = Field(default=5, description="Número de resultados")

# --- 2. DEFINIÇÃO DAS FERRAMENTAS ---

@tool(args_schema=WebSearchInput)
def web_search(query: str, num_results: int = 5) -> str:
    """Pesquisa na web usando DuckDuckGo (Grátis)."""
    try:
        if not query or not query.strip():
            return "Erro: consulta de pesquisa vazia"
        
        from duckduckgo_search import DDGS
        num_results = max(1, min(num_results, 10))
        
        print(f"[WEB SEARCH] 🌐 Pesquisando: '{query}'")
        
        with DDGS() as ddgs:
            # Sintaxe atualizada para evitar o Warning
            search_results = ddgs.text(query, max_results=num_results)
            results = [r for r in search_results]
        
        if not results:
            return f"Nenhum resultado encontrado para '{query}'"
        
        formatted_results = [f"🔍 Resultados para: '{query}'\n"]
        for i, result in enumerate(results, 1):
            formatted_results.append(f"[{i}] {result.get('title')}\n    {result.get('body')}\n    🔗 {result.get('href')}\n")
        
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Erro no DuckDuckGo: {str(e)}"

@tool(args_schema=SerpAPISearchInput)
def web_search_serpapi(query: str, num_results: int = 5) -> str:
    """Pesquisa na web usando SerpAPI (Google)."""
    try:
        api_key = os.getenv("SERPAPI_KEY")
        if not api_key:
            return "Erro: SERPAPI_KEY não configurada no .env"
        
        params = {
            "q": query, "api_key": api_key, "num": num_results, "engine": "google", "hl": "pt-br"
        }
        
        print(f"[SERPAPI] 🌐 Pesquisando no Google: '{query}'")
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        
        organic_results = response.json().get("organic_results", [])
        if not organic_results:
            return "Nenhum resultado encontrado."
            
        formatted_results = [f"🔍 Resultados Google: '{query}'\n"]
        for i, result in enumerate(organic_results[:num_results], 1):
            formatted_results.append(f"[{i}] {result.get('title')}\n    {result.get('snippet')}\n    🔗 {result.get('link')}\n")
        
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Erro na SerpAPI: {str(e)}"

# --- 3. BLOCO DE TESTE ---

if __name__ == "__main__":
    print("="*60)
    print("TESTANDO WEB SEARCH TOOL")
    print("="*60 + "\n")
    
    # Testando apenas o DuckDuckGo para validar
    print(web_search.invoke({"query": "clima hoje São Paulo", "num_results": 2}))