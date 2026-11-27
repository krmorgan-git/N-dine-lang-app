"""N-dine-lang-app: Standalone offline Diné Bizaad translator powered by fine-tuned Gemma 3 1B."""

import re
import sqlite3
import unicodedata
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from llama_cpp import Llama

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
MODEL_FILENAME = "gemma3-1b-ndine-Q4_K_M.gguf"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / MODEL_FILENAME
MODEL_RELEASES_PAGE = "https://github.com/krmorgan-git/N-dine-lang-app/releases"
MODEL_RELEASE_URL = f"{MODEL_RELEASES_PAGE}/download/v1.0/{MODEL_FILENAME}"
DB_PATH = BASE_DIR / "db" / "dine_lex_modern.db"


def ensure_model() -> Path:
    """Ensure the local GGUF model exists, downloading from Releases if missing."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists():
        return MODEL_PATH
    import urllib.request

    print(f"Downloading {MODEL_FILENAME} from {MODEL_RELEASE_URL}...")
    try:
        urllib.request.urlretrieve(MODEL_RELEASE_URL, str(MODEL_PATH))
    except Exception as exc:
        if MODEL_PATH.exists():
            MODEL_PATH.unlink()
        raise FileNotFoundError(
            f"Could not download {MODEL_FILENAME} from {MODEL_RELEASE_URL} ({exc}).\n"
            f"Download it manually from {MODEL_RELEASES_PAGE} into {MODEL_DIR}/ and restart app.py."
        ) from exc
    if not MODEL_PATH.exists() or MODEL_PATH.stat().st_size == 0:
        raise FileNotFoundError(f"Downloaded model is missing or empty: {MODEL_PATH}")
    return MODEL_PATH


ensure_model()

IGNORED_TOKENS = {
    "1sg", "2sg", "3sg", "1pl", "2pl", "3pl",
    "prs", "pst", "fut", "habitual", "imp", "hort",
    "now", "at", "in", "on", "the", "un", "be", "to", "not",
}

_llm = None


def get_llm():
    global _llm
    if _llm is None and MODEL_PATH.exists():
        _llm = Llama(model_path=str(MODEL_PATH), n_ctx=2048, n_threads=4, verbose=False)
    return _llm


def strip_diacritics_ascii(text: str) -> str:
    if not text:
        return ""
    for k, v in {"ł": "l", "Ł": "L", "’": "", "'": "", "ʼ": "", "`": ""}.items():
        text = text.replace(k, v)
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").strip()


def normalize_gloss(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", "", (text or "").lower()).strip()


def lookup_slot_roots(ndine_text: str) -> tuple[list[str], list[str]]:
    if not DB_PATH.exists():
        return [], []

    concepts: list[str] = []
    for tok in ndine_text.rstrip(".").split():
        if "-" not in tok:
            continue
        _, body = tok.split("-", 1)
        words = [re.sub(r"[^a-zA-Z]", "", w).lower() for w in body.split("-")]
        words = [w for w in words if len(w) > 2 and w not in IGNORED_TOKENS]
        if len(words) > 1:
            phrase = " ".join(words)
            if phrase not in concepts:
                concepts.append(phrase)
        for w in words:
            if w not in concepts:
                concepts.append(w)

    prompt_pairs: list[str] = []
    ui_details: list[str] = []
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        for concept in concepts[:6]:
            rows = cur.execute(
                """
                SELECT dine_raw, dine_ascii, english
                FROM lexicon
                WHERE LOWER(english) LIKE ?
                  AND (n_dine_full = '' OR is_phrase = 0)
                ORDER BY is_phrase ASC, LENGTH(english) ASC
                LIMIT 40
                """,
                (f"%{concept}%",),
            ).fetchall()
            best = None
            for dine_raw, dine_ascii, english in rows:
                norm = normalize_gloss(english)
                segments = [normalize_gloss(s) for s in re.split(r"[;,]", english)]
                if norm == concept or concept in segments:
                    best = (dine_raw, dine_ascii, english)
                    break
                if best is None and re.search(rf"\b{re.escape(concept)}\b", norm):
                    best = (dine_raw, dine_ascii, english)
            if best:
                raw, asc, eng = best
                clean = strip_diacritics_ascii(asc)
                if clean:
                    prompt_pairs.append(f"{concept} -> {clean}")
                    ui_details.append(f"{concept}: {clean} ({raw}) — {eng}")
    return prompt_pairs, ui_details


def ask_model(prompt: str, max_tokens: int = 110) -> str:
    llm = get_llm()
    if llm is None:
        return "(GGUF model not found in models/)"
    resp = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.0,
    )
    return resp["choices"][0]["message"]["content"].strip()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/translate", methods=["POST"])
def api_translate():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    mode = data.get("mode", "en_to_dine")
    use_roots = bool(data.get("use_roots", True))

    if not text:
        return jsonify({"error": "Please enter text to translate."}), 400

    if mode == "dine_to_en":
        clean_in = strip_diacritics_ascii(text)
        prompt = (
            "Translate the Diné (ASCII) text into clear English.\n"
            "Output ONLY the English translation.\n\n"
            f"Dine ASCII: {clean_in}\nEnglish:"
        )
        return jsonify({"english": ask_model(prompt), "dine_ascii": clean_in})

    step1_prompt = (
        "Convert the short English sentence into canonical N-dine-lang T S V O L slots.\n"
        "Canonical order: [T/Q/C/M]-[time] S-[subject] V-[verb] O-[object] L-[location]\n"
        "Output ONLY the N-dine-lang slot sequence.\n\n"
        f"English: {text}\nN-dine-lang:"
    )
    n_dine = ask_model(step1_prompt, max_tokens=96).splitlines()[0].strip()

    roots, ui_details = lookup_slot_roots(n_dine) if use_roots else ([], [])
    if use_roots:
        lex_block = "\n".join(roots) if roots else "(None)"
        step2_prompt = (
            "Translate the N-dine-lang T S V O L sequence into Diné (ASCII) using the dictionary roots.\n"
            "Output ONLY the Diné (ASCII) words with no English definitions, no apostrophes, and no diacritics.\n\n"
            f"Dictionary Roots (concept -> Dine ASCII):\n{lex_block}\n\n"
            f"N-dine-lang: {n_dine}\nDine ASCII:"
        )
    else:
        step2_prompt = (
            "Translate the N-dine-lang T S V O L sequence into Diné (ASCII).\n"
            "Output ONLY the Diné (ASCII) words with no English definitions, no apostrophes, and no diacritics.\n\n"
            f"N-dine-lang: {n_dine}\nDine ASCII:"
        )
    dine_ascii = strip_diacritics_ascii(ask_model(step2_prompt).splitlines()[0].strip())
    return jsonify({
        "english": text,
        "n_dine": n_dine,
        "dine_ascii": dine_ascii,
        "roots": ui_details,
    })


@app.route("/api/lookup")
def api_lookup():
    q = request.args.get("q", "").strip()
    if not q or not DB_PATH.exists():
        return jsonify({"results": []})
    like_q = f"%{q}%"
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT dine_raw, dine_ascii, english, n_dine_full
            FROM lexicon
            WHERE LOWER(english) LIKE LOWER(?) OR LOWER(dine_ascii) LIKE LOWER(?)
            ORDER BY is_phrase ASC, LENGTH(english) ASC
            LIMIT 25
            """,
            (like_q, like_q),
        ).fetchall()
    return jsonify({"results": [dict(r) for r in rows]})


if __name__ == "__main__":
    get_llm()
    app.run(debug=True, use_reloader=False, host="127.0.0.1", port=5080)
