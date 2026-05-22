---
name: gog
description: Google Workspace CLI for Gmail, Calendar, Drive, Docs, Sheets, Slides, Forms, Contacts, Tasks, Chat, Classroom, Groups, Keep, Meet, People, Admin, YouTube, Photos, Apps Script, Maps, Analytics, Search Console, Sites.
homepage: https://gogcli.sh
metadata:
  {
    "openclaw":
      {
        "emoji": "🎮",
        "requires": { "bins": ["gog"] },
        "install":
          [
            {
              "id": "brew",
              "kind": "brew",
              "formula": "steipete/tap/gogcli",
              "bins": ["gog"],
              "label": "Install gog (brew)",
            },
          ],
      },
  }
---

# gog

Use `gog` for all Google Workspace services. Requires OAuth setup.

Setup (once)

- `gog auth credentials /path/to/client_secret.json`
- `gog auth add you@gmail.com --services calendar,chat,classroom,contacts,docs,drive,forms,gmail,meet,photos,sheets,slides,tasks,youtube`
- `gog auth list`

## Services Overview

gog supports **24+ Google services**: Gmail, Calendar, Drive, Docs, Sheets, Slides, Forms, Contacts, Tasks, Chat, Classroom, Groups, Keep, Meet, YouTube, Photos, People, Admin (Directory API), Apps Script, Maps, Analytics, Search Console, Sites, Backup.

## Gmail

- Search threads: `gog gmail search 'newer_than:7d' --max 10`
- Search messages (per email): `gog gmail messages search "in:inbox from:someone" --max 20 --account you@example.com`
- Send (plain): `gog gmail send --to a@b.com --subject "Hi" --body "Hello"`
- Send (multi-line): `gog gmail send --to a@b.com --subject "Hi" --body-file ./message.txt`
- Send (stdin): `gog gmail send --to a@b.com --subject "Hi" --body-file -`
- Send (HTML): `gog gmail send --to a@b.com --subject "Hi" --body-html "<p>Hello</p>"`
- Reply: `gog gmail send --to a@b.com --subject "Re: Hi" --body "Reply" --reply-to-message-id <msgId>`
- Get message: `gog gmail get <messageId> --sanitize-content`
- Draft create: `gog gmail drafts create --to a@b.com --subject "Hi" --body-file ./message.txt`
- Draft send: `gog gmail drafts send <draftId>`
- Draft list: `gog gmail drafts list`
- Labels list: `gog gmail labels list`
- Labels create: `gog gmail labels create --name "MyLabel"`
- Archive: `gog gmail archive <messageId>`
- Trash: `gog gmail trash <messageId>`
- Mark read/unread: `gog gmail mark-read <messageId>`
- Forward: `gog gmail forward <messageId> --to a@b.com`
- Thread get: `gog gmail thread get <threadId>`
- Attachment download: `gog gmail attachment <messageId> <attachmentId> --out /tmp/file.pdf`

## Calendar

- List events: `gog calendar events <calendarId> --from <iso> --to <iso>`
- Search events: `gog calendar search --text "meeting" --from <iso> --to <iso>`
- Create event: `gog calendar create <calendarId> --summary "Title" --from <iso> --to <iso>`
- Create with color: `gog calendar create <calendarId> --summary "Title" --from <iso> --to <iso> --event-color 7`
- Update event: `gog calendar update <calendarId> <eventId> --summary "New Title" --event-color 4`
- Delete event: `gog calendar delete <calendarId> <eventId>`
- Get event: `gog calendar event <calendarId> <eventId>`
- List calendars: `gog calendar calendars list`
- Create calendar: `gog calendar create-calendar --summary "New Calendar"`
- Calendar colors: `gog calendar colors`
- Free/busy: `gog calendar freebusy --from <iso> --to <iso>`
- Conflicts: `gog calendar conflicts --from <iso> --to <iso>`
- Focus time: `gog calendar focus-time --from <iso> --to <iso>`
- Out of office: `gog calendar out-of-office --from <iso> --to <iso>`
- Working location: `gog calendar working-location home --from <iso> --to <iso>`

## Drive

- Search files: `gog drive search "query" --max 10`
- List folder: `gog drive ls [folderId]`
- Folder tree: `gog drive tree --parent <folderId> --depth 2`
- Folder sizes: `gog drive du --parent <folderId> --max 20`
- File metadata: `gog drive get <fileId>`
- Download: `gog drive download <fileId> --out /tmp/file.pdf`
- Upload: `gog drive upload /path/to/file.txt`
- Create folder: `gog drive mkdir --name "New Folder" --parent <folderId>`
- Copy file: `gog drive copy <fileId> --name "Copy"`
- Move file: `gog drive move <fileId> --parent <targetFolderId>`
- Rename: `gog drive rename <fileId> "New Name"`
- Delete/trash: `gog drive delete <fileId>`
- Share: `gog drive share <fileId> --email user@example.com --role reader`
- Permissions: `gog drive permissions <fileId>`
- Inventory (read-only): `gog drive inventory --parent <folderId>`
- Audit sharing: `gog drive audit sharing`
- Labels: `gog drive labels list`

## Docs

- Read as text: `gog docs cat <docId>`
- Export: `gog docs export <docId> --format txt --out /tmp/doc.txt`
- Create: `gog docs create --title "New Doc"`
- Info: `gog docs info <docId>`
- Edit (find/replace): `gog docs edit <docId> --match "old" --replacement "new"`
- Regex replace (sed): `gog docs sed <docId> "s/old/new/g"`
- Insert text: `gog docs insert <docId> --text "Hello" --index 0`
- Clear content: `gog docs clear <docId>`
- Format text: `gog docs format <docId> --match "title" --bold --font-size 18`
- Add comment: `gog docs comments add <docId> --text "Great!"`
- List comments: `gog docs comments list <docId>`

## Sheets

- Get values: `gog sheets get <sheetId> "Tab!A1:D10" --json`
- Update values: `gog sheets update <sheetId> "Tab!A1:B2" --values-json '[["A","B"],["1","2"]]' --input USER_ENTERED`
- Append rows: `gog sheets append <sheetId> "Tab!A:C" --values-json '[["x","y","z"]]' --insert INSERT_ROWS`
- Clear range: `gog sheets clear <sheetId> "Tab!A2:Z"`
- Create spreadsheet: `gog sheets create --title "New Sheet"`
- Metadata: `gog sheets metadata <sheetId> --json`
- Add tab: `gog sheets add-tab <sheetId> --title "New Tab"`
- Rename tab: `gog sheets rename-tab <sheetId> "Sheet1" "Data"`
- Export: `gog sheets export <sheetId> --format csv --out /tmp/data.csv`
- Format cells: `gog sheets format <sheetId> "A1:C10" --bold --background "#ff0000"`
- Charts: `gog sheets chart list <sheetId>`
- Conditional formatting: `gog sheets conditional-format list <sheetId>`
- Table: `gog sheets table list <sheetId>`

## Slides

- Info: `gog slides info <presentationId>`
- Export: `gog slides export <presentationId> --format pdf --out /tmp/deck.pdf`
- Create: `gog slides create --title "New Presentation"`
- Create from markdown: `gog slides create-from-markdown "Title" --content-file slides.md`
- Create from template: `gog slides create-from-template <templateId> --replacements-json '[{"key":"{{name}}","value":"Alice"}]'`
- Add slide: `gog slides add-slide <presentationId> --image-url "https://..." --notes "Speaker notes"`
- Delete slide: `gog slides delete-slide <presentationId> <slideObjectId>`
- Copy: `gog slides copy <presentationId> --title "Copy"`
- Insert text: `gog slides insert-text <presentationId> <elementId> --text "Hello"`

## Forms

- Get form: `gog forms get <formId>`
- Create form: `gog forms create --title "Survey"`
- Add question: `gog forms questions add <formId> --title "Your name?" --type TEXT`
- Delete question: `gog forms questions delete <formId> <questionId>`
- List responses: `gog forms responses list <formId> --max 20`
- Get response: `gog forms responses get <formId> <responseId>`
- Publish/unpublish: `gog forms publish <formId>`
- Update settings: `gog forms update <formId> --title "New Title"`

## Contacts

- List: `gog contacts list --max 20`
- Search: `gog contacts search "John" --max 10`
- Get: `gog contacts get <contactId>`
- Create: `gog contacts create --name "John Doe" --email john@example.com`
- Update: `gog contacts update <contactId> --name "John Smith"`
- Delete: `gog contacts delete <contactId>`
- Export vCard: `gog contacts export --out /tmp/contacts.vcf`
- Dedupe preview: `gog contacts dedupe`
- Directory search: `gog contacts directory search "Jane"`

## Tasks

- List task lists: `gog tasks lists`
- List tasks: `gog tasks list <tasklistId> --max 20`
- Add task: `gog tasks add <tasklistId> --title "Buy milk" --notes "At the store"`
- Update task: `gog tasks update <tasklistId> <taskId> --title "New title" --status completed`
- Delete task: `gog tasks delete <tasklistId> <taskId>`

## YouTube

- Search videos: `gog youtube videos search "python tutorial" --max 5`
- Channel info: `gog youtube channels get <channelId>`
- Playlist items: `gog youtube playlists items <playlistId>`

## Photos

- List media: `gog photos list --max 10`
- Search: `gog photos search "vacation" --max 10`
- Get item: `gog photos get <mediaItemId>`
- Download: `gog photos download <mediaItemId> --out /tmp/photo.jpg`

## Chat

- List spaces: `gog chat spaces list`
- Send message: `gog chat messages send <spaceId> --text "Hello"`
- List messages: `gog chat messages list <spaceId> --max 20`
- DM send: `gog chat dm send <userEmail> --text "Hi"`
- DM space: `gog chat dm space <userEmail>`

## Classroom

- List courses: `gog classroom courses list`
- Get course: `gog classroom courses get <courseId>`
- List announcements: `gog classroom announcements list <courseId>`
- List coursework: `gog classroom coursework list <courseId>`
- List submissions: `gog classroom submissions list <courseId> <courseworkId>`
- Get profile: `gog classroom profile get <userId>`

## People

- My profile: `gog people me`
- Get profile: `gog people get <resourceName>`
- Search directory: `gog people search "query"`

## Admin (domain-wide delegation)

- List users: `gog admin users list`
- Get user: `gog admin users get <userEmail>`
- Create user: `gog admin users create <email> --first-name A --last-name B`
- Suspend user: `gog admin users suspend <userEmail>`
- List orgunits: `gog admin orgunits list --type all`
- List groups: `gog admin groups list`
- Group members: `gog admin groups members list <groupEmail>`

## Meet

- Create meeting: `gog meet create --title "Standup"`
- Get meeting: `gog meet get <spaceName>`
- Participants: `gog meet participants <spaceName>`

## Keep (Workspace only)

- List notes: `gog keep list`
- Get note: `gog keep get <noteId>`
- Create note: `gog keep create --text "Remember this"`
- Search notes: `gog keep search "keyword"`
- Delete note: `gog keep delete <noteId>`

## Maps

- Geocode: `gog maps geocode "1600 Amphitheatre Parkway, Mountain View, CA"`
- Reverse geocode: `gog maps reverse-geocode "37.422,-122.084"`
- Directions: `gog maps directions "New York" "Boston"`
- Places search: `gog maps places search "coffee near me"`

## Analytics

- List accounts: `gog analytics accounts`
- Run report: `gog analytics report <propertyId> --metrics "screenPageViews" --date-ranges "2024-01-01,2024-01-31"`

## Search Console

- List sites: `gog searchconsole sites list`
- Run query: `gog searchconsole query <siteUrl> --dimensions query,page`

## Apps Script

- Get project: `gog appscript get <scriptId>`
- Create project: `gog appscript create --title "My Script"`
- Run function: `gog appscript run <scriptId> --function myFunction`

## Groups

- List groups: `gog groups list`
- List members: `gog groups members <groupEmail>`

## Sites

- List sites: `gog sites list`
- Get site: `gog sites get <siteId>`
- Search sites: `gog sites search "query"`

## Notes

- Set `GOG_ACCOUNT=you@gmail.com` to avoid repeating `--account`.
- Prefer `--json` plus `--no-input` for scripting.
- Docs supports export/cat/copy. In-place edits via `docs edit`/`docs sed`.
- Sheets values can be passed via `--values-json` (recommended).
- `gog gmail search` returns one row per thread; use `gog gmail messages search` for individual emails.
- Event color IDs from `gog calendar colors`:
  - 1: #a4bdfc  2: #7ae7bf  3: #dbadff  4: #ff887c
  - 5: #fbd75b  6: #ffb878  7: #46d6db  8: #e1e1e1
  - 9: #5484ed  10: #51b749  11: #dc2127
