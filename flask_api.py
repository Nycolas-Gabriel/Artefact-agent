from flask import Flask, request, jsonify
from flask_cors import CORS
from agents.super_agent import SuperAgent
from config.settings import settings
import uuid
from typing import Dict
import traceback

app = Flask(__name__)
CORS(app)  # Habilita CORS para chamadas de frontend

# Armazena instâncias de agentes por sessão
agents: Dict[str, SuperAgent] = {}

def get_or_create_agent(session_id: str, provider: str = None) -> SuperAgent:
    """
    Retorna ou cria uma instância do agente para a sessão
    """
    if session_id not in agents:
        agents[session_id] = SuperAgent(provider=provider)
    return agents[session_id]

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        "status": "healthy",
        "provider": settings.LLM_PROVIDER,
        "version": "1.0.0"
    }), 200

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Endpoint principal para chat
    
    Body JSON:
    {
        "message": "Sua mensagem aqui",
        "session_id": "optional-session-id",
        "provider": "openai" ou "groq" (opcional)
    }
    
    Response:
    {
        "success": true,
        "response": "Resposta do agente",
        "session_id": "session-id",
        "metadata": {}
    }
    """
    try:
        # Valida request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Body JSON não fornecido"
            }), 400
        
        message = data.get("message")
        
        if not message:
            return jsonify({
                "success": False,
                "error": "Campo 'message' é obrigatório"
            }), 400
        
        # Session ID
        session_id = data.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Provider (opcional)
        provider = data.get("provider")
        
        # Obtém ou cria agente
        agent = get_or_create_agent(session_id, provider)
        
        # Processa mensagem
        result = agent.process_message(
            user_input=message,
            thread_id=session_id
        )
        
        # Prepara resposta
        response_data = {
            "success": result["success"],
            "response": result["response"],
            "session_id": session_id,
            "metadata": result.get("metadata", {})
        }
        
        if not result["success"]:
            response_data["error"] = result.get("error", "unknown_error")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"[API] Erro no endpoint /chat: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "error": f"Erro interno do servidor: {str(e)}",
            "type": type(e).__name__
        }), 500

@app.route('/api/history/<session_id>', methods=['GET'])
def get_history(session_id: str):
    """
    Retorna o histórico de uma sessão
    
    Response:
    {
        "success": true,
        "session_id": "session-id",
        "messages": [...]
    }
    """
    try:
        if session_id not in agents:
            return jsonify({
                "success": False,
                "error": "Sessão não encontrada"
            }), 404
        
        agent = agents[session_id]
        history = agent.get_conversation_history(thread_id=session_id)
        
        # Serializa mensagens
        messages = []
        for msg in history:
            messages.append({
                "type": msg.__class__.__name__,
                "content": msg.content
            })
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "messages": messages,
            "count": len(messages)
        }), 200
        
    except Exception as e:
        print(f"[API] Erro no endpoint /history: {str(e)}")
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/clear/<session_id>', methods=['POST'])
def clear_conversation(session_id: str):
    """
    Limpa a conversa de uma sessão
    
    Response:
    {
        "success": true,
        "message": "Conversa limpa com sucesso"
    }
    """
    try:
        if session_id not in agents:
            return jsonify({
                "success": False,
                "error": "Sessão não encontrada"
            }), 404
        
        agent = agents[session_id]
        agent.clear_conversation(thread_id=session_id)
        
        return jsonify({
            "success": True,
            "message": "Conversa limpa com sucesso",
            "session_id": session_id
        }), 200
        
    except Exception as e:
        print(f"[API] Erro no endpoint /clear: {str(e)}")
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """
    Lista todas as sessões ativas
    
    Response:
    {
        "success": true,
        "sessions": ["session-1", "session-2", ...],
        "count": 2
    }
    """
    return jsonify({
        "success": True,
        "sessions": list(agents.keys()),
        "count": len(agents)
    }), 200

@app.route('/api/provider', methods=['GET', 'POST'])
def manage_provider():
    """
    GET: Retorna o provider atual
    POST: Atualiza o provider
    
    Body (POST):
    {
        "provider": "openai" ou "groq"
    }
    """
    if request.method == 'GET':
        from config.llm_factory import llm_factory
        
        return jsonify({
            "success": True,
            "provider_info": llm_factory.get_provider_info()
        }), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        new_provider = data.get("provider")
        
        if new_provider not in ["openai", "groq"]:
            return jsonify({
                "success": False,
                "error": "Provider deve ser 'openai' ou 'groq'"
            }), 400
        
        settings.LLM_PROVIDER = new_provider
        
        return jsonify({
            "success": True,
            "message": f"Provider alterado para {new_provider}",
            "provider": new_provider
        }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint não encontrado"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Erro interno do servidor"
    }), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 INICIANDO FLASK API")
    print("="*50)
    print(f"Provider: {settings.LLM_PROVIDER}")
    print(f"Modelo: {settings.OPENAI_MODEL if settings.LLM_PROVIDER == 'openai' else settings.GROQ_MODEL}")
    print("\nEndpoints disponíveis:")
    print("  - GET  /health")
    print("  - POST /api/chat")
    print("  - GET  /api/history/<session_id>")
    print("  - POST /api/clear/<session_id>")
    print("  - GET  /api/sessions")
    print("  - GET/POST /api/provider")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)