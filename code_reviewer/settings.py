import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parent.parent / "reviewer_settings.json"

DEFAULTS = {
    "tone":       "direto",
    "language":   "pt",
    "focus":      ["bug", "performance", "quality", "security"],
    "max_issues": 8,
}

# Maps focus keys → exact type string the model must return
# (matches what issue_card.py already renders)
FOCUS_TYPE_MAP = {
    "bug":         "bug",
    "performance": "performance",
    "quality":     "quality",
    "security":    "security",
}

FOCUS_LABELS = {
    "bug":         "🐛 Bug",
    "performance": "⚡ Performance",
    "quality":     "✨ Qualidade",
    "security":    "🔒 Segurança",
}

# Tone injected into USER prompt (stronger signal than system prompt)
TONE_INSTRUCTIONS = {
    "direto": (
        "Write every title, description and suggestion in a direct, concise style. "
        "No filler words. Get straight to the point."
    ),
    "didático": (
        "Write every title, description and suggestion in an educational style. "
        "Explain WHY each issue is a problem and HOW the suggestion fixes it."
    ),
    "rigoroso": (
        "Apply maximum scrutiny. Flag every potential problem, even minor style or "
        "naming issues. Prefer more issues over fewer."
    ),
}

LANGUAGE_INSTRUCTIONS = {
    "pt": (
        "IMPORTANT: Write ALL fields (title, description, suggestion) entirely in "
        "Brazilian Portuguese (pt-BR). Do NOT use English in any field."
    ),
    "en": (
        "IMPORTANT: Write ALL fields (title, description, suggestion) entirely in "
        "English. Do NOT use any other language."
    ),
    "es": (
        "IMPORTANT: Write ALL fields (title, description, suggestion) entirely in "
        "Spanish. Do NOT use any other language."
    ),
}


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            merged = dict(DEFAULTS)
            merged.update({k: v for k, v in data.items() if k in DEFAULTS})
            # sanitize focus keys
            merged["focus"] = [f for f in merged["focus"] if f in FOCUS_TYPE_MAP] or list(FOCUS_TYPE_MAP)
            return merged
        except Exception:
            pass
    return dict(DEFAULTS)


def save_settings(settings: dict) -> None:
    SETTINGS_FILE.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def build_system_prompt(settings: dict) -> str:
    # Minimal system prompt — role + hard JSON constraint only
    return (
        "You are a senior code reviewer. "
        "Respond ONLY with a valid JSON object. "
        "No markdown, no explanations, no text outside the JSON."
    )


def build_user_prompt(diff_summary: str, settings: dict) -> str:
    focus_keys = settings.get("focus") or list(FOCUS_TYPE_MAP)
    max_issues = max(3, int(settings.get("max_issues") or 8))
    tone       = settings.get("tone", "direto")
    language   = settings.get("language", "pt")

    valid_focus = [f for f in focus_keys if f in FOCUS_TYPE_MAP]
    if not valid_focus:
        valid_focus = list(FOCUS_TYPE_MAP)

    type_values = " | ".join(valid_focus)
    focus_str   = ", ".join(f'"{f}"' for f in valid_focus)

    tone_instruction     = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["direto"])
    language_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["pt"])

    return (
        f"{language_instruction}\n\n"
        f"{tone_instruction}\n\n"
        f"Analyze ONLY the added lines (+) below. Ignore removed lines and context lines.\n\n"
        f"Focus EXCLUSIVELY on these issue types: {focus_str}. "
        f"Do NOT return issues of any other type.\n\n"
        f"Return a JSON object with a single key \"issues\" containing an array. "
        f"Return between 3 and {max_issues} issues. "
        f"Each issue MUST have exactly these fields:\n"
        f"  - type: one of {type_values}\n"
        f"  - severity: one of high | medium | low\n"
        f"  - file: filename from the diff\n"
        f"  - line: line number (integer)\n"
        f"  - title: short summary\n"
        f"  - description: detailed explanation\n"
        f"  - suggestion: how to fix it\n"
        f"  - snippet: the relevant code snippet from the diff\n\n"
        f"Added lines to analyze:\n{diff_summary}"
    )