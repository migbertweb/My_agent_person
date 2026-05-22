# AgentPiro - Comandos en Lenguaje Natural

Referencia rápida de comandos para interactuar con:
- **Google Workspace** (gog) — Gmail, Calendar, Drive, Contacts, Sheets, Docs, Tasks, YouTube, Photos, Forms, Slides, Chat, Classroom, People, Admin, Keep, Meet, Groups, Sites, Apps Script, Maps, Analytics, Search Console
- **Filesystem** — búsqueda, apertura, copia, movimiento, eliminación y lectura de archivos
- **Apps** — lanzar aplicaciones instaladas
- **Web Search** y **Sistema**

---

## Filesystem (Archivos Locales)

| Si dices... | AgentPiro hace... |
|---|---|
| "busca archivos pdf en home" / "encuentra archivos con extension .py" | Busca archivos por patrón en tu home |
| "busca una carpeta llamada proyectos" | Busca carpetas por nombre |
| "abre la carpeta Descargas" | Abre la carpeta con el gestor de archivos |
| "abre el archivo informes/reporte.pdf" | Abre archivo con app predeterminada |
| "que pesa el archivo X" / "info del archivo X" | Muestra tipo, tamaño y permisos |
| "cuanto ocupa la carpeta Documentos" | Información de directorio |
| "muestrame el contenido de config.py" | Lee archivo de texto (hasta 50 líneas) |
| "lee el archivo notas.md" | Lee contenido de texto plano |
| "copia archivo.txt a Documentos/" | Copia archivo o carpeta |
| "mueve documento.docx a Trabajo/" | Mueve o renombra archivo |
| "borra archivo temporal.tmp" | Elimina archivo (requiere confirmación) |
| "renombra viejo.txt a nuevo.txt" | Renombra (equivale a mover) |

**Extensiones de texto soportadas:** .txt .md .py .js .ts .json .yml .yaml .cfg .conf .ini .toml .csv .env .sh .bash .zsh .html .css .xml .log .rst .tex .lua .rb .go .rs .c .cpp .h .hpp .java .kt .swift .pl .pm .tcl .sql .r .m .bat .ps1

---

## Apps (Aplicaciones)

| Si dices... | AgentPiro hace... |
|---|---|
| "abre vscodium" / "abre code" / "lanza vscode" | Abre VSCodium |
| "abre brave" / "abre el navegador" | Abre Brave Browser |
| "abre archivos" / "abre nautilus" | Abre gestor de archivos Nautilus |
| "abre steam" / "lanza steam" | Abre Steam |
| "abre kitty" / "abre terminal" | Abre Kitty (terminal) |
| "abre firefox" / "abre el navegador" | Abre Firefox |
| "abre libreoffice" / "abre office" / "abre writer" | Abre LibreOffice |
| "abre vlc" / "abre reproductor" | Abre VLC |
| "abre spotify" / "abre música" | Abre Spotify |
| "abre discord" / "abre discord" | Abre Discord |
| "abre telegram" | Abre Telegram Desktop |
| "abre signal" | Abre Signal |
| "abre gimp" | Abre GIMP |
| "abre thunderbird" | Abre Thunderbird |

---

## Gmail

| Si dices... | AgentPiro hace... |
|---|---|
| "leeme" / "leeme el ultimo correo" | Busca el email más reciente de la bandeja |
| "leeme los ultimos 3 correos" / "leeme los últimos 5 email" | Busca los últimos N correos |
| "tengo correos nuevos?" / "hay mensajes sin leer?" | Busca no leídos (hasta 5) |
| "busca correos de Amazon" / "busca emails de LinkedIn" | Busca por remitente |
| "busca correos con asunto factura" | Busca por asunto |
| "busca correos de la semana pasada" | Busca en rango de fechas |
| "envia un correo a juan@gmail.com con asunto Hola y cuerpo Que tal" | Envía email (requiere tool calling) |
| "responde al correo ID123 con cuerpo Gracias" | Responde un mensaje específico |

---

## Calendar

| Si dices... | AgentPiro hace... |
|---|---|
| "que tengo en mi calendario" / "mis eventos de esta semana" | Eventos próximos 7 días |
| "que reuniones tengo mañana" | Eventos del día siguiente |
| "muestrame mis eventos del sabado" | Eventos de día específico |
| "mis citas de la proxima semana" | Eventos próxima semana |
| "hay algo agendado para hoy?" | Eventos del día actual |
| "lista mis calendarios" | Lista calendarios disponibles |
| "agenda una reunion para el viernes" | Crear evento (requiere tool calling) |

---

## Contacts

| Si dices... | AgentPiro hace... |
|---|---|
| "listame mis contactos" / "muestrame mis contactos" | Lista hasta 20 contactos |
| "busca el contacto de Juan" | Busca contacto por nombre |
| "muestrame 10 contactos" | Lista cantidad solicitada |

---

## Drive

| Si dices... | AgentPiro hace... |
|---|---|
| "busca archivos en drive llamados reporte" | Busca por nombre en Drive |
| "encuentra PDFs en mi drive" | Busca por tipo |
| "listame documentos de word en drive" | Busca documentos Word |
| "busca presentaciones en drive" | Busca presentaciones |
| "muestrame archivos recientes" | Archivos ordenados por fecha |

---

## Sheets

| Si dices... | AgentPiro hace... |
|---|---|
| "lee la celda A1 de la hoja ID123" | Lee rango de la hoja |
| "muestrame Hoja1!A1:C10 del sheet XYZ" | Lee rango específico |
| "escribe Total 100 en A1 de la hoja ABC" | Actualiza celdas (requiere tool calling) |
| "agrega fila con datos a la hoja 123" | Agrega fila (requiere tool calling) |
| "limpia el rango A1:C10 de la hoja XYZ" | Limpia rango (requiere tool calling) |

---

## Docs

| Si dices... | AgentPiro hace... |
|---|---|
| "leeme el documento ID doc123" | Lee el contenido del documento |
| "exporta mi documento ID456 a PDF" | Exporta a PDF |
| "descarga el doc 789 como txt" | Exporta a TXT |
| "exporta el documento 123 a docx" | Exporta a DOCX |

---

## Tasks

| Si dices... | AgentPiro hace... |
|---|---|
| "lista mis listas de tareas" | Lista las listas de Google Tasks |
| "muestrame las tareas de mi lista default" | Muestra tareas de una lista |
| "agrega una tarea: Comprar leche" | Agrega tarea (requiere tool calling) |

---

## YouTube

| Si dices... | AgentPiro hace... |
|---|---|
| "busca videos de python en youtube" | Busca videos en YouTube |
| "encuentra tutoriales de linux en youtube" | Busca videos · |
| "busca música relajante en youtube" | Busca videos musicales |

---

## Google Photos

| Si dices... | AgentPiro hace... |
|---|---|
| "muestrame mis fotos recientes" | Lista fotos de Google Photos |
| "enseñame las últimas 5 fotos" | Lista N fotos recientes |

---

## Forms

| Si dices... | AgentPiro hace... |
|---|---|
| "obten el formulario ID form123" | Obtiene información del formulario |
| "muestrame las respuestas del form ABC" | Obtiene respuestas (requiere tool calling) |

---

## Slides

| Si dices... | AgentPiro hace... |
|---|---|
| "info de la presentacion ID pres123" | Información de la presentación |
| "exporta la presentacion ID456 a PDF" | Exporta slides a PDF (requiere tool calling) |

---

## Web Search

| Si dices... | AgentPiro hace... |
|---|---|
| "busca en internet el clima de hoy" | Búsqueda web actualizada |
| "busca noticias de tecnologia" | Noticias recientes |
| "busca el precio de..." / "cuanto cuesta..." | Consulta de precios |
| "que paso con..." / "ultimas noticias de..." | Info actual |
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

## Servicios Google Soportados por gog

gog da acceso a **24+ servicios de Google**:

core: gmail, calendar, drive, docs, sheets, slides, forms, contacts, tasks, youtube, photos, people, chat
extra: classroom, admin, groups, keep, meet, sites, appscript, maps, analytics, searchconsole, backup

Para autorizar servicios: `gog auth add tu@email.com --services calendar,chat,classroom,contacts,docs,drive,forms,gmail,meet,photos,sheets,slides,tasks,youtube`

---

## Arquitectura de Ejecución

- **Inyección forzada (no requiere tool calling del modelo):** Gmail (leer), Web Search, Calendar, Contacts, Drive, Filesystem (búsqueda), Apps (lanzar)
- **Requiere tool calling del modelo:** Gmail (enviar, responder), Sheets (escribir, limpiar), Docs (exportar), Forms, Slides, Tasks, YouTube, Photos, y acciones que necesitan parámetros complejos
- **Modelo actual:** `gemma3:12b` (Ollama Cloud) o `gemma3:1b` (local) — no soportan tool calling de forma fiable; las acciones que lo requieren están en espera

---

*Referencia generada para skills gog (24+ servicios) + filesystem + apps + web search + sistema.*
*Última actualización: 2026-05-21*
