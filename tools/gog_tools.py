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

# ──────────────────────────────────────────
# Gmail
# ──────────────────────────────────────────
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

def gog_gmail_reply(to: str, subject: str, body: str, reply_to_message_id: str, account: str = None):
    args = ["gmail", "send", "--to", to, "--subject", subject, "--body", body, "--reply-to-message-id", reply_to_message_id]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_gmail_drafts_create(to: str, subject: str, body: str, account: str = None):
    args = ["gmail", "drafts", "create", "--to", to, "--subject", subject, "--body", body]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_gmail_drafts_send(draft_id: str, account: str = None):
    args = ["gmail", "drafts", "send", draft_id]
    if account:
        args += ["--account", account]
    return _gog(*args)

# ──────────────────────────────────────────
# Calendar
# ──────────────────────────────────────────
def gog_calendar_events(calendar_id: str = None, date_from: str = None, date_to: str = None, account: str = None):
    args = ["calendar", "events"]
    if calendar_id:
        args.append(calendar_id)
    else:
        args.append("--all")
    if date_from:
        args += ["--from", date_from]
    if date_to:
        args += ["--to", date_to]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_calendar_create_event(calendar_id: str, summary: str, date_from: str, date_to: str, account: str = None):
    args = ["calendar", "create", calendar_id, "--summary", summary, "--from", date_from, "--to", date_to]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_calendar_list(account: str = None):
    args = ["calendar", "calendars"]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_calendar_create_calendar(summary: str, account: str = None):
    args = ["calendar", "create-calendar", "--summary", summary]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_calendar_update_event(calendar_id: str, event_id: str, summary: str = None, account: str = None):
    args = ["calendar", "update", calendar_id, event_id]
    if summary:
        args += ["--summary", summary]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_calendar_delete_event(calendar_id: str, event_id: str, account: str = None):
    args = ["calendar", "delete", calendar_id, event_id]
    if account:
        args += ["--account", account]
    return _gog(*args)

# ──────────────────────────────────────────
# Contacts
# ──────────────────────────────────────────
def gog_contacts_list(max_results: int = 20, account: str = None):
    args = ["contacts", "list", "--max", str(max_results)]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_contacts_get(contact_id: str, account: str = None):
    args = ["contacts", "get", contact_id]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_contacts_search(query: str, max_results: int = 10, account: str = None):
    args = ["contacts", "search", query, "--max", str(max_results)]
    if account:
        args += ["--account", account]
    return _gog(*args)

# ──────────────────────────────────────────
# Drive
# ──────────────────────────────────────────
def gog_drive_search(query: str, max_results: int = 10, account: str = None):
    args = ["drive", "search", query, "--max", str(max_results)]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_drive_download(file_id: str, outfile: str = "/tmp/download", account: str = None):
    args = ["drive", "download", file_id, "--out", outfile]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_drive_ls(path: str = "", account: str = None):
    args = ["drive", "ls"]
    if path:
        args.append(path)
    if account:
        args += ["--account", account]
    return _gog(*args)

# ──────────────────────────────────────────
# Sheets
# ──────────────────────────────────────────
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

def gog_sheets_append(sheet_id: str, range_: str, values_json: str, account: str = None):
    args = ["sheets", "append", sheet_id, range_, "--values-json", values_json, "--insert", "INSERT_ROWS"]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_sheets_create(title: str, account: str = None):
    args = ["sheets", "create", "--title", title]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_sheets_clear(sheet_id: str, range_: str, account: str = None):
    args = ["sheets", "clear", sheet_id, range_]
    if account:
        args += ["--account", account]
    return _gog(*args)

# ──────────────────────────────────────────
# Docs
# ──────────────────────────────────────────
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

def gog_docs_create(title: str, account: str = None):
    args = ["docs", "create", "--title", title]
    if account:
        args += ["--account", account]
    return _gog(*args)

# ──────────────────────────────────────────
# Tasks
# ──────────────────────────────────────────
def gog_tasks_lists(account: str = None):
    args = ["tasks", "lists"]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_tasks_list(tasklist_id: str, max_results: int = 20, account: str = None):
    args = ["tasks", "list", tasklist_id, "--max", str(max_results)]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_tasks_update(tasklist_id: str, task_id: str, title: str = None, status: str = None, notes: str = None, account: str = None):
    args = ["tasks", "update", tasklist_id, task_id]
    if title:
        args += ["--title", title]
    if status:
        args += ["--status", status]
    if notes:
        args += ["--notes", notes]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_tasks_add(tasklist_id: str, title: str, notes: str = "", account: str = None):
    args = ["tasks", "add", tasklist_id, "--title", title]
    if notes:
        args += ["--notes", notes]
    if account:
        args += ["--account", account]
    return _gog(*args)

# ──────────────────────────────────────────
# Slides
# ──────────────────────────────────────────
def gog_slides_info(presentation_id: str, account: str = None):
    args = ["slides", "info", presentation_id]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_slides_export(presentation_id: str, fmt: str = "pdf", outfile: str = "/tmp/slides.pdf", account: str = None):
    args = ["slides", "export", presentation_id, "--format", fmt, "--out", outfile]
    if account:
        args += ["--account", account]
    return _gog(*args)

# ──────────────────────────────────────────
# YouTube
# ──────────────────────────────────────────
def gog_youtube_search(query: str, max_results: int = 5, account: str = None):
    args = ["youtube", "videos", "search", query, "--max", str(max_results)]
    if account:
        args += ["--account", account]
    return _gog(*args)

# ──────────────────────────────────────────
# Photos
# ──────────────────────────────────────────
def gog_photos_list(max_results: int = 10, account: str = None):
    args = ["photos", "list", "--max", str(max_results)]
    if account:
        args += ["--account", account]
    return _gog(*args)

# ──────────────────────────────────────────
# Forms
# ──────────────────────────────────────────
def gog_forms_get(form_id: str, account: str = None):
    args = ["forms", "get", form_id]
    if account:
        args += ["--account", account]
    return _gog(*args)

def gog_forms_responses(form_id: str, max_results: int = 20, account: str = None):
    args = ["forms", "responses", form_id, "--max", str(max_results)]
    if account:
        args += ["--account", account]
    return _gog(*args)

# ──────────────────────────────────────────
# Generic — any gog command via raw string
# ──────────────────────────────────────────
def gog_raw(command: str, account: str = None):
    """Execute any gog command from a raw string.
    
    Args:
        command: Full gog subcommand and flags, e.g. "calendar colors" or "drive tree --parent X --depth 2"
        account: Optional account email
    Returns:
        Command output string
    """
    import shlex
    args = shlex.split(command)
    if account:
        args += ["--account", account]
    return _gog(*args)
