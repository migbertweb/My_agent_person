import os
import subprocess
import shutil
import glob as glob_module
from pathlib import Path

_HOME = os.path.expanduser("~")
_ALLOWED_PREFIXES = (_HOME + "/", "/tmp/")
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
    if not path.startswith(_ALLOWED_PREFIXES):
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
        return f"Error: directorio no permitido. Usa {_ALLOWED_PREFIXES[0]}"
    try:
        matches = list(Path(safe_dir).rglob(pattern))[:max_results]
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

def open_file(path: str) -> str:
    safe = _safe_path(path)
    if not safe:
        return f"Error: ruta no permitida. Usa {_ALLOWED_PREFIXES[0]}"
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
