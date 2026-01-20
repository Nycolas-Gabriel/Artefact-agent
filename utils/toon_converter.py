import json
from typing import Any, Dict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage

class TOONConverter:
    """
    Conversor JSON ↔ TOON (Text-Optimized Object Notation)
    
    Converte estruturas JSON para formato TOON otimizado para LLMs
    e vice-versa, seguindo as melhores práticas de comunicação com LLMs.
    """
    
    @staticmethod
    def json_to_toon(data: Dict[str, Any], indent: int = 0) -> str:
        """
        Converte JSON para formato TOON (similar a XML/YAML humanizado)
        
        Args:
            data: Dicionário JSON para converter
            indent: Nível de indentação atual
            
        Returns:
            String no formato TOON
        """
        toon_lines = []
        spacing = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                # Objeto nested
                toon_lines.append(f"{spacing}<{key}>")
                toon_lines.append(TOONConverter.json_to_toon(value, indent + 1))
                toon_lines.append(f"{spacing}</{key}>")
                
            elif isinstance(value, list):
                # Array
                toon_lines.append(f"{spacing}<{key}>")
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        toon_lines.append(f"{spacing}  <item index=\"{i}\">")
                        toon_lines.append(TOONConverter.json_to_toon(item, indent + 2))
                        toon_lines.append(f"{spacing}  </item>")
                    else:
                        toon_lines.append(f"{spacing}  <item index=\"{i}\">{item}</item>")
                toon_lines.append(f"{spacing}</{key}>")
                
            elif value is None:
                toon_lines.append(f"{spacing}<{key}>null</{key}>")
                
            elif isinstance(value, bool):
                toon_lines.append(f"{spacing}<{key}>{str(value).lower()}</{key}>")
                
            else:
                # Valores primitivos (string, number)
                toon_lines.append(f"{spacing}<{key}>{value}</{key}>")
        
        return "\n".join(toon_lines)
    
    @staticmethod
    def toon_to_json(toon_text: str) -> Dict[str, Any]:
        """
        Converte TOON de volta para JSON
        
        Args:
            toon_text: String no formato TOON
            
        Returns:
            Dicionário JSON
        """
        # Implementação simplificada - em produção usar parser XML robusto
        # Para este projeto, focamos no fluxo JSON → TOON → LLM
        # A resposta da LLM já vem em formato JSON estruturado
        try:
            # Tenta extrair JSON se estiver embutido
            import re
            json_match = re.search(r'\{.*\}', toon_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except:
            return {}
    
    @staticmethod
    def message_to_toon(message: BaseMessage) -> str:
        """
        Converte uma mensagem LangChain para formato TOON
        
        Args:
            message: Mensagem LangChain
            
        Returns:
            String TOON formatada
        """
        msg_type = message.__class__.__name__
        
        toon = f"<message type=\"{msg_type}\">\n"
        toon += f"  <content>{message.content}</content>\n"
        
        # Adiciona metadata se existir
        if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
            toon += "  <metadata>\n"
            toon += TOONConverter.json_to_toon(message.additional_kwargs, indent=2)
            toon += "\n  </metadata>\n"
        
        toon += "</message>"
        
        return toon
    
    @staticmethod
    def tool_call_to_toon(tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Converte chamada de ferramenta para TOON
        
        Args:
            tool_name: Nome da ferramenta
            tool_args: Argumentos da ferramenta
            
        Returns:
            String TOON formatada
        """
        toon = f"<tool_call>\n"
        toon += f"  <name>{tool_name}</name>\n"
        toon += f"  <arguments>\n"
        toon += TOONConverter.json_to_toon(tool_args, indent=2)
        toon += "\n  </arguments>\n"
        toon += "</tool_call>"
        
        return toon
    
    @staticmethod
    def structured_output_to_toon(data: Dict[str, Any], schema_name: str = "output") -> str:
        """
        Converte saída estruturada para TOON com schema
        
        Args:
            data: Dados estruturados
            schema_name: Nome do schema
            
        Returns:
            String TOON com schema
        """
        toon = f"<{schema_name}>\n"
        toon += TOONConverter.json_to_toon(data, indent=1)
        toon += f"\n</{schema_name}>"
        
        return toon


class TOONPromptBuilder:
    """
    Builder para criar prompts otimizados com formato TOON
    """
    
    @staticmethod
    def build_structured_prompt(
        task: str,
        input_data: Dict[str, Any],
        output_schema: Dict[str, Any],
        examples: List[Dict[str, Any]] = None
    ) -> str:
        """
        Constrói um prompt estruturado com TOON
        
        Args:
            task: Descrição da tarefa
            input_data: Dados de entrada em JSON
            output_schema: Schema esperado de saída
            examples: Exemplos opcionais
            
        Returns:
            Prompt formatado em TOON
        """
        prompt_parts = []
        
        # Task description
        prompt_parts.append(f"<task>\n{task}\n</task>\n")
        
        # Input data
        prompt_parts.append("<input>")
        prompt_parts.append(TOONConverter.json_to_toon(input_data, indent=1))
        prompt_parts.append("</input>\n")
        
        # Examples (if provided)
        if examples:
            prompt_parts.append("<examples>")
            for i, example in enumerate(examples):
                prompt_parts.append(f"  <example index=\"{i}\">")
                prompt_parts.append(TOONConverter.json_to_toon(example, indent=2))
                prompt_parts.append("  </example>")
            prompt_parts.append("</examples>\n")
        
        # Output schema
        prompt_parts.append("<output_schema>")
        prompt_parts.append(TOONConverter.json_to_toon(output_schema, indent=1))
        prompt_parts.append("</output_schema>\n")
        
        # Instructions
        prompt_parts.append("<instructions>")
        prompt_parts.append("Please provide your response in valid JSON format matching the output_schema.")
        prompt_parts.append("</instructions>")
        
        return "\n".join(prompt_parts)


# Exemplo de uso
if __name__ == "__main__":
    print("="*60)
    print("TESTANDO TOON CONVERTER")
    print("="*60 + "\n")
    
    # Exemplo 1: Conversão simples
    data = {
        "query": "Quanto é 2 + 2?",
        "category": "CALCULATOR",
        "metadata": {
            "timestamp": "2024-01-15T10:30:00",
            "user_id": "123"
        }
    }
    
    print("1. JSON → TOON:")
    print("-" * 60)
    toon = TOONConverter.json_to_toon(data)
    print(toon)
    print()
    
    # Exemplo 2: Tool call
    print("2. Tool Call → TOON:")
    print("-" * 60)
    tool_toon = TOONConverter.tool_call_to_toon(
        "calculator",
        {"expression": "2 + 2"}
    )
    print(tool_toon)
    print()
    
    # Exemplo 3: Structured prompt
    print("3. Structured Prompt Builder:")
    print("-" * 60)
    prompt = TOONPromptBuilder.build_structured_prompt(
        task="Classify the user query into one of the categories",
        input_data={"query": "What is 2 + 2?"},
        output_schema={
            "category": "string (CALCULATOR|RAG|DATETIME|DIRECT)",
            "confidence": "float (0.0-1.0)"
        },
        examples=[
            {
                "input": {"query": "Calculate 5 * 5"},
                "output": {"category": "CALCULATOR", "confidence": 0.95}
            }
        ]
    )
    print(prompt)