from typing import Annotated, List, Dict, Any, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from config.llm_factory import llm_factory
from tools.calculator_tool import calculator
from tools.rag_tool import search_knowledge_base
from tools.datetime_tool import get_current_datetime, calculate_date_difference
from tools.web_search_tool import web_search  # NOVA IMPORTAÇÃO
from agents.guardrails import InputGuardrails, OutputGuardrails, ConversationGuardrails
from agents.router_agent import RouterAgent
from prompts.system_prompts import get_super_agent_prompt, get_rag_agent_prompt

class AgentState(TypedDict):
    """Estado do agente com mensagens e contexto"""
    messages: Annotated[List[BaseMessage], add_messages]
    category: str
    error_count: int
    conversation_metadata: Dict[str, Any]

class SuperAgent:
    """
    Super Agente com Router e múltiplas ferramentas especializadas
    Agora inclui Web Search para informações atuais
    """
    
    def __init__(self, provider: str = None):
        """
        Inicializa o Super Agente com Router
        
        Args:
            provider: 'openai' ou 'groq'. Se None, usa configuração padrão
        """
        # LLM principal
        self.llm = llm_factory.create_llm(provider)
        
        # Router Agent
        self.router = RouterAgent(provider)
        
        # Ferramentas disponíveis
        self.tools = {
            "calculator": calculator,
            "rag": search_knowledge_base,
            "datetime": [get_current_datetime, calculate_date_difference],
            "web_search": web_search  # NOVA FERRAMENTA
        }
        
        # Guardrails
        self.input_guardrails = InputGuardrails()
        self.output_guardrails = OutputGuardrails()
        self.conversation_guardrails = ConversationGuardrails()
        
        # Constrói o grafo
        self.graph = self._build_graph()
        
        print(f"[SUPER AGENT] ✓ Inicializado com Router + Ferramentas especializadas")
        print(f"[SUPER AGENT] Provider: {llm_factory.get_provider_info()['provider']}")
        print(f"[SUPER AGENT] Ferramentas: CALCULATOR, RAG, WEB_SEARCH, DATETIME, DIRECT")
    
    def _build_graph(self) -> StateGraph:
        """Constrói o grafo de execução do agente com Router"""
        
        workflow = StateGraph(AgentState)
        
        # Adiciona nós
        workflow.add_node("router", self._router_node)
        workflow.add_node("calculator_agent", self._calculator_agent_node)
        workflow.add_node("rag_agent", self._rag_agent_node)
        workflow.add_node("web_search_agent", self._web_search_agent_node)  # NOVO NÓ
        workflow.add_node("datetime_agent", self._datetime_agent_node)
        workflow.add_node("direct_agent", self._direct_agent_node)
        
        # Edge inicial: sempre começa no router
        workflow.add_edge(START, "router")
        
        # Router decide qual agente chamar
        workflow.add_conditional_edges(
            "router",
            self._route_to_agent,
            {
                "CALCULATOR": "calculator_agent",
                "RAG": "rag_agent",
                "WEB_SEARCH": "web_search_agent",  # NOVA ROTA
                "DATETIME": "datetime_agent",
                "DIRECT": "direct_agent"
            }
        )
        
        # Todos os agentes terminam após executar
        workflow.add_edge("calculator_agent", END)
        workflow.add_edge("rag_agent", END)
        workflow.add_edge("web_search_agent", END)  # NOVA EDGE
        workflow.add_edge("datetime_agent", END)
        workflow.add_edge("direct_agent", END)
        
        # Compila com memória
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    def _router_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Nó do Router que classifica a pergunta
        """
        try:
            user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
            
            if not user_messages:
                return {"category": "DIRECT"}
            
            last_user_message = user_messages[-1].content
            
            # Classifica usando o Router
            category = self.router.route(last_user_message)
            
            return {"category": category}
            
        except Exception as e:
            print(f"[ROUTER NODE] ✗ Erro: {str(e)}")
            return {"category": "DIRECT"}
    
    def _route_to_agent(self, state: AgentState) -> Literal["CALCULATOR", "RAG", "WEB_SEARCH", "DATETIME", "DIRECT"]:
        """
        Função de decisão para conditional edge
        """
        category = state.get("category", "DIRECT")
        return category
    
    def _calculator_agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Agente especializado em cálculos matemáticos"""
        try:
            llm_with_calc = self.llm.bind_tools([calculator])
            system_msg = SystemMessage(content=get_super_agent_prompt() + "\n\nCATEGORIA: CALCULATOR - Use a ferramenta calculator.")
            messages = [system_msg] + state["messages"]
            
            response = llm_with_calc.invoke(messages)
            
            if response.tool_calls:
                tool_node = ToolNode([calculator])
                tool_result = tool_node.invoke({"messages": [response]})
                messages_with_result = messages + [response] + tool_result["messages"]
                final_response = self.llm.invoke(messages_with_result)
                return {"messages": [response] + tool_result["messages"] + [final_response]}
            else:
                return {"messages": [response]}
                
        except Exception as e:
            print(f"[CALCULATOR AGENT] ✗ Erro: {str(e)}")
            error_msg = self.output_guardrails.handle_error_gracefully(e, "calculator_agent")
            return {"messages": [AIMessage(content=error_msg)]}
    
    def _rag_agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Agente especializado em busca RAG"""
        try:
            llm_with_rag = self.llm.bind_tools([search_knowledge_base])
            system_msg = SystemMessage(content=get_rag_agent_prompt())
            messages = [system_msg] + state["messages"]
            
            response = llm_with_rag.invoke(messages)
            
            if response.tool_calls:
                tool_node = ToolNode([search_knowledge_base])
                tool_result = tool_node.invoke({"messages": [response]})
                messages_with_result = messages + [response] + tool_result["messages"]
                final_response = self.llm.invoke(messages_with_result)
                return {"messages": [response] + tool_result["messages"] + [final_response]}
            else:
                return {"messages": [response]}
                
        except Exception as e:
            print(f"[RAG AGENT] ✗ Erro: {str(e)}")
            error_msg = self.output_guardrails.handle_error_gracefully(e, "rag_agent")
            return {"messages": [AIMessage(content=error_msg)]}
    
    def _web_search_agent_node(self, state: AgentState) -> Dict[str, Any]:
        """
        NOVO: Agente especializado em pesquisa web para informações atuais
        """
        try:
            llm_with_web = self.llm.bind_tools([web_search])
            
            system_msg = SystemMessage(content=get_super_agent_prompt() + """

CATEGORIA: WEB_SEARCH - Use a ferramenta web_search para buscar informações atuais.

IMPORTANTE:
- Sempre cite as fontes (URLs) das informações
- Indique quando a pesquisa foi realizada
- Sintetize informações de múltiplas fontes quando relevante
- Se encontrar informações conflitantes, mencione isso
""")
            messages = [system_msg] + state["messages"]
            
            response = llm_with_web.invoke(messages)
            
            if response.tool_calls:
                tool_node = ToolNode([web_search])
                tool_result = tool_node.invoke({"messages": [response]})
                messages_with_result = messages + [response] + tool_result["messages"]
                final_response = self.llm.invoke(messages_with_result)
                return {"messages": [response] + tool_result["messages"] + [final_response]}
            else:
                return {"messages": [response]}
                
        except Exception as e:
            print(f"[WEB SEARCH AGENT] ✗ Erro: {str(e)}")
            error_msg = self.output_guardrails.handle_error_gracefully(e, "web_search_agent")
            return {"messages": [AIMessage(content=error_msg)]}
    
    def _datetime_agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Agente especializado em data/hora"""
        try:
            datetime_tools = [get_current_datetime, calculate_date_difference]
            llm_with_datetime = self.llm.bind_tools(datetime_tools)
            system_msg = SystemMessage(content=get_super_agent_prompt() + "\n\nCATEGORIA: DATETIME - Use as ferramentas de data/hora.")
            messages = [system_msg] + state["messages"]
            
            response = llm_with_datetime.invoke(messages)
            
            if response.tool_calls:
                tool_node = ToolNode(datetime_tools)
                tool_result = tool_node.invoke({"messages": [response]})
                messages_with_result = messages + [response] + tool_result["messages"]
                final_response = self.llm.invoke(messages_with_result)
                return {"messages": [response] + tool_result["messages"] + [final_response]}
            else:
                return {"messages": [response]}
                
        except Exception as e:
            print(f"[DATETIME AGENT] ✗ Erro: {str(e)}")
            error_msg = self.output_guardrails.handle_error_gracefully(e, "datetime_agent")
            return {"messages": [AIMessage(content=error_msg)]}
    
    def _direct_agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Agente para respostas diretas sem ferramentas"""
        try:
            system_msg = SystemMessage(content=get_super_agent_prompt() + "\n\nCATEGORIA: DIRECT - Responda diretamente usando seu conhecimento.")
            messages = [system_msg] + state["messages"]
            response = self.llm.invoke(messages)
            return {"messages": [response]}
                
        except Exception as e:
            print(f"[DIRECT AGENT] ✗ Erro: {str(e)}")
            error_msg = self.output_guardrails.handle_error_gracefully(e, "direct_agent")
            return {"messages": [AIMessage(content=error_msg)]}
    
    def process_message(
        self, 
        user_input: str, 
        thread_id: str = "default",
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        Processa uma mensagem do usuário com Router e Guardrails
        """
        
        # INPUT GUARDRAILS
        validation = self.input_guardrails.validate_input(user_input)
        
        if not validation["valid"]:
            return {
                "success": False,
                "response": validation["message"],
                "error": "input_validation_failed"
            }
        
        sanitized_input = validation["sanitized_input"]
        
        appropriateness = self.input_guardrails.check_message_appropriateness(sanitized_input)
        
        if not appropriateness["appropriate"]:
            return {
                "success": False,
                "response": "Desculpe, não posso processar esse tipo de conteúdo.",
                "error": appropriateness["reason"]
            }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            input_messages = [HumanMessage(content=sanitized_input)]
            
            result = self.graph.invoke(
                {
                    "messages": input_messages,
                    "category": "",
                    "error_count": 0,
                    "conversation_metadata": {}
                },
                config=config
            )
            
            messages = result.get("messages", [])
            category = result.get("category", "UNKNOWN")
            
            if not messages:
                return {
                    "success": False,
                    "response": "Erro: Nenhuma resposta foi gerada.",
                    "error": "empty_response",
                    "category": category
                }
            
            final_response = self.output_guardrails.ensure_complete_response(messages)
            output_validation = self.output_guardrails.validate_output(final_response)
            conversation_check = self.conversation_guardrails.check_conversation_length(messages)
            
            if conversation_check["warning"]:
                final_response += f"\n\n💡 {conversation_check['warning']}"
            
            if self.conversation_guardrails.detect_loops(messages):
                final_response += "\n\n⚠️ Parece que estamos em um padrão repetitivo. Posso ajudar com algo diferente?"
            
            response_dict = {
                "success": True,
                "response": output_validation["processed_response"],
                "category": category,
                "metadata": {
                    "message_count": conversation_check["message_count"],
                    "provider": llm_factory.get_provider_info()["provider"]
                }
            }
            
            if debug:
                response_dict["debug"] = {
                    "routing": category,
                    "total_messages": len(messages)
                }
            
            return response_dict
            
        except Exception as e:
            print(f"[SUPER AGENT] ✗ Erro ao processar mensagem: {str(e)}")
            error_message = self.output_guardrails.handle_error_gracefully(e, "process_message")
            return {
                "success": False,
                "response": error_message,
                "error": str(e),
                "category": "ERROR"
            }
    
    def get_conversation_history(self, thread_id: str = "default") -> List[BaseMessage]:
        """Recupera o histórico de conversação"""
        try:
            config = {"configurable": {"thread_id": thread_id}}
            state = self.graph.get_state(config)
            return state.values.get("messages", [])
        except Exception as e:
            print(f"[SUPER AGENT] ✗ Erro ao recuperar histórico: {str(e)}")
            return []
    
    def clear_conversation(self, thread_id: str = "default"):
        """Limpa a conversa de uma thread"""
        print(f"[SUPER AGENT] Conversa limpa para thread: {thread_id}")

if __name__ == "__main__":
    agent = SuperAgent()
    
    test_messages = [
        "Olá! Como você pode me ajudar?",
        "Quanto é 128 vezes 46?",
        "Me fale sobre LLMs",
        "Quem é o presidente do Brasil em 2025?",  # Agora deve usar WEB_SEARCH
        "Que horas são?",
        "Notícias sobre IA hoje",  # Deve usar WEB_SEARCH
        "Quem foi Albert Einstein?",
        "Calcule 2 elevado a 10"
    ]
    
    print("\n" + "="*60)
    print("TESTANDO SUPER AGENT COM WEB SEARCH")
    print("="*60 + "\n")
    
    for msg in test_messages:
        print(f"👤 User: {msg}")
        result = agent.process_message(msg, debug=True)
        print(f"🤖 Agent [{result.get('category', 'UNKNOWN')}]: {result['response']}")
        print(f"✓ Success: {result['success']}\n")
        print("-" * 60 + "\n")