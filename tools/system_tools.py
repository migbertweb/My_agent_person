import subprocess
import re
from datetime import datetime
from tools.toolkit import Tool, Toolkit
from tools.web_search import create_web_search_tool
from utils.config import ALLOWED_COMMANDS
from utils.logger import logger


# Palabras que indican que el "comando" es lenguaje natural, no un comando real
_NATURAL_LANG_PATTERNS = re.compile(
    r"^(dame|dime|busca|encuentra|escribe|genera|crea|haz|di|quiero|necesito|"
    r"comando|mensaje|texto|frase|oración|parrafo|párrafo|responde|"
    r"capitals|ciudad|país|capital|europa|mundo|"
    r"hola|gracias|por favor|ayuda|"
    r"completo|ejecutar|ejemplo)\b",
    re.IGNORECASE
)

# Palabras clave que indican una petición de conocimiento, no un comando
_KNOWLEDGE_KEYWORDS = re.compile(
    r"\b(qué|que|cómo|como|cuál|cual|cuando|cuándo|dónde|donde|quién|quien|"
    r"explica|significa|definición|diferencia|cuanto|cuánto|"
    r"capitales|población|historia|fecha|año|mes|día)\b",
    re.IGNORECASE
)


def _is_natural_language(text: str) -> bool:
    """Detecta si el texto parece lenguaje natural en lugar de un comando"""
    if len(text) > 50:
        return True
    
    if _NATURAL_LANG_PATTERNS.match(text):
        return True
    
    if _KNOWLEDGE_KEYWORDS.search(text) and not any(
        text.startswith(cmd) for cmd in ALLOWED_COMMANDS
    ):
        return True
    
    return False


def get_current_time() -> str:
    now = datetime.now()
    return now.strftime("%H:%M:%S")


def get_current_date() -> str:
    now = datetime.now()
    return now.strftime("%Y-%m-%d")


def get_datetime_full() -> str:
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S %A")


def execute_safe_command(command) -> str:
    """Ejecuta un comando del sistema de forma segura"""
    # Manejar caso donde command es un diccionario (error del modelo pasando schema en lugar de valor)
    if isinstance(command, dict):
        logger.warning(f"Argumento command es un diccionario: {command}")
        if "command" in command and isinstance(command["command"], str):
            command = command["command"]
        elif "description" in command and isinstance(command["description"], str):
            command = command["description"]
        else:
            command = str(command)
    
    command = str(command).strip() if command else ""
    
    if not command:
        return "Error: No se especificó ningún comando"

    # Detectar lenguaje natural y redirigir al modelo
    if _is_natural_language(command):
        logger.info(f"Lenguaje natural detectado, redirigiendo al modelo: '{command[:60]}'")
        return "NO_SE_NECESITA_HERRAMIENTA: Esto parece una pregunta de conocimiento general. Responde directamente usando tu propia base de datos."
    
    cmd = command.split()[0]

    if cmd not in ALLOWED_COMMANDS:
        logger.security(f"Comando bloqueado: {command}")
        return f"NO_SE_NECESITA_HERRAMIENTA: '{command}' no es un comando válido. Los comandos permitidos son: {', '.join(ALLOWED_COMMANDS)}. Responde usando tu conocimiento."

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip() if result.stdout else "Comando ejecutado correctamente"
        else:
            return f"Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Comando tardó demasiado"
    except Exception as e:
        logger.error(f"Error ejecutando comando: {e}")
        return f"Error: {str(e)}"


def create_system_tools() -> Toolkit:
    toolkit = Toolkit()

    toolkit.register(Tool(
        name="get_current_time",
        description="Obtiene la hora actual del sistema",
        parameters={"type": "object", "properties": {}, "required": []},
        handler=lambda: get_current_time()
    ))

    toolkit.register(Tool(
        name="get_current_date",
        description="Obtiene la fecha actual del sistema",
        parameters={"type": "object", "properties": {}, "required": []},
        handler=lambda: get_current_date()
    ))

    toolkit.register(Tool(
        name="get_datetime_full",
        description="Obtiene la fecha y hora completa actual",
        parameters={"type": "object", "properties": {}, "required": []},
        handler=lambda: get_datetime_full()
    ))

    toolkit.register(create_web_search_tool())

    toolkit.register(Tool(
        name="execute_command",
        description="Ejecuta comandos del sistema permitidos del listado: date, time, cal, echo, ls, pwd, whoami, uname, cat",
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Comando completo a ejecutar (ej: 'date', 'time', 'ls -la', 'echo hola')"
                }
            },
            "required": ["command"]
        },
        handler=lambda command: execute_safe_command(command)
    ))

    # --- Gog tools ---
    from tools import gog_tools
    toolkit.register(Tool(
        name="gog_gmail_search",
        description="Buscar correos en Gmail con query avanzada y max_results (usa 'from:', 'subject:', etc)",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Query de búsqueda Gmail, por ejemplo 'from:amazon.com' o 'subject:factura'"},
                "max_results": {"type": "integer", "description": "Máximo de resultados (default 10)", "default": 10},
                "account": {"type": "string", "description": "Cuenta Google opcional (email)"}
            },
            "required": ["query"]
        },
        handler=lambda query, max_results=10, account=None: gog_tools.gog_gmail_search(query, max_results, account)
    ))
    toolkit.register(Tool(
        name="gog_gmail_send",
        description="Enviar un correo desde Gmail (requiere: to, subject, body)",
        parameters={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Email destinatario"},
                "subject": {"type": "string", "description": "Asunto del correo"},
                "body": {"type": "string", "description": "Contenido del correo"},
                "account": {"type": "string", "description": "Cuenta Google opcional (email)"}
            },
            "required": ["to", "subject", "body"]
        },
        handler=lambda to, subject, body, account=None: gog_tools.gog_gmail_send(to, subject, body, account)
    ))
    toolkit.register(Tool(
        name="gog_calendar_events",
        description="Listar eventos de Google Calendar en un rango de fechas",
        parameters={
            "type": "object",
            "properties": {
                "calendar_id": {"type": "string", "description": "ID del calendario (o email)"},
                "date_from": {"type": "string", "description": "Fecha inicio (ISO: YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS)"},
                "date_to": {"type": "string", "description": "Fecha fin (ISO: YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS)"},
                "account": {"type": "string", "description": "Cuenta Google opcional (email)"}
            },
            "required": ["calendar_id", "date_from", "date_to"]
        },
        handler=lambda calendar_id, date_from, date_to, account=None: gog_tools.gog_calendar_events(calendar_id, date_from, date_to, account)
    ))

    toolkit.register(Tool(
        name="gog_contacts_list",
        description="Listar contactos de Google Contacts (máx 20 por defecto)",
        parameters={
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "description": "Máximo de contactos a listar (def 20)", "default": 20},
                "account": {"type": "string", "description": "Cuenta Google opcional (email)"}
            },
            "required": []
        },
        handler=lambda max_results=20, account=None: gog_tools.gog_contacts_list(max_results, account)
    ))
    toolkit.register(Tool(
        name="gog_drive_search",
        description="Buscar archivos en Google Drive por query y max_results",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Consulta de búsqueda (ej: name:reporte.pdf)"},
                "max_results": {"type": "integer", "description": "Máximo de resultados (def 10)", "default": 10},
                "account": {"type": "string", "description": "Cuenta Google opcional (email)"}
            },
            "required": ["query"]
        },
        handler=lambda query, max_results=10, account=None: gog_tools.gog_drive_search(query, max_results, account)
    ))
    toolkit.register(Tool(
        name="gog_sheets_get",
        description="Leer un rango de celdas de una hoja de Google Sheets.",
        parameters={
            "type": "object",
            "properties": {
                "sheet_id": {"type": "string", "description": "ID de la hoja de cálculo (Google Sheet)"},
                "range_": {"type": "string", "description": "Rango a leer, ej: 'Hoja1!A1:B2'"},
                "account": {"type": "string", "description": "Cuenta Google opcional (email)"},
                "as_json": {"type": "boolean", "description": "Devolver en JSON (default True)", "default": True}
            },
            "required": ["sheet_id", "range_" ]
        },
        handler=lambda sheet_id, range_, account=None, as_json=True: gog_tools.gog_sheets_get(sheet_id, range_, account, as_json)
    ))
    toolkit.register(Tool(
        name="gog_sheets_update",
        description="Actualizar un rango de celdas en Google Sheets.",
        parameters={
            "type": "object",
            "properties": {
                "sheet_id": {"type": "string", "description": "ID de la hoja de cálculo"},
                "range_": {"type": "string", "description": "Rango a actualizar, ej: 'Hoja1!A1:B2'"},
                "values_json": {"type": "string", "description": "Valores en formato JSON ([[fila1],[fila2],...])"},
                "account": {"type": "string", "description": "Cuenta Google opcional (email)"}
            },
            "required": ["sheet_id", "range_", "values_json"]
        },
        handler=lambda sheet_id, range_, values_json, account=None: gog_tools.gog_sheets_update(sheet_id, range_, values_json, account)
    ))
    toolkit.register(Tool(
        name="gog_docs_cat",
        description="Leer el contenido de un documento de Google Docs (solo texto).",
        parameters={
            "type": "object",
            "properties": {
                "doc_id": {"type": "string", "description": "ID de Google Doc"},
                "account": {"type": "string", "description": "Cuenta Google opcional (email)"}
            },
            "required": ["doc_id"]
        },
        handler=lambda doc_id, account=None: gog_tools.gog_docs_cat(doc_id, account)
    ))
    toolkit.register(Tool(
        name="gog_docs_export",
        description="Exportar un documento de Google Docs a txt/pdf/docx/otros.",
        parameters={
            "type": "object",
            "properties": {
                "doc_id": {"type": "string", "description": "ID de Google Doc"},
                "fmt": {"type": "string", "description": "Formato de exportación: txt/pdf/docx, default: txt", "default": "txt"},
                "outfile": {"type": "string", "description": "Archivo destino local (default: /tmp/doc.txt)", "default": "/tmp/doc.txt"},
                "account": {"type": "string", "description": "Cuenta Google opcional (email)"}
            },
            "required": ["doc_id"]
        },
        handler=lambda doc_id, fmt="txt", outfile="/tmp/doc.txt", account=None: gog_tools.gog_docs_export(doc_id, fmt, outfile, account)
    ))
    logger.info(f"Herramientas del sistema cargadas: {[t.name for t in toolkit.tools.values()]}")
    return toolkit
