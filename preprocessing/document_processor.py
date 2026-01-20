import os
from typing import List
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings  
from langchain_community.vectorstores import FAISS
from config.settings import settings

class DocumentProcessor:
    """Processa documentos, faz chunking e indexa no vector store"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.embedding_function = None
        
    def get_embedding_function(self):
        """Retorna instância única do OpenAI embedding model"""
        if self.embedding_function is None:
            print(f"[EMBEDDING] Inicializando OpenAI ({settings.EMBEDDING_MODEL})...")
            
            # OpenAI exige uma API Key. Certifique-se que OPENAI_API_KEY 
            # esteja no seu arquivo .env ou variáveis de ambiente.
            self.embedding_function = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL # Ex: "text-embedding-3-small"
            )
            print("[EMBEDDING] ✓ OpenAI Embeddings carregado")
        return self.embedding_function
    
    def load_document(self, file_path: str) -> List[Document]:
        """Carrega documento baseado na extensão"""
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == ".pdf":
                loader = PyPDFLoader(file_path)
            elif file_ext == ".docx":
                loader = Docx2txtLoader(file_path)
            elif file_ext == ".txt":
                loader = TextLoader(file_path, encoding="utf-8")
            else:
                raise ValueError(f"Formato não suportado: {file_ext}")
            
            documents = loader.load()
            print(f"[LOADER] ✓ {len(documents)} páginas carregadas de {Path(file_path).name}")
            return documents
            
        except Exception as e:
            print(f"[LOADER] ✗ Erro ao carregar {file_path}: {str(e)}")
            return []
    
    def load_all_documents(self, docs_path: str = None) -> List[Document]:
        """Carrega todos os documentos da pasta docs"""
        docs_path = docs_path or settings.DOCS_PATH
        all_documents = []
        
        if not os.path.exists(docs_path):
            print(f"[LOADER] ✗ Pasta {docs_path} não encontrada")
            return all_documents
        
        supported_extensions = {".pdf", ".docx", ".txt"}
        files = [f for f in Path(docs_path).glob("*") if f.suffix.lower() in supported_extensions]
        
        print(f"[LOADER] Encontrados {len(files)} documentos em {docs_path}")
        
        for file_path in files:
            docs = self.load_document(str(file_path))
            all_documents.extend(docs)
        
        print(f"[LOADER] ✓ Total: {len(all_documents)} páginas carregadas")
        return all_documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Divide documentos em chunks"""
        if not documents:
            return []
        
        chunks = self.text_splitter.split_documents(documents)
        print(f"[CHUNKING] ✓ {len(chunks)} chunks criados")
        
        # Adiciona metadados aos chunks
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = i
            chunk.metadata["chunk_size"] = len(chunk.page_content)
        
        return chunks
    
    def create_vector_store(self, chunks: List[Document]) -> FAISS:
        """Cria vector store FAISS a partir dos chunks"""
        if not chunks:
            raise ValueError("Nenhum chunk fornecido para criar vector store")
        
        embedding_function = self.get_embedding_function()
        
        print(f"[VECTOR STORE] Criando índice FAISS com {len(chunks)} chunks...")
        vector_store = FAISS.from_documents(chunks, embedding_function)
        print(f"[VECTOR STORE] ✓ Índice criado: {vector_store.index.ntotal} vetores")
        
        return vector_store
    
    def save_vector_store(self, vector_store: FAISS, path: str = None):
        """Salva vector store em disco"""
        path = path or settings.VECTOR_STORE_PATH
        
        os.makedirs(path, exist_ok=True)
        vector_store.save_local(path)
        print(f"[VECTOR STORE] ✓ Salvo em {path}")
    
    def load_vector_store(self, path: str = None) -> FAISS:
        """Carrega vector store do disco"""
        path = path or settings.VECTOR_STORE_PATH
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Vector store não encontrado em {path}")
        
        embedding_function = self.get_embedding_function()
        
        print(f"[VECTOR STORE] Carregando de {path}...")
        vector_store = FAISS.load_local(
            path, 
            embedding_function, 
            allow_dangerous_deserialization=True
        )
        print(f"[VECTOR STORE] ✓ Carregado: {vector_store.index.ntotal} vetores")
        
        return vector_store
    
    def process_and_index(self, docs_path: str = None, vector_store_path: str = None):
        """Pipeline completo: carrega, chunka e indexa documentos"""
        print("\n" + "="*50)
        print("INICIANDO PROCESSAMENTO DE DOCUMENTOS")
        print("="*50 + "\n")
        
        # Carregar documentos
        documents = self.load_all_documents(docs_path)
        
        if not documents:
            print("[PIPELINE] ✗ Nenhum documento encontrado")
            return None
        
        # Criar chunks
        chunks = self.split_documents(documents)
        
        # Criar e salvar vector store
        vector_store = self.create_vector_store(chunks)
        self.save_vector_store(vector_store, vector_store_path)
        
        print("\n" + "="*50)
        print("PROCESSAMENTO CONCLUÍDO COM SUCESSO")
        print("="*50 + "\n")
        
        return vector_store

if __name__ == "__main__":
    processor = DocumentProcessor()
    processor.process_and_index()