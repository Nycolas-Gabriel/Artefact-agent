from langchain_core.tools import tool
from datetime import datetime
import pytz
from pydantic import BaseModel, Field

# 1. Definimos os Schemas para forçar a IA a seguir o formato correto
class DateTimeInput(BaseModel):
    timezone: str = Field(
        default="UTC", 
        description="Fuso horário (ex: 'America/Sao_Paulo', 'Europe/London').",
        examples=["America/Sao_Paulo", "UTC"] # Ajuda a IA a entender o formato
    )

class DateDiffInput(BaseModel):
    date1: str = Field(description="Primeira data no formato YYYY-MM-DD")
    date2: str = Field(description="Segunda data no formato YYYY-MM-DD")

# 2. Aplicamos os schemas nas ferramentas
@tool(args_schema=DateTimeInput)
def get_current_datetime(timezone: str = "UTC") -> str:
    """
    Retorna a data e hora atual em um fuso horário específico.
    """
    try:
        # Limpa possíveis aspas extras ou espaços que a IA possa enviar
        clean_tz = timezone.strip().replace('"', '').replace("'", "")
        tz = pytz.timezone(clean_tz)
        now = datetime.now(tz)
        
        formatted = now.strftime("%Y-%m-%d %H:%M:%S %Z")
        return f"Data/Hora atual em {clean_tz}: {formatted}"
        
    except pytz.exceptions.UnknownTimeZoneError:
        return f"Erro: Fuso horário '{timezone}' desconhecido. Tente 'America/Sao_Paulo' ou 'UTC'."
    except Exception as e:
        return f"Erro ao obter data/hora: {str(e)}"

@tool(args_schema=DateDiffInput)
def calculate_date_difference(date1: str, date2: str) -> str:
    """
    Calcula a diferença em dias entre duas datas (YYYY-MM-DD).
    """
    try:
        d1 = datetime.strptime(date1.strip(), "%Y-%m-%d")
        d2 = datetime.strptime(date2.strip(), "%Y-%m-%d")
        
        diff = abs((d2 - d1).days)
        return f"Diferença entre {date1} e {date2}: {diff} dias"
        
    except ValueError:
        return f"Erro: Formato de data inválido. Use YYYY-MM-DD."
    except Exception as e:
        return f"Erro ao calcular diferença: {str(e)}"