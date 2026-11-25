# N-dine-lang-app

**Author:** Kelly R. Morgan, Assistant Professor of Information Technology  
**Affiliation:** Navajo Technical University (Crownpoint, NM & Chinle, AZ)  
**Related Spec & Studio:** [`N-dine-lang`](https://github.com/krmorgan-git/N-dine-lang) · `N-dine-lang-studio`  

---

## Overview

**`N-dine-lang-app`** is a clean, offline Flask translator powered by your fine-tuned **`gemma3-1b-ndine-Q4_K_M.gguf`** model and curated **`db/dine_lex_modern.db`** lexicon—with **no `ex_sents.csv` required at runtime**.

### Features
- **Two-Step Bridge (`English → N-dine-lang → Diné ASCII`):** Converts English into canonical `T S V O L` slots, then translates to plain-ASCII Diné (with optional `Dictionary Roots` hints from `dine_lex_modern.db` or standalone mode).
- **Reverse Translation (`Diné ASCII → English`):** Translates plain-ASCII Diné back into English.
- **Word / Lexicon Lookup:** Direct search across `dine_raw`, `dine_ascii`, and `english` in `db/dine_lex_modern.db`.

---

## Guide for AI Models: `N-dine-lang` (`T S V O L`)

Canonical slot order:
```text
[T/Q/C/M]-[time/mode]  S-[subject]  V-[verb]  O-[object]  L-[location]
```
- `T-` Tense/Time (`prs`, `pst`, `fut`) · `Q-` Question · `C-` Condition · `M-` Mode/Command
- `S-` Subject (`1sg`, `2sg`, `3sg`, `1pl`, `3pl`, or noun)
- `V-` Verb (`un-` for negation)
- `O-` Object · `L-` Location

---

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5080` in your browser.

### Download the Model
Download [`gemma3-1b-ndine-Q4_K_M.gguf`](https://github.com/krmorgan-git/N-dine-lang-app/releases/download/v1.0/gemma3-1b-ndine-Q4_K_M.gguf) from [Releases](https://github.com/krmorgan-git/N-dine-lang-app/releases/tag/v1.0) and place it in `models/`:
```bash
mkdir -p models
curl -L -o models/gemma3-1b-ndine-Q4_K_M.gguf https://github.com/krmorgan-git/N-dine-lang-app/releases/download/v1.0/gemma3-1b-ndine-Q4_K_M.gguf
```
