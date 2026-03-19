# File Generator — CLAUDE.md

## Purpose
Web app that parses ASCII tree `.txt` files and scaffolds empty directory/file structures on disk.

## Stack
- **Backend**: Python 3.11, Flask, Werkzeug (`server.py`)
- **Frontend**: Vanilla JS (`FileStructureGenerator` class in `static/app.js`), inline CSS in `static/index.html`
- **Runtime**: Docker (primary) via `docker-compose.yml`

## Running the App
```bash
docker-compose up --build
# App available at http://localhost:5000
```

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serve `index.html` |
| GET | `/api/health` | Server status |
| POST | `/api/parse` | Upload + parse `.txt` file → returns `structure[]` with `comment` field |
| POST | `/api/generate` | Create file structure on disk |
| POST | `/api/preview` | Preview without writing |
| POST | `/api/validate` | Validate structure, return warnings (depth, duplicates, missing extensions) |
| GET | `/api/download/<filename>` | Download ZIP |
| POST | `/api/clean` | Remove old generated files |

## Parser Rules (`StructureParser` in `server.py`)
- Trailing `/` → directory
- File extension present → file
- Name in `standard_dirs` list (src, assets, css, js, components…) → directory
- **No extension, no slash → directory** (intentional default, user-confirmed)
- Inline comments are extracted into a separate `comment` field and stripped from the name — the frontend shows them when **Preserve Comments** is checked. Two formats supported:
  - `# hash style` → `server.py                 # Serveur Flask principal`
  - `(parens style)` → `css/          (Copiez les fichiers CSS ici)`
  - If both are present on the same line, `#` takes priority

## Key Classes
| Class | File | Role |
|-------|------|------|
| `StructureParser` | `server.py` | Parses ASCII tree text into `structure[]` items |
| `FileGenerator` | `server.py` | Creates directories and files from `structure[]`, generates default content |
| `FileStructureGenerator` | `static/app.js` | All frontend logic: upload, parse, generate, preview, validate, history |

## Frontend Conventions
- All CSS lives inline in `static/index.html` — `static/style.css` is intentionally empty
- History is persisted in `localStorage` under key `generationHistory` (max 20 entries), not server-side
- `window.generator` holds the single `FileStructureGenerator` instance (set in constructor)
- Toast notifications use `#toast` div and `.toast.show` CSS class (3 s auto-dismiss)
- The **Validate** button calls `window.generator.validateStructure()` (returns `string[]` of issues) and `window.generator.showToast()`

## Options Passed to Backend (`/api/generate`)
| Option | Default | Effect |
|--------|---------|--------|
| `overwrite` | `true` | Overwrite existing files |
| `generate_content` | `true` | Write default content templates (.vue, .js, .css, .html, .json) |
| `dryRun` | `false` | Preview only (use `/api/preview` instead) |
| `createZip` | `false` | Create downloadable ZIP after generation |
| `recursive` | `true` | Create parent directories automatically (already default via `exist_ok=True`) |
| `preserveComments` | `false` | Frontend toggle — shows inline comments in output text |

## Content Templates (`FileGenerator.generate_content`)
- `.vue` → Vue 2 SFC boilerplate
- `main.js` → Vue 2 entry point
- `.js` → ES module stub
- `.css` → comment placeholder
- `.html` → HTML5 boilerplate
- `.json` → minimal package.json stub
- Other extensions → empty file (single `// Fichier: name` comment)

## Constraints
- Max upload size: 16 MB
- Generated files land in `generated/generation_<timestamp>/` when target is the default path
- ZIP files are created inside the target path, not a separate location
