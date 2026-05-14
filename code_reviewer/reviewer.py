import json
import re
from datetime import datetime
from pathlib import Path

from groq import Groq

from .config import load_api_key, save_api_key
from .constants import DEFAULT_MODEL, MAX_ADDED_LINES, MAX_RESPONSE_TOKENS

TOKEN_HISTORY_FILE = Path(__file__).resolve().parent.parent / "token_usage.json"


def extract_added_lines(diff_text: str, max_lines: int = MAX_ADDED_LINES):
    added = []
    current_file = None
    new_line_number = None

    for raw in diff_text.splitlines():
        if raw.startswith("diff --git"):
            current_file = None
            new_line_number = None
            continue

        if raw.startswith("+++ "):
            path = raw[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            current_file = path
            continue

        if raw.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,(\d+))?", raw)
            if match:
                new_line_number = int(match.group(1))
            continue

        if raw.startswith("+") and not raw.startswith("+++"):
            if current_file and new_line_number is not None:
                added.append((current_file, new_line_number, raw[1:]))
                new_line_number += 1
                if len(added) >= max_lines:
                    break
            continue

        if raw.startswith(" ") and new_line_number is not None:
            new_line_number += 1
            continue

    return added


def build_review_messages(diff_summary: str):
    return [
        {
            "role": "system",
            "content": (
                "Você é um revisor de código sênior. Responda apenas com JSON válido sem explicações extras."
            ),
        },
        {
            "role": "user",
            "content": (
                "Analise apenas as linhas de adição (+) abaixo. Ignore remoções e contexto. "
                "Retorne um objeto JSON com a chave issues, onde cada item tem: "
                "type, severity, file, line, title, description, suggestion, snippet. "
                "Use type: bug, quality, performance e severity: high, medium, low. "
                "Retorne entre 3 e 10 issues.\n\n"
                + diff_summary
            ),
        },
    ]


def format_added_lines(added_lines):
    return "\n".join(
        f"+ {filename}:{line_number}: {content.strip()}"
        for filename, line_number, content in added_lines
        if content.strip()
    )


def load_usage_history():
    if TOKEN_HISTORY_FILE.exists():
        try:
            return json.loads(TOKEN_HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            save_usage_history([])
            return []

    save_usage_history([])
    return []


def save_usage_history(history):
    TOKEN_HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def extract_usage_from_response(resp):
    usage = {}
    if hasattr(resp, "usage"):
        usage = getattr(resp, "usage") or {}
    elif isinstance(resp, dict):
        usage = resp.get("usage") or {}
    elif hasattr(resp, "get"):
        usage = resp.get("usage") or {}

    if hasattr(usage, "to_dict"):
        usage = usage.to_dict()
    elif hasattr(usage, "__dict__") and not isinstance(usage, dict):
        usage = dict(usage.__dict__)
    elif not isinstance(usage, dict):
        usage = {}

    return {
        "prompt_tokens": usage.get("prompt_tokens") or usage.get("promptTokens") or 0,
        "completion_tokens": usage.get("completion_tokens") or usage.get("completionTokens") or 0,
        "total_tokens": usage.get("total_tokens") or usage.get("totalTokens") or 0,
    }


def review_diff_files(api_key: str, model_name: str, diff_paths):
    if not api_key:
        raise ValueError("Informe a API Key do Groq.")

    all_added = []
    for path in diff_paths:
        diff_text = Path(path).read_text(encoding="utf-8", errors="replace")
        all_added.extend(extract_added_lines(diff_text))

    if not all_added:
        raise ValueError("Nenhuma adição encontrada no diff selecionado.")

    diff_summary = format_added_lines(all_added)
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=model_name.strip() or DEFAULT_MODEL,
        messages=build_review_messages(diff_summary),
        temperature=0.1,
        max_tokens=MAX_RESPONSE_TOKENS,
    )

    content = getattr(resp.choices[0].message, "content", "") if hasattr(resp, "choices") else ""
    text = content.strip()
    clean = text.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(clean)
    issues = parsed.get("issues", [])
    usage = extract_usage_from_response(resp)

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": model_name.strip() or DEFAULT_MODEL,
        "prompt_tokens": usage["prompt_tokens"],
        "completion_tokens": usage["completion_tokens"],
        "total_tokens": usage["total_tokens"],
        "issues": len(issues),
        "files": len(diff_paths),
    }

    history = load_usage_history()
    history.append(record)
    save_usage_history(history[-20:])

    return issues, record
