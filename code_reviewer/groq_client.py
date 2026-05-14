import json

from groq import Groq

from .constants import DEFAULT_MODEL, MAX_RESPONSE_TOKENS


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
                "Retorne entre 3 e 10 issues.\n\n",
                + diff_summary
            ),
        },
    ]


def review_diff_summary(api_key: str, model_name: str, diff_summary: str):
    client = Groq(api_key=api_key)
    return client.chat.completions.create(
        model=model_name.strip() or DEFAULT_MODEL,
        messages=build_review_messages(diff_summary),
        temperature=0.1,
        max_tokens=MAX_RESPONSE_TOKENS,
    )


def _extract_usage_from_response(resp):
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


def parse_review_response(resp):
    content = ""
    if hasattr(resp, "choices") and resp.choices:
        message = getattr(resp.choices[0], "message", None)
        content = getattr(message, "content", "") if message is not None else ""
    elif isinstance(resp, dict):
        choices = resp.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")

    text = content.strip()
    clean = text.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(clean)
    issues = parsed.get("issues", [])
    usage = _extract_usage_from_response(resp)

    return issues, usage
