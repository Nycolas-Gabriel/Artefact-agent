"""
Exemplo demonstrando o workflow JSON → TOON → JSON

Este exemplo mostra como:
1. Trabalhar com dados em JSON programaticamente
2. Converter para TOON antes de enviar para LLM
3. Receber resposta e converter de volta para JSON
"""

from utils.toon_converter import TOONConverter, TOONPromptBuilder
import json

def example_1_basic_conversion():
    """Exemplo 1: Conversão básica JSON → TOON"""
    print("\n" + "="*60)
    print("EXEMPLO 1: Conversão Básica JSON → TOON")
    print("="*60 + "\n")
    
    # Dados em JSON (como trabalhamos programaticamente)
    user_data = {
        "name": "João Silva",
        "query": "Quanto é 128 vezes 46?",
        "timestamp": "2024-01-15T10:30:00",
        "metadata": {
            "session_id": "abc123",
            "platform": "web"
        }
    }
    
    print("📦 Dados originais (JSON):")
    print(json.dumps(user_data, indent=2, ensure_ascii=False))
    
    # Converte para TOON antes de enviar para LLM
    toon_format = TOONConverter.json_to_toon(user_data)
    
    print("\n📤 Formato TOON (enviado para LLM):")
    print(toon_format)
    
    print("\n✅ Vantagem: LLMs processam TOON melhor que JSON puro")

def example_2_structured_output():
    """Exemplo 2: Saída estruturada com schema"""
    print("\n" + "="*60)
    print("EXEMPLO 2: Saída Estruturada com Schema")
    print("="*60 + "\n")
    
    # Definimos o schema da resposta esperada (em JSON)
    output_schema = {
        "category": "string (CALCULATOR|RAG|DATETIME|DIRECT)",
        "confidence": "float (0.0-1.0)",
        "reasoning": "string",
        "suggested_tools": "array of strings"
    }
    
    # Input data
    input_data = {
        "user_query": "Me fale sobre Large Language Models",
        "context": "technical_documentation"
    }
    
    # Constrói prompt estruturado em TOON
    structured_prompt = TOONPromptBuilder.build_structured_prompt(
        task="Classify the user query and suggest appropriate tools",
        input_data=input_data,
        output_schema=output_schema
    )
    
    print("📤 Prompt enviado para LLM (TOON):")
    print(structured_prompt)
    
    print("\n💡 O LLM receberá um prompt claramente estruturado")
    print("💡 E responderá em JSON matching o schema")

def example_3_tool_call_workflow():
    """Exemplo 3: Workflow completo de chamada de ferramenta"""
    print("\n" + "="*60)
    print("EXEMPLO 3: Workflow Completo de Tool Call")
    print("="*60 + "\n")
    
    # Passo 1: Router classifica (trabalha em JSON)
    router_input = {
        "query": "Calcule a raiz quadrada de 144",
        "user_id": "user_123"
    }
    
    print("1️⃣ Router recebe input (JSON):")
    print(json.dumps(router_input, indent=2, ensure_ascii=False))
    
    # Passo 2: Converte para TOON e envia para LLM
    toon_input = TOONConverter.json_to_toon(router_input)
    print("\n2️⃣ Convertido para TOON:")
    print(toon_input)
    
    # Passo 3: LLM responde (simulado)
    llm_response_json = {
        "category": "CALCULATOR",
        "confidence": 0.98,
        "tool_call": {
            "name": "calculator",
            "arguments": {
                "expression": "sqrt(144)"
            }
        }
    }
    
    print("\n3️⃣ LLM responde em JSON:")
    print(json.dumps(llm_response_json, indent=2, ensure_ascii=False))
    
    # Passo 4: Preparamos a tool call em TOON
    tool_call_toon = TOONConverter.tool_call_to_toon(
        llm_response_json["tool_call"]["name"],
        llm_response_json["tool_call"]["arguments"]
    )
    
    print("\n4️⃣ Tool call formatado em TOON:")
    print(tool_call_toon)
    
    # Passo 5: Executamos a tool e trabalhamos em JSON
    tool_result = {"result": 12.0, "status": "success"}
    
    print("\n5️⃣ Tool retorna resultado (JSON):")
    print(json.dumps(tool_result, indent=2, ensure_ascii=False))
    
    print("\n✅ Todo o workflow mantém dados em JSON")
    print("✅ TOON é usado apenas na comunicação com LLM")

def example_4_real_world_scenario():
    """Exemplo 4: Cenário real com Router Agent"""
    print("\n" + "="*60)
    print("EXEMPLO 4: Cenário Real - Router Agent")
    print("="*60 + "\n")
    
    # Aplicação trabalha em JSON
    application_state = {
        "user_query": "Qual é a diferença entre 2024-12-31 e 2024-01-01?",
        "session": {
            "id": "session_456",
            "history_count": 5
        },
        "user_preferences": {
            "language": "pt-BR",
            "timezone": "America/Sao_Paulo"
        }
    }
    
    print("📱 Estado da aplicação (JSON):")
    print(json.dumps(application_state, indent=2, ensure_ascii=False))
    
    # Preparamos para enviar ao Router
    router_prompt_data = {
        "query": application_state["user_query"],
        "context": {
            "has_history": application_state["session"]["history_count"] > 0,
            "language": application_state["user_preferences"]["language"]
        }
    }
    
    # Schema esperado da resposta
    response_schema = {
        "category": "string",
        "confidence": "float",
        "reasoning": "string"
    }
    
    # Constrói prompt TOON
    toon_prompt = TOONPromptBuilder.build_structured_prompt(
        task="Classify this query into the most appropriate category",
        input_data=router_prompt_data,
        output_schema=response_schema,
        examples=[
            {
                "input": {"query": "What's the difference between two dates?"},
                "output": {
                    "category": "DATETIME",
                    "confidence": 0.95,
                    "reasoning": "Date calculation detected"
                }
            }
        ]
    )
    
    print("\n📤 Prompt enviado ao LLM (TOON):")
    print(toon_prompt[:500] + "...")
    
    # LLM responde
    llm_response = {
        "category": "DATETIME",
        "confidence": 0.97,
        "reasoning": "User is asking to calculate difference between two dates"
    }
    
    print("\n📥 Resposta do LLM (JSON parseado):")
    print(json.dumps(llm_response, indent=2, ensure_ascii=False))
    
    # Aplicação continua trabalhando em JSON
    application_state["routing_decision"] = llm_response
    application_state["next_agent"] = llm_response["category"].lower() + "_agent"
    
    print("\n📱 Estado atualizado da aplicação (JSON):")
    print(json.dumps(application_state, indent=2, ensure_ascii=False))
    
    print("\n" + "="*60)
    print("RESUMO DO WORKFLOW")
    print("="*60)
    print("✅ Aplicação trabalha 100% em JSON")
    print("✅ TOON usado apenas para comunicação com LLM")
    print("✅ Parsing de volta para JSON automático")
    print("✅ Estrutura clara e type-safe")

if __name__ == "__main__":
    # Executa todos os exemplos
    example_1_basic_conversion()
    example_2_structured_output()
    example_3_tool_call_workflow()
    example_4_real_world_scenario()
    
    print("\n\n" + "="*60)
    print("🎯 CONCLUSÃO")
    print("="*60)
    print("""
O workflow JSON → TOON → JSON oferece:

1. ✅ Trabalho programático em JSON (type-safe, fácil manipular)
2. ✅ Comunicação otimizada com LLM (TOON é mais legível)
3. ✅ Parsing automático de volta para JSON
4. ✅ Schemas claros para validação
5. ✅ Melhor performance e accuracy do LLM

Este é o padrão recomendado para aplicações profissionais!
    """)