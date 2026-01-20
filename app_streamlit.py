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
    
    provider_options = ["groq", "openai"]
    selected_provider = st.selectbox(
        "Escolha o Provider LLM:",
        provider_options,
        index=provider_options.index(settings.LLM_PROVIDER)
    )
    
    if selected_provider == "openai":
        model_options = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
    elif selected_provider == "groq":
        model_options = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama-guard-4-12b"]
        
    selected_model = st.selectbox("Modelo:", model_options, index=0)
    selected_temp = st.slider("Temperatura:", min_value=0.0, max_value=1.0, value=settings.TEMPERATURE, step=0.1)

    config_changed = (
        st.session_state.get("current_provider") != selected_provider or
        st.session_state.get("current_model") != selected_model or
        st.session_state.get("current_temp") != selected_temp
    )

    if st.session_state.agent is None or config_changed:
        with st.spinner("Atualizando Agente..."):
            st.session_state.agent = SuperAgent(
                provider=selected_provider, 
                model=selected_model, 
                temperature=selected_temp
            )
            st.session_state.current_provider = selected_provider
            st.session_state.current_model = selected_model
            st.session_state.current_temp = selected_temp
            st.toast(f"Agente configurado: {selected_model}", icon="🚀")

    st.markdown("### 📊 Informações do Sistema")
    if st.session_state.agent:
        info = llm_factory.get_provider_info()
        st.info(f"**Max Tokens:** {info['max_tokens']}")
        st.success("O agente usa um Router inteligente!")
    
    st.markdown("---")
    st.markdown("### 🛠️ Ferramentas Disponíveis")
    st.markdown("""
    - 🧮 **Calculadora** | 📚 **RAG** | 🌐 **Web Search**
    - 🕐 **Data/Hora** | 📅 **Datas** | 💭 **Direta**
    """)
    
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = f"streamlit-session-{int(time.time())}"
        st.rerun()

# --- ÁREA DE CHAT ---
st.markdown("### 💬 Conversa")

# Container para mensagens (Isso permite que o chat role enquanto o input fica fixo)
chat_placeholder = st.container()

with chat_placeholder:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 Você:</strong><br>{msg["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            success_badge = '<span class="success-badge">✓ Sucesso</span>' if msg.get("success", True) else '<span class="error-message">✗ Erro</span>'
            category = msg.get("category", "UNKNOWN")
            category_badges = {
                "CALCULATOR": '<span class="tool-badge" style="background: #4CAF50;">🧮 CALCULATOR</span>',
                "RAG": '<span class="tool-badge" style="background: #2196F3;">📚 RAG</span>',
                "WEB_SEARCH": '<span class="tool-badge" style="background: #FF9800;">🌐 WEB SEARCH</span>',
                "DATETIME": '<span class="tool-badge" style="background: #9C27B0;">🕐 DATETIME</span>',
                "DIRECT": '<span class="tool-badge" style="background: #607D8B;">💭 DIRECT</span>'
            }
            badge = category_badges.get(category, '')
            st.markdown(f"""
            <div class="chat-message agent-message">
                <strong>🤖 Agente:</strong> {success_badge} {badge}<br>{msg["content"]}
            </div>
            """, unsafe_allow_html=True)

# --- INPUT FIXO NO RODAPÉ ---
# O st.chat_input fica automaticamente fixo na base da página
user_input = st.chat_input("Digite sua mensagem aqui...")

if user_input:
    # 1. Adiciona a mensagem do usuário ao estado
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 2. Rerenderiza para mostrar a pergunta do usuário antes de processar
    st.rerun()

# Lógica de processamento (Executa após o rerun se a última mensagem for do usuário)
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🤔 Analisando..."):
            try:
                result = st.session_state.agent.process_message(
                    last_user_msg,
                    thread_id=st.session_state.thread_id,
                    debug=True
                )
                
                # Salva a resposta
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["response"],
                    "success": result["success"],
                    "category": result.get("category", "UNKNOWN")
                })
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro: {str(e)}")

# Exemplos de uso (Só aparecem se o chat estiver vazio)
if len(st.session_state.messages) == 0:
    st.markdown("---")
    cols = st.columns(4)
    examples = [
        ("🧮 Calculadora", "Quanto é 128 x 46?"),
        ("📚 Rag", "Nycolas tem experiencias em projetos internacionais?"),
        ("🌐 Web", "Notícias sobre IA hoje"),
        ("🕐 Tempo", "Que horas são?")
    ]
    for col, (title, text) in zip(cols, examples):
        with col:
            st.markdown(f"**{title}**\n- {text}")