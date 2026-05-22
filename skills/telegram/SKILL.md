---
name: telegram
description: Telegram User API via Telethon — send/receive messages, manage dialogs, download media, search, and account management.
homepage: https://github.com/LonamiWebs/Telethon
metadata:
  {
    "openclaw":
      {
        "emoji": "✈️",
        "requires": { "pip": ["telethon"] },
        "install":
          [
            {
              "id": "pip",
              "kind": "pip",
              "package": "telethon>=1.43",
              "label": "pip install telethon",
            },
          ],
      },
  }
---

# Telegram (Telethon)

Use Telethon (Telegram User API) to interact with Telegram as a user. Requires API credentials from https://my.telegram.org.

## Setup

1. Go to https://my.telegram.org/apps and create an app.
2. Set env vars in `.env`:

```
TELEGRAM_API_ID=12345
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+34612345678
```

3. On first run, Telethon will ask for the verification code sent to your Telegram.

## Session

Sessions are stored in `telegram_<phone>.session` in the project root. The client connects once and reuses the session on subsequent calls.

If the session expires, you'll need to re-authenticate (delete the `.session` file and restart).

## All Operations

### Dialogs (conversations/chats)

| Operation | Tool | Example |
|-----------|------|---------|
| List dialogs | `telegram_get_dialogs` | `telegram_get_dialogs(limit=20)` |
| Get entity by username | `telegram_get_entity` | `telegram_get_entity("@username")` |
| Get entity by phone | `telegram_get_entity` | `telegram_get_entity("+34612345678")` |

### Messages

| Operation | Tool | Example |
|-----------|------|---------|
| Send text | `telegram_send_message` | `telegram_send_message("@username", "Hola!")` |
| Send file | `telegram_send_file` | `telegram_send_file("@username", "/tmp/doc.pdf")` |
| Get messages | `telegram_get_messages` | `telegram_get_messages("@username", limit=10)` |
| Search messages | `telegram_search_messages` | `telegram_search_messages("consulta", limit=20)` |
| Read all (mark read) | `telegram_read_all` | `telegram_read_all("@username")` |

### Account / Profile

| Operation | Tool | Example |
|-----------|------|---------|
| My info | `telegram_get_me` | `telegram_get_me()` |

### Downloads

| Operation | Tool | Example |
|-----------|------|---------|
| Download media | `telegram_download_media` | `telegram_download_media("@username", message_id=42)` |
| Download messages to file | `telegram_export_chat` | `telegram_export_chat("@username", limit=50, outfile="/tmp/chat.txt")` |

## Examples / Use Cases

- "mira mis mensajes de telegram" → `telegram_get_dialogs(limit=10)` to list recent chats, then pick one
- "leeme los ultimos mensajes de @pepe" → `telegram_get_messages("@pepe", limit=5)`
- "enviale un mensaje a mama diciendo llego en 10" → `telegram_send_message("Mamá", "Llego en 10")`
- "busca en telegram mensajes sobre el proyecto" → `telegram_search_messages("proyecto", limit=20)`
- "descargame la foto del ultimo mensaje de @canal" → first get messages, then `telegram_download_media`
- "quien soy en telegram" → `telegram_get_me()`

## Notes

- The entity can be a username (`@user`), phone (`+34...`), or the name from your contacts list.
- For group chats, use the group name (as it appears in your dialogs) or `@group_username`.
- All operations use a shared global client. The client is lazy-connected (first call triggers login).
- If a 2FA password is set, set `TELEGRAM_PASSWORD` in `.env`.
- The session file auto-saves; no need to manually reconnect.
- Max message length is 4096 characters. Longer messages are auto-split.
