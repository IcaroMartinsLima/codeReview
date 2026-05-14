from datetime import datetime
from pathlib import Path

from .constants import DEFAULT_MODEL
from .diff_parser import extract_added_lines, format_added_lines
from .groq_client import parse_review_response, review_diff_summary
from .history import load_usage_history, save_usage_history
from .settings import load_settings


def review_diff_files(api_key: str, model_name: str, diff_paths,
                      settings: dict | None = None):
    if not api_key:
        raise ValueError("Informe a API Key do Groq.")

    s = settings or load_settings()

    all_added = []
    for path in diff_paths:
        diff_text = Path(path).read_text(encoding="utf-8", errors="replace")
        all_added.extend(extract_added_lines(diff_text))

    if not all_added:
        raise ValueError("Nenhuma adição encontrada no diff selecionado.")

    diff_summary = format_added_lines(all_added)
    resp         = review_diff_summary(api_key, model_name, diff_summary, settings=s)
    issues, usage = parse_review_response(resp)

    record = {
        "timestamp":         datetime.now().isoformat(timespec="seconds"),
        "model":             model_name.strip() or DEFAULT_MODEL,
        "prompt_tokens":     usage["prompt_tokens"],
        "completion_tokens": usage["completion_tokens"],
        "total_tokens":      usage["total_tokens"],
        "issues":            len(issues),
        "files":             len(diff_paths),
        # record the settings used for traceability
        "tone":              s.get("tone", "direto"),
        "language":          s.get("language", "pt"),
        "focus":             s.get("focus", []),
        "max_issues":        s.get("max_issues", 8),
    }

    history = load_usage_history()
    history.append(record)
    save_usage_history(history[-20:])

    return issues, record