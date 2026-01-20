import streamlit as st
import time
from agents.super_agent import SuperAgent
from config.settings import settings
from config.llm_factory import llm_factory
import os

# Configuração da página
st.set_page_config(
    page_title="Super AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
def load_css(file_path):
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("assets/style.css")

st.markdown('<div class="main-header">🤖 Super AI Agent</div>', unsafe_allow_html=True)


# Inicialização do estado da sessão
if "agent" not in st.session_state:
    st.session_state.agent = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "streamlit-session"

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Configurações")
    
    # Seleção de Provider
    provider_options = ["groq", "openai"]
    selected_provider = st.selectbox(
        "Escolha o Provider LLM:",
        provider_options,
        index=provider_options.index(settings.LLM_PROVIDER)
    )
    
    # Informações do modelo
    st.markdown("### 📊 Informações do Sistema")
    if st.session_state.agent:
        info = llm_factory.get_provider_info()
        st.info(f"""
        **Provider:** {info['provider']}  
        **Modelo:** {info['model']}  
        **Temperatura:** {info['temperature']}  
        **Max Tokens:** {info['max_tokens']}
        """)
        
        st.markdown("**🧭 Router Ativo:**")
        st.success("O agente usa um Router inteligente para decidir qual ferramenta usar automaticamente!")
    
    st.markdown("---")
    
    # Ferramentas disponíveis
    st.markdown("### 🛠️ Ferramentas Disponíveis")
    st.markdown("""
    - 🧮 **Calculadora**: Operações matemáticas
    - 📚 **Base de Conhecimento**: Busca RAG
    - 🕐 **Data/Hora**: Informações temporais
    - 📅 **Cálculo de Datas**: Diferenças entre datas
    """)
    
    st.markdown("---")
    
    # Botão para limpar conversa
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = f"streamlit-session-{int(time.time())}"
        st.rerun()
    
    # Informações adicionais
    st.markdown("---")
    st.markdown("### ℹ️ Sobre")
    st.markdown("""
    Este é um **Super Agente de IA** equipado com múltiplas ferramentas 
    para fornecer respostas precisas e úteis.
    
    Desenvolvido com:
    - LangChain
    - LangGraph
    - Streamlit
    """)
    
    # Status do Vector Store
    st.markdown("---")
    st.markdown("### 📦 Status do Sistema")
    
    vector_store_exists = os.path.exists(settings.VECTOR_STORE_PATH)
    
    if vector_store_exists:
        st.success("✅ Base de Conhecimento Carregada")
    else:
        st.warning("⚠️ Base de Conhecimento não encontrada")
        st.info("Execute `python preprocessing/document_processor.py` para processar documentos")

# Header principal


# Inicializa o agente se necessário
if st.session_state.agent is None or settings.LLM_PROVIDER != selected_provider:
    with st.spinner(f"Inicializando agente com {selected_provider}..."):
        try:
            # Atualiza o provider nas settings
            settings.LLM_PROVIDER = selected_provider
            st.session_state.agent = SuperAgent(provider=selected_provider)
            st.success(f"✅ Agente inicializado com {selected_provider}!")
        except Exception as e:
            st.error(f"❌ Erro ao inicializar agente: {str(e)}")
            st.stop()

# Área de chat
st.markdown("### 💬 Conversa")

# Container para mensagens
chat_container = st.container()

with chat_container:
    # Exibe mensagens anteriores
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 Você:</strong><br>
                {msg["content"]}
            </div>
            """, unsafe_allow_html=True)
        elif msg["role"] == "assistant":
            success_badge = '<span class="success-badge">✓ Sucesso</span>' if msg.get("success", True) else '<span class="error-message">✗ Erro</span>'
            
            # Badge de categoria
            category = msg.get("category", "UNKNOWN")
            category_badges = {
                "CALCULATOR": '<span class="tool-badge">🧮 CALCULATOR</span>',
                "RAG": '<span class="tool-badge">📚 RAG</span>',
                "DATETIME": '<span class="tool-badge">🕐 DATETIME</span>',
                "DIRECT": '<span class="tool-badge">💭 DIRECT</span>'
            }
            category_badge = category_badges.get(category, '')
            
            st.markdown(f"""
            <div class="chat-message agent-message">
                <strong>🤖 Agente:</strong> {success_badge} {category_badge}<br>
                {msg["content"]}
            </div>
            """, unsafe_allow_html=True)

# Input do usuário
with st.container():
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_input = st.text_input(
            "Digite sua mensagem:",
            key="user_input",
            placeholder="Ex: Quanto é 128 vezes 46? / Me fale sobre LLMs / Que horas são?",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Enviar", use_container_width=True, type="primary")

# Processa a mensagem
if send_button and user_input:
    # Adiciona mensagem do usuário
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Processa com o agente
    with st.spinner("🤔 Analisando e processando..."):
        try:
            result = st.session_state.agent.process_message(
                user_input,
                thread_id=st.session_state.thread_id,
                debug=True
            )
            
            # Mostra a categoria detectada
            category = result.get("category", "UNKNOWN")
            category_icons = {
                "CALCULATOR": "🧮",
                "RAG": "📚",
                "DATETIME": "🕐",
                "DIRECT": "💭"
            }
            icon = category_icons.get(category, "❓")
            
            st.toast(f"{icon} Usando: {category}", icon="ℹ️")
            
            # Adiciona resposta do agente
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["response"],
                "success": result["success"],
                "category": result.get("category", "UNKNOWN"),
                "metadata": result.get("metadata", {})
            })
            
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Erro ao processar mensagem: {str(e)}",
                "success": False,
                "category": "ERROR"
            })
    
    # Recarrega a página para mostrar as novas mensagens
    st.rerun()

# Exemplos de uso
if len(st.session_state.messages) == 0:
    st.markdown("---")
    st.markdown("### 💡 Exemplos de perguntas:")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        **🧮 Matemática:**
        - Quanto é 128 vezes 46?
        - Calcule a raiz quadrada de 144
        - Qual é 2 elevado a 10?
        """)
    
    with col2:
        st.markdown("""
        **📚 Conhecimento:**
        - Me fale sobre LLMs
        - O que você sabe sobre IA?
        - Explique sobre embeddings
        """)
    
    with col3:
        st.markdown("""
        **🕐 Data/Hora:**
        - Que horas são?
        - Qual é a data de hoje?
        - Quantos dias entre 2024-01-01 e 2024-12-31?
        """)
        
    with col4:
        st.markdown("""
        **📄 Currículo de Nycolas:**
        - Quais são as principais habilidades de Nycolas?
        - Quais são as experiências profissionais de Nycolas?
        - Nycolas tem experiência com MCP?
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    Desenvolvido com ❤️ usando LangChain, LangGraph e Streamlit
</div>
""", unsafe_allow_html=True)