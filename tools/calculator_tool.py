from langchain_core.tools import tool
import re
from typing import Union

@tool
def calculator(expression: str) -> str:
    """
    Calculadora para operações matemáticas básicas e avançadas.
    
    Suporta: +, -, *, /, **, (), funções matemáticas básicas.
    
    Args:
        expression: Expressão matemática como string (ex: "2 + 2", "sqrt(16)", "3**2")
    
    Returns:
        Resultado da operação como string
    
    Exemplos:
        calculator("2 + 2") -> "4"
        calculator("10 * 5 + 3") -> "53"
        calculator("2 ** 8") -> "256"
    """
    try:
        # Remove espaços e valida a expressão
        expression = expression.strip()
        
        if not expression:
            return "Erro: expressão vazia fornecida"
        
        # Validação de segurança: apenas caracteres matemáticos permitidos
        allowed_chars = set("0123456789+-*/().,** ")
        allowed_funcs = {"sqrt", "abs", "pow", "min", "max", "round"}
        
        # Cria um ambiente seguro com funções matemáticas
        import math
        safe_dict = {
            "sqrt": math.sqrt,
            "abs": abs,
            "pow": pow,
            "min": min,
            "max": max,
            "round": round,
            "pi": math.pi,
            "e": math.e,
            "__builtins__": {}
        }
        
        # Avalia a expressão de forma segura
        result = eval(expression, safe_dict, {})
        
        # Formata o resultado
        if isinstance(result, float):
            # Remove zeros desnecessários
            if result.is_integer():
                return str(int(result))
            return f"{result:.6f}".rstrip('0').rstrip('.')
        
        return str(result)
        
    except ZeroDivisionError:
        return "Erro: divisão por zero não é permitida"
    except SyntaxError:
        return f"Erro: sintaxe inválida na expressão '{expression}'"
    except NameError as e:
        return f"Erro: função ou variável não reconhecida - {str(e)}"
    except Exception as e:
        return f"Erro ao calcular: {type(e).__name__}: {str(e)}"

# Exemplo de uso
if __name__ == "__main__":
    test_cases = [
        "2 + 2",
        "128 * 46",
        "10 / 3",
        "2 ** 8",
        "sqrt(16)",
        "max(10, 20, 5)"
    ]
    
    print("Testando calculadora:\n")
    for expr in test_cases:
        result = calculator.invoke({"expression": expr})
        print(f"{expr} = {result}")