import subprocess
import shutil
import os

_GOG_PATH = shutil.which("gog")
if not _GOG_PATH:
    _GOG_PATH = shutil.which("gog", path="/home/migbert/.local/bin:/usr/local/bin:/opt/homebrew/bin:" + os.environ.get("PATH", ""))
if not _GOG_PATH:
    for p in ["/home/migbert/.local/bin/gog", "/usr/local/bin/gog", "/opt/homebrew/bin/gog"]:
        if os.path.exists(p):
            _GOG_PATH = p
            break

def _gog(*args):
    if not _GOG_PATH:
        return "Error: gog no encontrado. Instálalo con: brew install steipete/tap/gogcli"
    try:
        full_args = [_GOG_PATH] + list(args)
        result = subprocess.run(full_args, capture_output=True, text=True)
        return result.stdout or result.stderr
    except Exception as e:
        return f"Error ejecutando gog: {e}"

def gog_gmail_search(query: str, max_results: int = 10, account: str = None):
    args = ["gmail", "search", query, "--max", str(max_results)]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_gmail_send(to: str, subject: str, body: str, account: str = None):
    args = ["gmail", "send", "--to", to, "--subject", subject, "--body", body]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_calendar_events(calendar_id: str, date_from: str, date_to: str, account: str = None):
    args = ["calendar", "events", calendar_id, "--from", date_from, "--to", date_to]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_contacts_list(max_results: int = 20, account: str = None):
    args = ["contacts", "list", "--max", str(max_results)]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_drive_search(query: str, max_results: int = 10, account: str = None):
    args = ["drive", "search", query, "--max", str(max_results)]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_sheets_get(sheet_id: str, range_: str, account: str = None, as_json: bool = True):
    args = ["sheets", "get", sheet_id, range_]
    if as_json:
        args += ["--json"]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_sheets_update(sheet_id: str, range_: str, values_json: str, account: str = None):
    args = ["sheets", "update", sheet_id, range_, "--values-json", values_json, "--input", "USER_ENTERED"]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_docs_cat(doc_id: str, account: str = None):
    args = ["docs", "cat", doc_id]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_docs_export(doc_id: str, fmt: str = "txt", outfile: str = "/tmp/doc.txt", account: str = None):
    args = ["docs", "export", doc_id, "--format", fmt, "--out", outfile]
    if account:
        args += ["--account", account]
    return _gog(*args)
