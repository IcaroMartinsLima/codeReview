import re

from .constants import MAX_ADDED_LINES


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


def format_added_lines(added_lines):
    return "\n".join(
        f"+ {filename}:{line_number}: {content.strip()}"
        for filename, line_number, content in added_lines
        if content.strip()
    )
