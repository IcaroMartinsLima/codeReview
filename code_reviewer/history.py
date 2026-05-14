import json
from pathlib import Path

TOKEN_HISTORY_FILE = Path(__file__).resolve().parent.parent / "token_usage.json"


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


def record_usage(usage_record):
    history = load_usage_history()
    history.append(usage_record)
    save_usage_history(history[-20:])
    return history
