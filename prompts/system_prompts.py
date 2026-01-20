import os
from pathlib import Path

# Caminho base para os prompts
PROMPTS_DIR = Path(__file__).parent

def _load_prompt(filename: str) -> str:
    """
    Carrega um prompt de um arquivo .txt
    
    Args:
        filename: Nome do arquivo (ex: 'router_prompt.txt')
        
    Returns:
        Conteúdo do arquivo como string
    """
    file_path = PROMPTS_DIR / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo de prompt não encontrado: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        print(f"[PROMPTS] ✓ Carregado: {filename}")
        return content
        
    except Exception as e:
        print(f"[PROMPTS] ✗ Erro ao carregar {filename}: {str(e)}")
        raise

def get_router_prompt() -> str:
    """
    Retorna o prompt do sistema para o Router Agent
    
    Returns:
        String com o prompt do router
    """
    return _load_prompt("router_prompt.txt")

def get_super_agent_prompt() -> str:
    """
    Retorna o prompt do sistema para o Super Agent (executor)
    
    Returns:
        String com o prompt do super agent
    """
    return _load_prompt("super_agent_prompt.txt")

def get_rag_agent_prompt() -> str:
    """
    Retorna o prompt específico para o agente RAG
    
    Returns:
        String com o prompt do RAG agent
    """
    return _load_prompt("rag_agent_prompt.txt")


def reload_prompts():
    """
    Recarrega todos os prompts (útil para desenvolvimento)
    """
    print("\n[PROMPTS] Recarregando todos os prompts...")
    
    prompts = {
        "Router": get_router_prompt(),
        "Super Agent": get_super_agent_prompt(),
        "RAG Agent": get_rag_agent_prompt()
    }
    
    print(f"[PROMPTS] ✓ {len(prompts)} prompts recarregados com sucesso\n")
    
    return prompts

def validate_prompts():
    """
    Valida que todos os arquivos de prompt existem e são legíveis
    
    Returns:
        bool: True se todos os prompts são válidos
    """
    required_prompts = [
        "router_prompt.txt",
        "super_agent_prompt.txt",
        "rag_agent_prompt.txt"
    ]
    
    all_valid = True
    
    print("\n[PROMPTS] Validando arquivos de prompt...")
    
    for prompt_file in required_prompts:
        file_path = PROMPTS_DIR / prompt_file
        
        if not file_path.exists():
            print(f"[PROMPTS] ✗ Arquivo não encontrado: {prompt_file}")
            all_valid = False
        elif file_path.stat().st_size == 0:
            print(f"[PROMPTS] ✗ Arquivo vazio: {prompt_file}")
            all_valid = False
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content.strip()) < 50:
                        print(f"[PROMPTS]  Arquivo muito curto: {prompt_file}")
                    else:
                        print(f"[PROMPTS] ✓ Válido: {prompt_file} ({len(content)} chars)")
            except Exception as e:
                print(f"[PROMPTS] ✗ Erro ao ler {prompt_file}: {str(e)}")
                all_valid = False
    
    print()
    return all_valid

