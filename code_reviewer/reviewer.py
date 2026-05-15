from datetime import datetime
from pathlib import Path

from .constants import DEFAULT_MODEL
from .diff_preprocessor import DiffPreprocessor
from .groq_client import parse_review_response, review_diff_summary
from .history import load_usage_history, save_usage_history
from .settings import load_settings


def review_diff_files(api_key: str, model_name: str, diff_paths,
                      settings: dict | None = None):
    if not api_key:
        raise ValueError("Informe a API Key do Groq.")

    s = settings or load_settings()

    # ── Agent 1: local pre-processor ─────────────────────────────────────────
    preprocessor = DiffPreprocessor()
    combined_diff = ""
    for path in diff_paths:
        combined_diff += Path(path).read_text(encoding="utf-8", errors="replace") + "\n"

    if not combined_diff.strip():
        raise ValueError("Nenhum conteúdo encontrado nos arquivos selecionados.")

    optimized_diff, preprocess_stats = preprocessor.process(combined_diff)

    if not optimized_diff.strip():
        raise ValueError("Nenhuma adição relevante encontrada no diff após pré-processamento.")

    # ── Agent 2: LLM reviewer ────────────────────────────────────────────────
    resp = review_diff_summary(api_key, model_name, optimized_diff, settings=s)
    issues, usage = parse_review_response(resp)

    record = {
        "timestamp":         datetime.now().isoformat(timespec="seconds"),
        "model":             model_name.strip() or DEFAULT_MODEL,
        "prompt_tokens":     usage["prompt_tokens"],
        "completion_tokens": usage["completion_tokens"],
        "total_tokens":      usage["total_tokens"],
        "issues":            len(issues),
        "files":             len(diff_paths),
        "tone":              s.get("tone", "direto"),
        "language":          s.get("language", "pt"),
        "focus":             s.get("focus", []),
        "max_issues":        s.get("max_issues", 8),
        # pre-processor metrics
        "preprocess_original_lines": preprocess_stats["original_lines"],
        "preprocess_final_lines":    preprocess_stats["final_lines"],
        "preprocess_savings_pct":    preprocess_stats["savings_pct"],
        "preprocess_dropped_hunks":  preprocess_stats["dropped_hunks"],
        "preprocess_summarized":     preprocess_stats["summarized_hunks"],
    }

    history = load_usage_history()
    history.append(record)
    save_usage_history(history[-20:])

    return issues, record, preprocess_stats