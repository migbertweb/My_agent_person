import os
import subprocess
import shutil
import itertools
import glob as glob_module
from pathlib import Path

_HOME = os.path.expanduser("~")
_ALLOWED_DIRS = (_HOME + "/", "/tmp/", "/opt/", "/mnt/")
_APPS = {
    "vscodium": "codium",
    "brave": "brave-browser",
    "nautilus": "nautilus",
    "steam": "steam",
    "kitty": "kitty",
    "firefox": "firefox",
    "libreoffice": "libreoffice",
    "vlc": "vlc",
    "mpv": "mpv",
    "gimp": "gimp",
    "discord": "discord",
    "spotify": "spotify",
    "signal": "signal-desktop",
    "telegram": "telegram-desktop",
    "thunderbird": "thunderbird",
}

def _safe_path(path: str) -> str:
    path = os.path.abspath(os.path.expanduser(path))
    allowed = any(
        path == d.rstrip("/") or path.startswith(d)
        for d in _ALLOWED_DIRS
    )
    if not allowed:
        return ""
    return path

def _list_apps() -> str:
    available = []
    for name, cmd in sorted(_APPS.items()):
        if shutil.which(cmd):
            available.append(f"{name} ({cmd})")
    return "\n".join(available) if available else "Ninguna app encontrada"

def search_files(pattern: str, directory: str = None, max_results: int = 20) -> str:
    if not directory:
        directory = _HOME
    safe_dir = _safe_path(directory)
    if not safe_dir:
        return f"Error: directorio no permitido. Usa {_ALLOWED_DIRS[0]}"
    try:
        matches = list(itertools.islice(Path(safe_dir).rglob(pattern), max_results))
        if not matches:
            return f"No se encontraron archivos con '{pattern}' en {safe_dir[:60]}..."
        result = []
        for p in matches:
            size = p.stat().st_size if p.is_file() else 0
            size_str = f"{size}B" if size < 1024 else f"{size//1024}KB" if size < 1024**2 else f"{size//(1024**2)}MB"
            result.append(f"{'📄' if p.is_file() else '📁'} {p} ({size_str})")
        return "\n".join(result[:max_results])
    except PermissionError:
        return f"Error: permisos insuficientes en {safe_dir[:60]}..."
    except Exception as e:
        return f"Error: {e}"

def search_content(query: str, directory: str = None, max_results: int = 20) -> str:
    """Busca texto DENTRO del contenido de archivos con rg. No interactivo."""
    safe_dir = _safe_path(directory) if directory else _HOME
    if not safe_dir:
        return "Error: directorio no permitido"
    if not query or len(query.strip()) < 2:
        return "Error: query debe tener al menos 2 caracteres"
    query = query.strip()
    try:
        _EXCLUDE_GLOBS = ["!.git", "!node_modules", "!.cache", "!.local",
                          "!.mozilla", "!.npm", "!.cargo", "!.venv", "!venv"]
        proc = subprocess.run(
            ["rg", "-l", "-i", "--max-depth", "12", "--no-messages",
             *(a for g in _EXCLUDE_GLOBS for a in ("-g", g)),
             "--", query, safe_dir],
            capture_output=True, text=True, timeout=15,
        )
        matches = [l for l in proc.stdout.strip().split("\n") if l][:max_results]
        if not matches:
            return f"No se encontraron archivos conteniendo '{query}' en {safe_dir[:60]}..."
        result = []
        for p in matches:
            try:
                size = os.path.getsize(p) if os.path.isfile(p) else 0
                size_str = f"{size}B" if size < 1024 else f"{size//1024}KB" if size < 1024**2 else f"{size//(1024**2)}MB"
            except OSError:
                size_str = "?"
            result.append(f"📄 {p} ({size_str})")
        return f"Archivos con '{query}':\n" + "\n".join(result[:max_results])
    except FileNotFoundError:
        return "Error: ripgrep no está instalado (sudo pacman -S ripgrep)"
    except subprocess.TimeoutExpired:
        return "Error: búsqueda agotó el tiempo (15s)"
    except Exception as e:
        return f"Error: {e}"

def open_file(path: str) -> str:
    safe = _safe_path(path)
    if not safe:
        return f"Error: ruta no permitida. Usa {_ALLOWED_DIRS[0]}"
    if not os.path.exists(safe):
        return f"Error: '{path}' no existe"
    try:
        subprocess.run(["xdg-open", safe], check=True)
        return f"Abriendo: {path}"
    except Exception as e:
        return f"Error abriendo: {e}"

def run_app(app: str) -> str:
    app_lower = app.lower().strip()
    if app_lower not in _APPS:
        avail = _list_apps()
        return f"App '{app}' no encontrada. Apps disponibles:\n{avail}"
    cmd = _APPS[app_lower]
    if not shutil.which(cmd):
        return f"Error: '{cmd}' no instalado. Apps disponibles:\n{_list_apps()}"
    try:
        subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Abriendo: {app} ({cmd})"
    except Exception as e:
        return f"Error abriendo {app}: {e}"

def copy_file(source: str, dest: str) -> str:
    src = _safe_path(source)
    dst = _safe_path(dest)
    if not src or not dst:
        return "Error: ruta no permitida"
    if not os.path.exists(src):
        return f"Error: '{source}' no existe"
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        return f"Copiado: {source} → {dest}"
    except Exception as e:
        return f"Error copiando: {e}"

def move_file(source: str, dest: str) -> str:
    src = _safe_path(source)
    dst = _safe_path(dest)
    if not src or not dst:
        return "Error: ruta no permitida"
    if not os.path.exists(src):
        return f"Error: '{source}' no existe"
    try:
        shutil.move(src, dst)
        return f"Movido: {source} → {dest}"
    except Exception as e:
        return f"Error moviendo: {e}"

def delete_file(path: str, confirm: bool = False) -> str:
    if not confirm:
        return "Error: se requiere confirm=True para borrar archivos"
    safe = _safe_path(path)
    if not safe:
        return "Error: ruta no permitida"
    if not os.path.exists(safe):
        return f"Error: '{path}' no existe"
    try:
        if os.path.isdir(safe):
            shutil.rmtree(safe)
        else:
            os.remove(safe)
        return f"Eliminado: {path}"
    except Exception as e:
        return f"Error eliminando: {e}"

def file_info(path: str) -> str:
    safe = _safe_path(path)
    if not safe:
        return "Error: ruta no permitida"
    if not os.path.exists(safe):
        return f"Error: '{path}' no existe"
    try:
        stat = os.stat(safe)
        size = stat.st_size
        size_str = f"{size}B" if size < 1024 else f"{size/1024:.1f}KB" if size < 1024**2 else f"{size/(1024**2):.1f}MB" if size < 1024**3 else f"{size/(1024**3):.1f}GB"
        kind = "Directorio" if os.path.isdir(safe) else "Archivo"
        perms = oct(stat.st_mode)[-3:]
        return f"{kind}: {path}\nTamaño: {size_str}\nPermisos: {perms}\nModificado: {os.path.getmtime(safe)}"
    except Exception as e:
        return f"Error: {e}"

def read_file(path: str, max_lines: int = 50) -> str:
    safe = _safe_path(path)
    if not safe:
        return "Error: ruta no permitida"
    if not os.path.isfile(safe):
        return f"Error: '{path}' no es un archivo de texto"
    _TEXT_EXTENSIONS = {".txt", ".md", ".py", ".js", ".ts", ".json", ".yml", ".yaml",
                        ".cfg", ".conf", ".ini", ".toml", ".csv", ".env", ".sh", ".bash",
                        ".zsh", ".html", ".css", ".xml", ".log", ".rst", ".tex", ".lua",
                        ".rb", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".java", ".kt",
                        ".swift", ".pl", ".pm", ".tcl", ".sql", ".r", ".m", ".bat", ".ps1"}
    ext = os.path.splitext(safe)[1].lower()
    if ext not in _TEXT_EXTENSIONS:
        return f"Error: extensión '{ext}' no reconocida como texto. Extensiones permitidas: {', '.join(sorted(_TEXT_EXTENSIONS))}"
    try:
        with open(safe, 'r', encoding='utf-8', errors='replace') as f:
            lines = []
            for i, line in enumerate(f, 1):
                if i > max_lines:
                    remaining = sum(1 for _ in f)
                    lines.append(f"... y {remaining + 1} líneas más")
                    break
                lines.append(line.rstrip())
        return "\n".join(lines)
    except Exception as e:
        return f"Error leyendo archivo: {e}"


def _fzf_prompt(items: list[str], preview_cmd: str = "", header: str = "") -> str:
    """Lanza fzf con items via stdin y captura la selección."""
    if not items:
        return ""
    cmd = ["fzf", "--height=80%", "--layout=reverse", "--border"]
    if preview_cmd:
        cmd += ["--preview", preview_cmd]
    if header:
        cmd += ["--header", header]
    try:
        proc = subprocess.run(
            cmd,
            input="\n".join(items),
            capture_output=True,
            text=True,
            timeout=120,
        )
        return proc.stdout.strip()
    except Exception:
        return ""


def fzf_browse(directory: str = None) -> str:
    """Exploración interactiva de archivos con fzf + fd + bat"""
    safe_dir = _safe_path(directory) if directory else _HOME
    if not safe_dir:
        return "Error: directorio no permitido"
    try:
        proc = subprocess.run(
            ["fd", "--type=f", "--type=d", ".", safe_dir],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return f"No se encontraron archivos en {safe_dir}"
        files = [l for l in proc.stdout.strip().split("\n") if l]
        preview = 'bat --style=numbers,changes --color=always {} 2>/dev/null || ls -la {}'
        selected = _fzf_prompt(files, preview, f"Explorando: {safe_dir}")
        if not selected:
            return "Selección cancelada"
        return f"Seleccionado: {selected}"
    except FileNotFoundError:
        return "Error: fd no está instalado (sudo pacman -S fd)"
    except subprocess.TimeoutExpired:
        return "Error: búsqueda agotó el tiempo"
    except Exception as e:
        return f"Error: {e}"


def fzf_content_search(query: str, directory: str = None) -> str:
    """Busca texto DENTRO de archivos con rg + fzf selección + bat preview"""
    safe_dir = _safe_path(directory) if directory else _HOME
    if not safe_dir:
        return "Error: directorio no permitido"
    if not query or len(query.strip()) < 2:
        return "Error: query debe tener al menos 2 caracteres"
    query = query.strip()
    try:
        _EXCLUDE = ["!.git", "!node_modules", "!.cache", "!.local",
                     "!.mozilla", "!.npm", "!.cargo", "!.venv", "!venv"]
        proc = subprocess.run(
            ["rg", "-l", "-i", "--max-depth", "12", "--no-messages",
             *(a for g in _EXCLUDE for a in ("-g", g)),
             "--", query, safe_dir],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode not in (0, 1) or not proc.stdout.strip():
            return f"No se encontraron archivos conteniendo '{query}' en {safe_dir}"
        files = [l for l in proc.stdout.strip().split("\n") if l]
        if not files:
            return f"No se encontraron archivos conteniendo '{query}'"
        preview = f'bat --style=numbers,changes --color=always {{}} 2>/dev/null || head -100 {{}}'
        header = f"Archivos con '{query}' — selecciona uno para abrir"
        selected = _fzf_prompt(files, preview, header)
        if not selected:
            return "Selección cancelada"
        return f"Archivo con '{query}': {selected}"
    except FileNotFoundError:
        return "Error: ripgrep no está instalado (sudo pacman -S ripgrep)"
    except subprocess.TimeoutExpired:
        return "Error: búsqueda agotó el tiempo"
    except Exception as e:
        return f"Error: {e}"


def fzf_grep_lines(query: str, directory: str = None) -> str:
    """Busca líneas exactas con rg, permite seleccionar archivo:línea con fzf"""
    safe_dir = _safe_path(directory) if directory else _HOME
    if not safe_dir:
        return "Error: directorio no permitido"
    if not query or len(query.strip()) < 2:
        return "Error: query debe tener al menos 2 caracteres"
    query = query.strip()
    try:
        _EXCLUDE = ["!.git", "!node_modules", "!.cache", "!.local",
                     "!.mozilla", "!.npm", "!.cargo", "!.venv", "!venv"]
        proc = subprocess.run(
            ["rg", "-n", "-i", "--max-depth", "12", "--no-messages",
             *(a for g in _EXCLUDE for a in ("-g", g)),
             "--", query, safe_dir],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode not in (0, 1) or not proc.stdout.strip():
            return f"No se encontraron líneas con '{query}'"
        lines = [l for l in proc.stdout.strip().split("\n") if l]
        preview = (
            f'bat --style=numbers,changes --color=always --highlight-line {{2}} '
            f'{{1}} 2>/dev/null || echo "{{}}"'
        )
        header = f"Líneas con '{query}' — formato: archivo:línea:contenido"
        selected = _fzf_prompt(lines, preview, header)
        if not selected:
            return "Selección cancelada"
        parts = selected.split(":", 2)
        if len(parts) >= 2:
            return f"Línea seleccionada: {parts[0]}:{parts[1]}\n{parts[2] if len(parts) > 2 else ''}"
        return f"Seleccionado: {selected}"
    except FileNotFoundError:
        return "Error: ripgrep no está instalado"
    except subprocess.TimeoutExpired:
        return "Error: búsqueda agotó el tiempo"
    except Exception as e:
        return f"Error: {e}"


def extract_text(path: str) -> str:
    """Extrae texto de archivos TXT, PDF, DOCX y código fuente"""
    safe = _safe_path(path)
    if not safe:
        return "Error: ruta no permitida"
    if not os.path.isfile(safe):
        return f"Error: '{path}' no es un archivo"
    ext = os.path.splitext(safe)[1].lower()
    _TEXT_EXTS = {".txt", ".md", ".py", ".js", ".ts", ".json", ".yml", ".yaml",
                  ".cfg", ".conf", ".ini", ".toml", ".csv", ".env", ".sh", ".bash",
                  ".zsh", ".html", ".css", ".xml", ".log", ".rst", ".tex", ".lua",
                  ".rb", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".java", ".kt",
                  ".swift", ".pl", ".pm", ".tcl", ".sql", ".r", ".m", ".bat", ".ps1",
                  ".yaml", ".svelte", ".vue", ".tsx", ".jsx"}

    try:
        if ext in _TEXT_EXTS:
            with open(safe, "r", encoding="utf-8", errors="replace") as f:
                return f.read(50000)
        elif ext == ".pdf":
            proc = subprocess.run(
                ["pdftotext", "-layout", safe, "-"],
                capture_output=True, text=True, timeout=30,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()[:50000]
            return f"Error extrayendo PDF: {proc.stderr.strip() or 'sin contenido'}"
        elif ext == ".docx":
            try:
                from docx import Document
                doc = Document(safe)
                text = "\n".join(p.text for p in doc.paragraphs)
                return text[:50000] if text.strip() else "Documento vacío o sin texto"
            except ImportError:
                return "Error: python-docx no está instalado"
            except Exception as e:
                return f"Error leyendo DOCX: {e}"
        else:
            return f"Extensión '{ext}' no soportada para extracción de texto"
    except subprocess.TimeoutExpired:
        return "Error: extracción agotó el tiempo"
    except Exception as e:
        return f"Error extrayendo texto: {e}"
