# N-dine-lang-app

**Author:** Kelly R. Morgan, Assistant Professor of Information Technology  
**Affiliation:** Navajo Technical University (Crownpoint, NM & Chinle, AZ)  
**Related Spec:** [`N-dine-lang`](https://github.com/krmorgan-git/N-dine-lang)  

---

## Overview

**`N-dine-lang-app`** is a clean, offline Flask translator powered by your fine-tuned **`gemma3-1b-ndine-Q4_K_M.gguf`** model and curated **`db/dine_lex_modern.db`** lexicon—with **no `ex_sents.csv` required at runtime**.

### Features
- **Two-Step Bridge (`English → N-dine-lang → Diné ASCII`):** Converts English into canonical `T S V O L` slots, then translates to plain-ASCII Diné (with optional `Dictionary Roots` hints from `dine_lex_modern.db` or standalone mode).
- **Reverse Translation (`Diné ASCII → English`):** Translates plain-ASCII Diné back into English.
- **Word / Lexicon Lookup:** Direct search across `dine_raw`, `dine_ascii`, and `english` in `db/dine_lex_modern.db`.

---

## Core Architecture (`T S V O L`)

Canonical slot order:
```text
T-[time]  S-[subject]  V-[verb]  O-[object]  L-[location]
```
- `T-` Time (`prs` = present, `pst` = past, `fut` = future)
- `S-` Subject (`1sg` = I, `2sg` = you, `3sg` = he/she, `1pl` = we, `3pl` = they, or a noun)
- `V-` Verb (`un-` for negation)
- `O-` Object · `L-` Location

---

## Setup & Installation

### Option A: One-Command Install & Run (Recommended)

**Linux / macOS / WSL:**
```bash
git clone https://github.com/krmorgan-git/N-dine-lang-app.git
cd N-dine-lang-app
bash start.sh
```

**Windows (Command Prompt / PowerShell):**
```bat
git clone https://github.com/krmorgan-git/N-dine-lang-app.git
cd N-dine-lang-app
start.bat
```

The script creates `.venv`, installs dependencies, downloads the ~777 MB AI model automatically on first run, and starts the web app at **<http://127.0.0.1:5080>**.

### Option B: Manual Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
