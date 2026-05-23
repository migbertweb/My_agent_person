# File Search

Búsqueda de archivos por nombre y contenido usando `rg` (ripgrep), `fd`, `pdftotext` y `python-docx`.

## Requisitos

| Herramienta | Propósito |
|---|---|
| `rg` (ripgrep) | Búsqueda de texto dentro de archivos |
| `fd` | Enumeración rápida de archivos |
| `pdftotext` (poppler) | Extracción de texto de PDFs |
| `python-docx` | Extracción de texto de DOCX |

## Herramientas del agente (GUI)

Todas las herramientas son NO interactivas y funcionan dentro de la GUI.

### `search_files(pattern, directory, max_results)`
Busca archivos por **nombre/patrón glob**.

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `pattern` | string | — | Patrón glob: `*.pdf`, `*curriculo*`, `*reporte*`, `*.py` |
| `directory` | string | `$HOME` | Directorio base |
| `max_results` | int | 20 | Máximo de resultados |

**Uso:** *"busca archivos pdf en Documentos"*, *"encuentra archivos llamados curriculo"*, *"busca *.py en /opt"*

### `search_content(query, directory, max_results)`
Busca texto **dentro** del contenido de archivos usando `ripgrep`.

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `query` | string | — | Texto a buscar (mín 2 caracteres) |
| `directory` | string | `$HOME` | Directorio base |
| `max_results` | int | 20 | Máximo de resultados |

**Uso:** *"busca archivos que contengan 'presupuesto'"*, *"encuentra documentos con la palabra 'informe'"*

### `extract_text(path)`
Extrae texto plano de cualquier archivo soportado.

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `path` | string | — | Ruta del archivo |

**Formatos soportados:**
- **Código/TXT:** `.py .js .ts .json .yml .yaml .md .txt .html .css .sh .bash .go .rs .c .cpp .java .rb .lua .sql ...`
- **PDF:** vía `pdftotext -layout`
- **DOCX:** vía `python-docx`

**Uso:** *"extrae texto de /ruta/doc.pdf"*, *"lee el documento reporte.docx"*

## Directorios permitidos

| Prefijo | Acceso |
|---|---|
| `/home/migbert/` | ✅ |
| `/opt/` | ✅ |
| `/mnt/` | ✅ |
| `/tmp/` | ✅ |

## Flujos típicos

1. **Buscar archivo por nombre:** `search_files(pattern="*curriculo*")`
2. **Buscar dentro de archivos:** `search_content(query="presupuesto 2026")`
3. **Leer contenido de archivo encontrado:** `extract_text(path="/ruta/archivo.pdf")`

## Notas

- Las rutas se validan contra `_safe_path()` por seguridad.
- Límite de 50k caracteres en `extract_text`.
- Exclusiones automáticas: `.git`, `node_modules`, `.cache`, `.local`, `.mozilla`, `.npm`, `.cargo`, `.venv` — se omiten para velocidad.
