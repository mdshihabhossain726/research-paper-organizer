# SDP2 — Research Paper Organizer: kaj bhag (shudhu ja complete hoyeche — Part 1)

Part 1 app ta **5 ta** bhage bhag kora hoyeche. Prottek bhag-er alada file ache, tai ekjon arekjon-er kaj bhange na.
Prottek member: **nijer part bujhbe -> test likhbe -> report section likhbe -> demo-te explain korbe.**

| Member | Part | Files | Ki kore |
|---|---|---|---|
| **M1** | Database & storage | `database.py`, `tests/test_database.py` | SQLite notes table, create/read/update/delete/search, DB file kothay thakbe |
| **M2** | UI design & layout | `theme.py`, `ui_builder.py` | Rong/style (QSS), 3-panel layout, shortcut |
| **M3** | Markdown live preview | `preview.py`, `tests/test_preview.py` | Markdown -> HTML, `[flow]`, `[math]`, figure caption, scroll sync |
| **M4 (Leader)** | App core, logic, integration & demo | `app.py` | Note save/open/delete/new, unsaved-change warning, sob part jora, demo |
| **M5** | Build, docs & testing | `requirements.txt`, `*.spec`, `*.bat`, `README.md`, `docs/` | .exe build, README, overall test plan, final report compile |

> **Smart editor** (`/` suggestion + Tab, toolbar) Part 2-er feature — ekhon-er zip-e nai.

## Part-gulo kibhabe jora (code flow)
```
app.py (M4)  ──uses──>  database.py (M1)    notes save/load/search
     │        ──uses──>  theme.py (M2)       app-er style
     │        ──mixes──> ui_builder.py (M2)  widgets/layout banay
     └────────mixes──>  preview.py (M3)     editor text -> preview
```
Run: `run_windows.bat` ba `python app.py` (Python 3.10+, `pip install -r requirements.txt`).
Test: `python -m unittest discover -s tests -t .`

## Rules
- Nijer file-ei kaj korbe. Onno member-er file-e change dorkar hole take bolo.
- Function/class-er naam bodlabe na (onno file import kore).
- Kaj shesh hole **nijer changed file gulo M4-ke pathabe**; M4 master copy-te boshiye `python app.py` diye check kore.
- Submit-er age `research_notes.db` ar personal file bad dao.

## Sobar common kaj
1. Zip extract kore app chalaw, ekta note banao/save/search/delete kore dekho.
2. Nijer part-er code porbe, protita function-er kaj nijer bhashay likhe rakho (viva-r jonno).
3. **Report section** (1-2 page): *Part-er purpose, kibhabe kaj kore (flow/diagram), main code explanation, screenshot, testing result.* Sob section M5-ke dao, M5 jore final report banabe (M4 review korbe).
4. Demo-te nijer part 1-2 minute dekhabe.

