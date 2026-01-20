from typing import Dict, Any, List
from langchain_core.messages import BaseMessage, AIMessage
import re

class InputGuardrails:
    """Guardrails para validação de entrada do usuário"""
    
    @staticmethod
    def validate_input(user_input: str) -> Dict[str, Any]:
        """
        Valida e sanitiza a entrada do usuário
        
        Returns:
            dict com 'valid', 'message', 'sanitized_input'
        """
        # Verifica se entrada está vazia
        if not user_input or not user_input.strip():
            return {
                "valid": False,
                "message": "Por favor, digite uma mensagem válida.",
                "sanitized_input": None
            }
        
        # Limita tamanho da entrada
        max_length = 10000
        if len(user_input) > max_length:
            return {
                "valid": False,
                "message": f"Mensagem muito longa. Máximo permitido: {max_length} caracteres.",
                "sanitized_input": None
            }
        
        # Remove caracteres de controle perigosos
        sanitized = user_input.strip()
        
        # Detecta possíveis tentativas de injection
        injection_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                return {
                    "valid": False,
                    "message": "Entrada contém conteúdo potencialmente perigoso.",
                    "sanitized_input": None
                }
        
        return {
            "valid": True,
            "message": "Entrada válida",
            "sanitized_input": sanitized
        }
    
    @staticmethod
    def check_message_appropriateness(user_input: str) -> Dict[str, Any]:
        """
        Verifica se a mensagem é apropriada (básico)
        
        Returns:
            dict com 'appropriate' e 'reason'
        """
        # Lista básica de palavras/padrões inapropriados
        # Em produção, use uma lista mais completa ou serviço de moderação
        inappropriate_patterns = [
            # Adicione padrões conforme necessário
        ]
        
        lower_input = user_input.lower()
        
        for pattern in inappropriate_patterns:
            if pattern in lower_input:
                return {
                    "appropriate": False,
                    "reason": "Conteúdo inapropriado detectado"
                }
        
        return {
            "appropriate": True,
            "reason": "Conteúdo apropriado"
        }


class OutputGuardrails:
    """Guardrails para validação e processamento de saída"""
    
    @staticmethod
    def validate_output(response: str) -> Dict[str, Any]:
        """
        Valida a resposta da IA antes de enviar ao usuário
        
        Returns:
            dict com 'valid', 'message', 'processed_response'
        """
        if not response or not response.strip():
            return {
                "valid": False,
                "message": "Resposta vazia gerada",
                "processed_response": "Desculpe, não consegui gerar uma resposta adequada. Por favor, tente reformular sua pergunta."
            }
        
        # Verifica truncamento
        if len(response) < 10:
            return {
                "valid": False,
                "message": "Resposta muito curta (possível truncamento)",
                "processed_response": f"{response}\n\n[Nota: A resposta pode ter sido truncada. Tente fazer uma pergunta mais específica.]"
            }
        
        return {
            "valid": True,
            "message": "Resposta válida",
            "processed_response": response.strip()
        }
    
    @staticmethod
    def handle_error_gracefully(error: Exception, context: str = "") -> str:
        """
        Converte erros em mensagens amigáveis para o usuário
        
        Args:
            error: Exceção capturada
            context: Contexto onde o erro ocorreu
            
        Returns:
            Mensagem amigável para o usuário
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Mapeamento de erros conhecidos
        friendly_messages = {
            "RateLimitError": "Desculpe, estou recebendo muitas requisições no momento. Por favor, aguarde alguns segundos e tente novamente.",
            "TimeoutError": "A requisição demorou muito para ser processada. Por favor, tente uma pergunta mais simples ou tente novamente.",
            "AuthenticationError": "Erro de autenticação com o serviço de IA. Por favor, verifique as configurações.",
            "InvalidRequestError": "Sua requisição não pôde ser processada. Por favor, reformule sua pergunta.",
            "APIError": "Erro temporário ao comunicar com o serviço de IA. Por favor, tente novamente em alguns instantes.",
        }
        
        if error_type in friendly_messages:
            base_message = friendly_messages[error_type]
        else:
            base_message = "Desculpe, ocorreu um erro ao processar sua solicitação."
        
        # Adiciona contexto técnico se disponível
        technical_info = f"\n\n[Detalhes técnicos: {error_type}"
        if context:
            technical_info += f" em {context}"
        technical_info += "]"
        
        return base_message + technical_info
    
    @staticmethod
    def ensure_complete_response(messages: List[BaseMessage]) -> str:
        """
        Garante que a resposta esteja completa e não truncada
        
        Args:
            messages: Lista de mensagens da conversa
            
        Returns:
            Resposta processada
        """
        if not messages:
            return "Erro: Nenhuma resposta foi gerada."
        
        # Pega a última mensagem da IA
        last_message = messages[-1]
        
        if isinstance(last_message, AIMessage):
            content = last_message.content
            
            # Verifica se termina abruptamente
            if content and not content.rstrip().endswith((".", "!", "?", ":", ")")):
                content += "\n\n[Nota: A resposta pode estar incompleta devido a limitações de tamanho.]"
            
            return content
        
        return "Erro: Formato de resposta inesperado."


class ConversationGuardrails:
    """Guardrails para gerenciar a conversa como um todo"""
    
    @staticmethod
    def check_conversation_length(messages: List[BaseMessage], max_turns: int = 50) -> Dict[str, Any]:
        """
        Verifica se a conversa está muito longa
        
        Returns:
            dict com 'should_summarize', 'message_count'
        """
        message_count = len(messages)
        
        return {
            "should_summarize": message_count > max_turns,
            "message_count": message_count,
            "warning": f"Conversa com {message_count} mensagens. Considere iniciar uma nova conversa para melhor performance." if message_count > max_turns else None
        }
    
    @staticmethod
    def detect_loops(messages: List[BaseMessage], window: int = 6) -> bool:
        """
        Detecta se a conversa está em loop
        
        Args:
            messages: Lista de mensagens
            window: Tamanho da janela para verificar repetições
            
        Returns:
            True se detectar loop
        """
        if len(messages) < window:
            return False
        
        recent_messages = [m.content for m in messages[-window:]]
        
        # Verifica repetições exatas
        unique_messages = set(recent_messages)
        
        if len(unique_messages) <= 2:  # Muito pouca variação
            return True
        
        return False