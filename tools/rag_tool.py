from langchain_core.tools import tool
from preprocessing.document_processor import DocumentProcessor
from config.settings import settings
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List

# Instância global do vector store
_vector_store = None

def get_vector_store():
    """Retorna instância única do vector store"""
    global _vector_store
    
    if _vector_store is None:
        processor = DocumentProcessor()
        try:
            _vector_store = processor.load_vector_store()
        except FileNotFoundError:
            print("[RAG] Vector store não encontrado. Execute o preprocessing primeiro.")
            return None
    
    return _vector_store

class SearchInput(BaseModel):
    query: str = Field(description="A pergunta ou termo para buscar na base de conhecimento")
    k: int = Field(default=3, description="O número de documentos. DEVE ser um número inteiro.")

# 2. Aplicamos o schema à ferramenta
@tool(args_schema=SearchInput)
def search_knowledge_base(query: str, k: int = 3) -> str:
    """
    Busca informações relevantes na base de conhecimento usando RAG.
    Use para documentação técnica, currículos ou informações sobre LLMs.
    """
    try:
        # O Pydantic garantirá que 'k' chegue aqui como int, mesmo que a IA envie "3"
        if not query or not query.strip():
            return "Erro: consulta vazia"
        
        vector_store = get_vector_store()
        if vector_store is None:
            return "Erro: base de conhecimento não encontrada."

        print(f"[RAG] 🔍 Buscando: '{query}' (k={k})")
        
        # Realiza a busca
        results = vector_store.similarity_search(query.strip(), k=int(k)) # Garantimos o cast aqui também
        
        if not results:
            return "Nenhum documento relevante encontrado."

        formatted_results = []
        for i, doc in enumerate(results, 1):
            source = Path(doc.metadata.get("source", "Desconhecido")).name
            formatted_results.append(f"[Doc {i}] (Fonte: {source}): {doc.page_content}")
        
        return "\n\n".join(formatted_results)
        
    except Exception as e:
        return f"Erro técnico na busca: {str(e)}"
# Exemplo de uso
if __name__ == "__main__":
    result = search_knowledge_base.invoke({
        "query": "O que são LLMs?",
        "k": 2
    })
    print(result)