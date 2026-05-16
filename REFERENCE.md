# AgentPiro - Comandos en Lenguaje Natural

Referencia rápida de comandos que entiende AgentPiro para interactuar con Google Workspace (gog), web search y herramientas del sistema.

---

## Gmail

| Si dices... | AgentPiro hace... |
|---|---|
| "leeme" / "leeme el ultimo correo" / "leeme el último email" | Busca el email más reciente de la bandeja de entrada |
| "leeme los ultimos 3 correos" / "leeme los últimos 5 email" | Busca los últimos N correos |
| "tengo correos nuevos?" / "hay mensajes sin leer?" | Busca correos no leídos (hasta 5) |
| "busca correos de Amazon" / "busca emails de LinkedIn" | Busca por remitente |
| "busca correos con asunto factura" | Busca por asunto |
| "busca correos de la semana pasada" | Busca en un rango de fechas |
| "envia un correo a juan@gmail.com con asunto Hola y cuerpo Que tal" | Envía un email (requiere tool calling del modelo) |
| "manda un mensaje a ana@example.com" | Envía un email (requiere tool calling) |

**Nota:** Los comandos de lectura (leeme, buscar) funcionan automáticamente por inyección forzada.

---

## Calendar

| Si dices... | AgentPiro hace... |
|---|---|
| "que tengo en mi calendario" / "mis eventos de esta semana" | Muestra eventos de los próximos 7 días |
| "que reuniones tengo mañana" | Eventos del día siguiente |
| "muestrame mis eventos del sabado" | Eventos de un día específico |
| "mis citas de la proxima semana" | Eventos de la próxima semana |
| "hay algo agendado para hoy?" | Eventos del día actual |
| "agenda una reunion para el viernes" | Crear evento (requiere tool calling) |

---

## Contacts

| Si dices... | AgentPiro hace... |
|---|---|
| "listame mis contactos" / "muestrame mis contactos" | Lista hasta 20 contactos |
| "muestrame 10 contactos" | Lista la cantidad solicitada |

---

## Drive

| Si dices... | AgentPiro hace... |
|---|---|
| "busca archivos en mi drive llamados reporte" | Busca por nombre en Drive |
| "encuentra PDFs en mi drive" | Busca por tipo PDF |
| "listame mis documentos de word" | Busca documentos Word |
| "busca presentaciones en drive" | Busca presentaciones |
| "muestrame mis archivos recientes" | Archivos ordenados por fecha |

---

## Sheets

| Si dices... | AgentPiro hace... |
|---|---|
| "lee la celda A1 de la hoja ID123" | Lee un rango de la hoja |
| "muestrame los datos de Hoja1!A1:C10 del sheet XYZ" | Lee un rango específico |
| "escribe Total 100 en A1 de la hoja ABC" | Actualiza celdas (requiere tool calling) |
| "agrega una fila con datos a la hoja 123" | Agrega fila (requiere tool calling) |

---

## Docs

| Si dices... | AgentPiro hace... |
|---|---|
| "leeme el documento con ID doc123" | Lee el contenido del documento |
| "exporta mi documento ID456 a PDF" | Exporta a PDF |
| "descarga el doc 789 como txt" | Exporta a TXT |
| "exporta el documento 123 a docx" | Exporta a DOCX |

---

## Web Search

| Si dices... | AgentPiro hace... |
|---|---|
| "busca en internet el clima de hoy" | Busca información actualizada |
| "busca noticias de tecnologia" | Noticias recientes |
| "busca el precio de..." / "cuanto cuesta..." | Consulta de precios |
| "que paso con..." / "ultimas noticias de..." | Información actual |
| "donde queda..." / "donde esta..." | Ubicaciones |
| "busca informacion sobre..." | Cualquier consulta web |

---

## Sistema

| Si dices... | AgentPiro hace... |
|---|---|
| "que hora es" | Hora actual |
| "que fecha es hoy" | Fecha actual |
| "fecha y hora completa" | Fecha, hora y día de la semana |
| "listame los archivos" | Ejecuta `ls` |
| "donde estoy" | Ejecuta `pwd` |
| "quien soy" | Ejecuta `whoami` |
| "muestrame el calendario" | Ejecuta `cal` |

---

## Arquitectura de Ejecución

- **Inyección forzada (no requiere tool calling del modelo):** Gmail (leer), Web Search, Calendar, Contacts, Drive
- **Requiere tool calling del modelo:** Gmail (enviar), Sheets (escribir), Docs (exportar), y acciones que necesitan parámetros complejos
- **Modelo actual:** `gemma3:12b` (Ollama Cloud) o `gemma3:1b` (local) — no soportan tool calling de forma fiable; las acciones que lo requieren están en espera

---

*Referencia generada para skills gog + web search + sistema.*
*Última actualización: 2026-05-16*
