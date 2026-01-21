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
    k: int = Field(default=5, description="O número de documentos a recuperar. Use valores maiores (5-7) para respostas detalhadas.")

@tool(args_schema=SearchInput)
def search_knowledge_base(query: str, k: int = 5) -> str:
    """
    Recupera informações detalhadas da base de conhecimento (PDFs, Docs).
    Use esta ferramenta para responder sobre a carreira de Nycolas Gabriel, 
    projetos específicos, tecnologias e competências técnicas.
    """
    try:
        if not query or not query.strip():
            return "Erro: consulta vazia"
        
        vector_store = get_vector_store()
        if vector_store is None:
            return "Erro: base de conhecimento não encontrada."

        print(f"[RAG] 🔍 Buscando contexto detalhado para: '{query}' (k={k})")
        
        # Realiza a busca semântica
        results = vector_store.similarity_search(query.strip(), k=int(k))
        
        if not results:
            return "Nenhuma informação relevante encontrada nos documentos internos."

        # Construção da resposta para a LLM
        # Adicionamos uma instrução implícita no retorno da ferramenta
        header = "INFORMAÇÕES RECUPERADAS DA BASE DE CONHECIMENTO:\n"
        formatted_results = []
        
        sources = set()
        for i, doc in enumerate(results, 1):
            source_name = Path(doc.metadata.get("source", "Desconhecido")).name
            sources.add(source_name)
            content = doc.page_content.replace('\n', ' ') # Limpa quebras de linha excessivas
            formatted_results.append(f"--- TRECHO {i} [FONTE: {source_name}] ---\n{content}")
        
        context_body = "\n\n".join(formatted_results)
        footer = f"\n\nFONTES DISPONÍVEIS: {', '.join(sources)}\n"
        footer += "\nINSTRUÇÃO: Use todos os detalhes acima para fornecer uma resposta completa, rica e estruturada. Não resuma demais."

        return header + context_body + footer
        
    except Exception as e:
        return f"Erro técnico na busca: {str(e)}"

if __name__ == "__main__":
    # Teste rápido
    result = search_knowledge_base.invoke({"query": "Quem é Nycolas Gabriel?", "k": 3})
    print(result)