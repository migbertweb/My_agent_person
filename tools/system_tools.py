import subprocess
import re
from datetime import datetime
from tools.toolkit import Tool, Toolkit
from tools.web_search import create_web_search_tool
from tools import telegram_tools
from utils.config import ALLOWED_COMMANDS
from utils.logger import logger


_NATURAL_LANG_PATTERNS = re.compile(
    r"^(dame|dime|busca|encuentra|escribe|genera|crea|haz|di|quiero|necesito|"
    r"comando|mensaje|texto|frase|oración|parrafo|párrafo|responde|"
    r"capitals|ciudad|país|capital|europa|mundo|"
    r"hola|gracias|por favor|ayuda|"
    r"completo|ejecutar|ejemplo)\b",
    re.IGNORECASE
)

_KNOWLEDGE_KEYWORDS = re.compile(
    r"\b(qué|que|cómo|como|cuál|cual|cuando|cuándo|dónde|donde|quién|quien|"
    r"explica|significa|definición|diferencia|cuanto|cuánto|"
    r"capitales|población|historia|fecha|año|mes|día)\b",
    re.IGNORECASE
)


def _is_natural_language(text: str) -> bool:
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
    return datetime.now().strftime("%H:%M:%S")


def get_current_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_datetime_full() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")


def execute_safe_command(command) -> str:
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


def _r(name, desc, params, handler):
    return Tool(name=name, description=desc, parameters=params, handler=handler)


def create_system_tools() -> Toolkit:
    toolkit = Toolkit()
    from tools import gog_tools, filesystem_tools

    # ── Sistema ──
    toolkit.register(_r("get_current_time", "Obtiene la hora actual del sistema",
        {"type": "object", "properties": {}, "required": []}, lambda: get_current_time()))
    toolkit.register(_r("get_current_date", "Obtiene la fecha actual del sistema",
        {"type": "object", "properties": {}, "required": []}, lambda: get_current_date()))
    toolkit.register(_r("get_datetime_full", "Obtiene la fecha y hora completa actual",
        {"type": "object", "properties": {}, "required": []}, lambda: get_datetime_full()))
    toolkit.register(create_web_search_tool())
    toolkit.register(_r("execute_command",
        "Ejecuta comandos del sistema permitidos del listado: date, time, cal, echo, ls, pwd, whoami, uname, cat",
        {"type": "object", "properties": {"command": {"type": "string", "description": "Comando completo a ejecutar (ej: 'date', 'ls -la')"}}, "required": ["command"]},
        lambda command: execute_safe_command(command)))

    # ── Filesystem ──
    toolkit.register(_r("search_files",
        "Busca archivos por NOMBRE en el sistema local. Herramienta PRINCIPAL de búsqueda. Usa patrones glob: *.pdf, *reporte*, *curriculo*",
        {"type": "object", "properties": {
            "pattern": {"type": "string", "description": "Patrón de búsqueda (ej: '*.pdf', '*reporte*', 'foto*.jpg')"},
            "directory": {"type": "string", "description": "Directorio base (default: home)"},
            "max_results": {"type": "integer", "description": "Máximo de resultados (default 20)", "default": 20}},
         "required": ["pattern"]},
        lambda pattern, directory=None, max_results=20: filesystem_tools.search_files(pattern, directory, max_results)))
    toolkit.register(_r("search_content",
        "Busca texto DENTRO del contenido de archivos usando ripgrep. USO PRINCIPAL para encontrar archivos por su contenido.",
        {"type": "object", "properties": {
            "query": {"type": "string", "description": "Texto a buscar dentro del contenido de archivos"},
            "directory": {"type": "string", "description": "Directorio base (default: home)"},
            "max_results": {"type": "integer", "description": "Máximo de resultados (default 20)", "default": 20}},
         "required": ["query"]},
        lambda query, directory=None, max_results=20: filesystem_tools.search_content(query, directory, max_results)))
    toolkit.register(_r("open_file",
        "Abre un archivo o carpeta con la aplicación predeterminada del sistema",
        {"type": "object", "properties": {"path": {"type": "string", "description": "Ruta del archivo o carpeta"}}, "required": ["path"]},
        lambda path: filesystem_tools.open_file(path)))
    toolkit.register(_r("run_app",
        "Ejecuta una aplicación instalada. Apps: vscodium, brave, nautilus, steam, kitty, firefox, libreoffice, vlc, mpv, gimp, discord, spotify, signal, telegram, thunderbird",
        {"type": "object", "properties": {"app": {"type": "string", "description": "Nombre de la app (vscodium, brave, nautilus, steam, kitty, ...)"}}, "required": ["app"]},
        lambda app: filesystem_tools.run_app(app)))
    toolkit.register(_r("copy_file",
        "Copia un archivo o carpeta de origen a destino",
        {"type": "object", "properties": {
            "source": {"type": "string", "description": "Ruta de origen"},
            "dest": {"type": "string", "description": "Ruta de destino"}},
         "required": ["source", "dest"]},
        lambda source, dest: filesystem_tools.copy_file(source, dest)))
    toolkit.register(_r("move_file",
        "Mueve un archivo o carpeta de origen a destino",
        {"type": "object", "properties": {
            "source": {"type": "string", "description": "Ruta de origen"},
            "dest": {"type": "string", "description": "Ruta de destino"}},
         "required": ["source", "dest"]},
        lambda source, dest: filesystem_tools.move_file(source, dest)))
    toolkit.register(_r("delete_file",
        "ELIMINA un archivo o carpeta. Requiere confirm=True para ejecutarse.",
        {"type": "object", "properties": {
            "path": {"type": "string", "description": "Ruta del archivo/carpeta a eliminar"},
            "confirm": {"type": "boolean", "description": "Debe ser true para confirmar eliminación"}},
         "required": ["path", "confirm"]},
        lambda path, confirm=False: filesystem_tools.delete_file(path, confirm)))
    toolkit.register(_r("file_info",
        "Muestra información de un archivo: tipo, tamaño, permisos, fecha",
        {"type": "object", "properties": {"path": {"type": "string", "description": "Ruta del archivo"}}, "required": ["path"]},
        lambda path: filesystem_tools.file_info(path)))
    toolkit.register(_r("read_file",
        "Lee el contenido de un archivo de texto plano (txt, md, py, json, etc). Límite 50 líneas.",
        {"type": "object", "properties": {
            "path": {"type": "string", "description": "Ruta del archivo de texto"},
            "max_lines": {"type": "integer", "description": "Máximo de líneas a leer (default 50)", "default": 50}},
         "required": ["path"]},
        lambda path, max_lines=50: filesystem_tools.read_file(path, max_lines)))
    toolkit.register(_r("extract_text",
        "Extrae el texto completo de archivos: PDF (pdftotext), DOCX (python-docx), TXT y código fuente",
        {"type": "object", "properties": {
            "path": {"type": "string", "description": "Ruta al archivo (PDF, DOCX, TXT, código)"}},
         "required": ["path"]},
        lambda path: filesystem_tools.extract_text(path)))

    # ── Gog Gmail ──
    toolkit.register(_r("gog_gmail_search",
        "Buscar correos en Gmail con query avanzada (from:, subject:, is:unread, etc)",
        {"type": "object", "properties": {
            "query": {"type": "string", "description": "Query de búsqueda Gmail"},
            "max_results": {"type": "integer", "description": "Máximo de resultados (default 10)", "default": 10},
            "account": {"type": "string", "description": "Cuenta Google opcional"}},
         "required": ["query"]},
        lambda query, max_results=10, account=None: gog_tools.gog_gmail_search(query, max_results, account)))
    toolkit.register(_r("gog_gmail_send",
        "Enviar un correo desde Gmail",
        {"type": "object", "properties": {
            "to": {"type": "string", "description": "Email destinatario"},
            "subject": {"type": "string", "description": "Asunto"},
            "body": {"type": "string", "description": "Contenido del correo"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["to", "subject", "body"]},
        lambda to, subject, body, account=None: gog_tools.gog_gmail_send(to, subject, body, account)))

    # ── Gog Calendar ──
    toolkit.register(_r("gog_calendar_events",
        "Listar eventos de Google Calendar en un rango de fechas",
        {"type": "object", "properties": {
            "calendar_id": {"type": "string", "description": "ID del calendario o dejar vacío para todos"},
            "date_from": {"type": "string", "description": "Fecha inicio ISO"},
            "date_to": {"type": "string", "description": "Fecha fin ISO"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": []},
        lambda calendar_id=None, date_from=None, date_to=None, account=None: gog_tools.gog_calendar_events(calendar_id, date_from, date_to, account)))
    toolkit.register(_r("gog_calendar_create_event",
        "CREAR un nuevo evento en Google Calendar. Requiere calendar_id, summary, date_from, date_to en formato ISO",
        {"type": "object", "properties": {
            "calendar_id": {"type": "string", "description": "ID del calendario donde crear el evento (ej: migbert.yanez@gmail.com)"},
            "summary": {"type": "string", "description": "Título del evento"},
            "date_from": {"type": "string", "description": "Fecha/hora inicio ISO (ej: 2026-05-22T18:00:00)"},
            "date_to": {"type": "string", "description": "Fecha/hora fin ISO (ej: 2026-05-22T19:00:00)"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["calendar_id", "summary", "date_from", "date_to"]},
        lambda calendar_id, summary, date_from, date_to, account=None: gog_tools.gog_calendar_create_event(calendar_id, summary, date_from, date_to, account)))
    toolkit.register(_r("gog_calendar_list",
        "Listar calendarios disponibles de Google Calendar",
        {"type": "object", "properties": {"account": {"type": "string", "description": "Cuenta opcional"}}, "required": []},
        lambda account=None: gog_tools.gog_calendar_list(account)))
    toolkit.register(_r("gog_calendar_update_event",
        "Actualizar un evento de Google Calendar",
        {"type": "object", "properties": {
            "calendar_id": {"type": "string", "description": "ID del calendario"},
            "event_id": {"type": "string", "description": "ID del evento"},
            "summary": {"type": "string", "description": "Nuevo título (opcional)"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["calendar_id", "event_id"]},
        lambda calendar_id, event_id, summary=None, account=None: gog_tools.gog_calendar_update_event(calendar_id, event_id, summary, account)))
    toolkit.register(_r("gog_calendar_delete_event",
        "Eliminar un evento de Google Calendar",
        {"type": "object", "properties": {
            "calendar_id": {"type": "string", "description": "ID del calendario"},
            "event_id": {"type": "string", "description": "ID del evento"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["calendar_id", "event_id"]},
        lambda calendar_id, event_id, account=None: gog_tools.gog_calendar_delete_event(calendar_id, event_id, account)))

    # ── Gog Contacts ──
    toolkit.register(_r("gog_contacts_list",
        "Listar contactos de Google Contacts",
        {"type": "object", "properties": {
            "max_results": {"type": "integer", "description": "Máximo (def 20)", "default": 20},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": []},
        lambda max_results=20, account=None: gog_tools.gog_contacts_list(max_results, account)))
    toolkit.register(_r("gog_contacts_search",
        "Buscar contactos en Google Contacts por nombre o email",
        {"type": "object", "properties": {
            "query": {"type": "string", "description": "Término de búsqueda"},
            "max_results": {"type": "integer", "description": "Máximo (def 10)", "default": 10},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["query"]},
        lambda query, max_results=10, account=None: gog_tools.gog_contacts_search(query, max_results, account)))

    # ── Gog Drive ──
    toolkit.register(_r("gog_drive_search",
        "Buscar archivos en Google Drive por query",
        {"type": "object", "properties": {
            "query": {"type": "string", "description": "Consulta (ej: name:reporte.pdf)"},
            "max_results": {"type": "integer", "description": "Máximo (def 10)", "default": 10},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["query"]},
        lambda query, max_results=10, account=None: gog_tools.gog_drive_search(query, max_results, account)))
    toolkit.register(_r("gog_drive_download",
        "Descargar un archivo de Google Drive",
        {"type": "object", "properties": {
            "file_id": {"type": "string", "description": "ID del archivo en Drive"},
            "outfile": {"type": "string", "description": "Ruta de destino", "default": "/tmp/download"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["file_id"]},
        lambda file_id, outfile="/tmp/download", account=None: gog_tools.gog_drive_download(file_id, outfile, account)))

    # ── Gog Sheets ──
    toolkit.register(_r("gog_sheets_get",
        "Leer un rango de celdas de Google Sheets",
        {"type": "object", "properties": {
            "sheet_id": {"type": "string", "description": "ID de la hoja de cálculo"},
            "range_": {"type": "string", "description": "Rango, ej: Hoja1!A1:B2"},
            "account": {"type": "string", "description": "Cuenta opcional"},
            "as_json": {"type": "boolean", "description": "JSON (def True)", "default": True}},
         "required": ["sheet_id", "range_"]},
        lambda sheet_id, range_, account=None, as_json=True: gog_tools.gog_sheets_get(sheet_id, range_, account, as_json)))
    toolkit.register(_r("gog_sheets_update",
        "Actualizar un rango de celdas en Google Sheets",
        {"type": "object", "properties": {
            "sheet_id": {"type": "string", "description": "ID de la hoja"},
            "range_": {"type": "string", "description": "Rango"},
            "values_json": {"type": "string", "description": "Valores en JSON ([[fila1],[fila2],...])"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["sheet_id", "range_", "values_json"]},
        lambda sheet_id, range_, values_json, account=None: gog_tools.gog_sheets_update(sheet_id, range_, values_json, account)))
    toolkit.register(_r("gog_sheets_append",
        "Agregar filas a una hoja de Google Sheets",
        {"type": "object", "properties": {
            "sheet_id": {"type": "string", "description": "ID de la hoja"},
            "range_": {"type": "string", "description": "Rango, ej: Hoja1!A:C"},
            "values_json": {"type": "string", "description": "Valores en JSON ([[fila1],[fila2],...])"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["sheet_id", "range_", "values_json"]},
        lambda sheet_id, range_, values_json, account=None: gog_tools.gog_sheets_append(sheet_id, range_, values_json, account)))
    toolkit.register(_r("gog_sheets_create",
        "Crear una nueva hoja de cálculo en Google Sheets",
        {"type": "object", "properties": {
            "title": {"type": "string", "description": "Título de la hoja"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["title"]},
        lambda title, account=None: gog_tools.gog_sheets_create(title, account)))
    toolkit.register(_r("gog_sheets_clear",
        "Limpiar un rango de celdas en Google Sheets",
        {"type": "object", "properties": {
            "sheet_id": {"type": "string", "description": "ID de la hoja"},
            "range_": {"type": "string", "description": "Rango a limpiar, ej: Hoja1!A1:Z"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["sheet_id", "range_"]},
        lambda sheet_id, range_, account=None: gog_tools.gog_sheets_clear(sheet_id, range_, account)))

    # ── Gog Docs ──
    toolkit.register(_r("gog_docs_cat",
        "Leer el contenido de un Google Docs",
        {"type": "object", "properties": {
            "doc_id": {"type": "string", "description": "ID de Google Doc"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["doc_id"]},
        lambda doc_id, account=None: gog_tools.gog_docs_cat(doc_id, account)))
    toolkit.register(_r("gog_docs_export",
        "Exportar un Google Docs a txt/pdf/docx/etc",
        {"type": "object", "properties": {
            "doc_id": {"type": "string", "description": "ID de Google Doc"},
            "fmt": {"type": "string", "description": "Formato: txt/pdf/docx (def txt)", "default": "txt"},
            "outfile": {"type": "string", "description": "Archivo destino", "default": "/tmp/doc.txt"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["doc_id"]},
        lambda doc_id, fmt="txt", outfile="/tmp/doc.txt", account=None: gog_tools.gog_docs_export(doc_id, fmt, outfile, account)))

    toolkit.register(_r("gog_docs_create",
        "Crear un nuevo Google Docs",
        {"type": "object", "properties": {
            "title": {"type": "string", "description": "Título del documento"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["title"]},
        lambda title, account=None: gog_tools.gog_docs_create(title, account)))

    # ── Gog Tasks ──
    toolkit.register(_r("gog_tasks_lists",
        "Listar las listas de tareas de Google Tasks",
        {"type": "object", "properties": {"account": {"type": "string", "description": "Cuenta opcional"}}, "required": []},
        lambda account=None: gog_tools.gog_tasks_lists(account)))
    toolkit.register(_r("gog_tasks_list",
        "Listar tareas de una lista específica de Google Tasks",
        {"type": "object", "properties": {
            "tasklist_id": {"type": "string", "description": "ID de la lista de tareas"},
            "max_results": {"type": "integer", "description": "Máximo (def 20)", "default": 20},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["tasklist_id"]},
        lambda tasklist_id, max_results=20, account=None: gog_tools.gog_tasks_list(tasklist_id, max_results, account)))
    toolkit.register(_r("gog_tasks_add",
        "Agregar una nueva tarea a Google Tasks",
        {"type": "object", "properties": {
            "tasklist_id": {"type": "string", "description": "ID de la lista de tareas"},
            "title": {"type": "string", "description": "Título de la tarea"},
            "notes": {"type": "string", "description": "Notas (opcional)", "default": ""},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["tasklist_id", "title"]},
        lambda tasklist_id, title, notes="", account=None: gog_tools.gog_tasks_add(tasklist_id, title, notes, account)))
    toolkit.register(_r("gog_tasks_update",
        "Actualizar o completar una tarea de Google Tasks",
        {"type": "object", "properties": {
            "tasklist_id": {"type": "string", "description": "ID de la lista de tareas"},
            "task_id": {"type": "string", "description": "ID de la tarea"},
            "title": {"type": "string", "description": "Nuevo título (opcional)"},
            "status": {"type": "string", "description": "Estado: needsAction o completed"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["tasklist_id", "task_id"]},
        lambda tasklist_id, task_id, title=None, status=None, account=None: gog_tools.gog_tasks_update(tasklist_id, task_id, title, status, account=account)))

    toolkit.register(_r("gog_contacts_get",
        "Obtener detalle de un contacto de Google Contacts",
        {"type": "object", "properties": {
            "contact_id": {"type": "string", "description": "ID del contacto (resourceName)"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["contact_id"]},
        lambda contact_id, account=None: gog_tools.gog_contacts_get(contact_id, account)))

    # ── Gog YouTube ──
    toolkit.register(_r("gog_youtube_search",
        "Buscar videos en YouTube",
        {"type": "object", "properties": {
            "query": {"type": "string", "description": "Término de búsqueda"},
            "max_results": {"type": "integer", "description": "Máximo (def 5)", "default": 5},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["query"]},
        lambda query, max_results=5, account=None: gog_tools.gog_youtube_search(query, max_results, account)))

    # ── Gog Photos ──
    toolkit.register(_r("gog_photos_list",
        "Listar fotos recientes de Google Photos",
        {"type": "object", "properties": {
            "max_results": {"type": "integer", "description": "Máximo (def 10)", "default": 10},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": []},
        lambda max_results=10, account=None: gog_tools.gog_photos_list(max_results, account)))

    # ── Gog Forms ──
    toolkit.register(_r("gog_forms_get",
        "Obtener información de un formulario de Google Forms",
        {"type": "object", "properties": {
            "form_id": {"type": "string", "description": "ID del formulario"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["form_id"]},
        lambda form_id, account=None: gog_tools.gog_forms_get(form_id, account)))
    toolkit.register(_r("gog_forms_responses",
        "Obtener respuestas de un formulario de Google Forms",
        {"type": "object", "properties": {
            "form_id": {"type": "string", "description": "ID del formulario"},
            "max_results": {"type": "integer", "description": "Máximo (def 20)", "default": 20},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["form_id"]},
        lambda form_id, max_results=20, account=None: gog_tools.gog_forms_responses(form_id, max_results, account)))

    # ── Gog Slides ──
    toolkit.register(_r("gog_slides_info",
        "Obtener información de una presentación de Google Slides",
        {"type": "object", "properties": {
            "presentation_id": {"type": "string", "description": "ID de la presentación"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["presentation_id"]},
        lambda presentation_id, account=None: gog_tools.gog_slides_info(presentation_id, account)))
    toolkit.register(_r("gog_slides_export",
        "Exportar una presentación de Google Slides a PDF/PPTX",
        {"type": "object", "properties": {
            "presentation_id": {"type": "string", "description": "ID de la presentación"},
            "fmt": {"type": "string", "description": "Formato: pdf o pptx (def pdf)", "default": "pdf"},
            "outfile": {"type": "string", "description": "Archivo destino", "default": "/tmp/slides.pdf"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["presentation_id"]},
        lambda presentation_id, fmt="pdf", outfile="/tmp/slides.pdf", account=None: gog_tools.gog_slides_export(presentation_id, fmt, outfile, account)))

    # ── Gog Raw (generic catch-all) ──
    toolkit.register(_r("gog_raw",
        "Ejecutar cualquier comando de gog directamente. ÚSALO para comandos no cubiertos por las otras herramientas gog_ específicas (admin, classroom, chat, groups, keep, people, apps script, maps, analytics, search console, sites). Ejemplos: 'calendar colors', 'drive tree --parent ID --depth 2', 'people me', 'admin users list', 'chat spaces list', 'classroom courses list', 'keep list', 'maps geocode DIRECCION', 'appscript run SCRIPT_ID --function myFunc'",
        {"type": "object", "properties": {
            "command": {"type": "string", "description": "Comando gog completo sin el prefijo 'gog', ej: 'calendar colors', 'drive tree --parent X', 'people me', 'admin users list'"},
            "account": {"type": "string", "description": "Cuenta opcional"}},
         "required": ["command"]},
        lambda command, account=None: gog_tools.gog_raw(command, account)))

    # ── Telegram tools ──
    toolkit.register(_r("telegram_get_me",
        "Obtener mi información de perfil de Telegram",
        {"type": "object", "properties": {}},
        lambda: telegram_tools.telegram_get_me()))
    toolkit.register(_r("telegram_get_dialogs",
        "Listar conversaciones/chats recientes de Telegram",
        {"type": "object", "properties": {
            "limit": {"type": "integer", "description": "Máx chats (def 20)", "default": 20}},
         "required": []},
        lambda limit=20: telegram_tools.telegram_get_dialogs(limit)))
    toolkit.register(_r("telegram_get_messages",
        "Obtener mensajes recientes de un chat de Telegram",
        {"type": "object", "properties": {
            "entity": {"type": "string", "description": "Destino: @username, +3412345 o nombre del chat"},
            "limit": {"type": "integer", "description": "Máx mensajes (def 10)", "default": 10}},
         "required": ["entity"]},
        lambda entity, limit=10: telegram_tools.telegram_get_messages(entity, limit)))
    toolkit.register(_r("telegram_send_message",
        "Enviar un mensaje de texto a un chat de Telegram",
        {"type": "object", "properties": {
            "entity": {"type": "string", "description": "Destino: @username, +3412345 o nombre"},
            "message": {"type": "string", "description": "Texto del mensaje"}},
         "required": ["entity", "message"]},
        lambda entity, message: telegram_tools.telegram_send_message(entity, message)))
    toolkit.register(_r("telegram_send_file",
        "Enviar un archivo a un chat de Telegram",
        {"type": "object", "properties": {
            "entity": {"type": "string", "description": "Destino: @username, +3412345 o nombre"},
            "file_path": {"type": "string", "description": "Ruta al archivo"},
            "caption": {"type": "string", "description": "Texto opcional", "default": ""}},
         "required": ["entity", "file_path"]},
        lambda entity, file_path, caption="": telegram_tools.telegram_send_file(entity, file_path, caption)))
    toolkit.register(_r("telegram_search_messages",
        "Buscar mensajes en un chat de Telegram por palabra clave",
        {"type": "object", "properties": {
            "entity": {"type": "string", "description": "Destino: @username, +3412345 o nombre"},
            "query": {"type": "string", "description": "Texto a buscar"},
            "limit": {"type": "integer", "description": "Máx resultados (def 20)", "default": 20}},
         "required": ["entity", "query"]},
        lambda entity, query, limit=20: telegram_tools.telegram_search_messages(entity, query, limit)))
    toolkit.register(_r("telegram_read_all",
        "Marcar todos los mensajes como leídos en un chat de Telegram",
        {"type": "object", "properties": {
            "entity": {"type": "string", "description": "Destino: @username, +3412345 o nombre"}},
         "required": ["entity"]},
        lambda entity: telegram_tools.telegram_read_all(entity)))
    toolkit.register(_r("telegram_download_media",
        "Descargar un archivo multimedia de un mensaje de Telegram",
        {"type": "object", "properties": {
            "entity": {"type": "string", "description": "Destino: @username, +3412345 o nombre"},
            "message_id": {"type": "integer", "description": "ID numérico del mensaje"},
            "out_dir": {"type": "string", "description": "Directorio destino (def /tmp)", "default": "/tmp"}},
         "required": ["entity", "message_id"]},
        lambda entity, message_id, out_dir="/tmp": telegram_tools.telegram_download_media(entity, message_id, out_dir)))
    toolkit.register(_r("telegram_export_chat",
        "Exportar mensajes de un chat de Telegram a un archivo de texto",
        {"type": "object", "properties": {
            "entity": {"type": "string", "description": "Destino: @username, +3412345 o nombre"},
            "limit": {"type": "integer", "description": "Máx mensajes (def 50)", "default": 50},
            "outfile": {"type": "string", "description": "Archivo destino (opcional)"}},
         "required": ["entity"]},
        lambda entity, limit=50, outfile="": telegram_tools.telegram_export_chat(entity, limit, outfile)))

    logger.info(f"Herramientas del sistema cargadas: {[t.name for t in toolkit.tools.values()]}")
    return toolkit
