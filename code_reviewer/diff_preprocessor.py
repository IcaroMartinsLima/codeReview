"""
diff_preprocessor.py
--------------------
Local pre-processing agent: cleans, scores and compresses a raw diff
before it reaches the LLM reviewer.

Pipeline
--------
raw diff text
  → _parse_hunks()         — split into structured Hunk objects
  → _remove_noise()        — drop trivial/irrelevant hunks
  → _score_and_prioritize() — rank hunks by risk keywords
  → _summarize_large_hunks() — collapse low-risk large hunks
  → _serialize()           — back to compact text for the LLM
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── tunables ──────────────────────────────────────────────────────────────────

# Hunks with more added lines than this AND low risk score get summarized
LARGE_HUNK_THRESHOLD = 12

# Added lines budget sent to the LLM (keeps token spend predictable)
MAX_OUTPUT_LINES = 200

# Files whose path matches these patterns are dropped entirely
NOISE_FILE_PATTERNS: list[str] = [
    r"package-lock\.json$",
    r"yarn\.lock$",
    r"poetry\.lock$",
    r"Pipfile\.lock$",
    r"\.lock$",
    r"\.min\.js$",
    r"\.min\.css$",
    r"dist/",
    r"build/",
    r"__pycache__/",
    r"\.pyc$",
    r"\.map$",
    r"\.snap$",         # Jest snapshots
    r"migrations/.*\.sql$",
    r"node_modules/",
]

# Added lines that match these patterns (after stripping the leading +) are
# considered noise inside otherwise useful hunks
NOISE_LINE_PATTERNS: list[str] = [
    r"^\s*$",                            # blank
    r"^\s*#\s*$",                        # lone comment char
    r"^\s*//\s*$",
    r"^\s*\*\s*$",
    r"^\s*(import|from)\s+\S+",         # pure import statements
    r"^\s*require\(",                    # JS require
    r"^\s*using\s+\S+;",               # C# using
    r'^\s*"[^"]+"\s*:\s*"[^"]*",?\s*$', # JSON key-value (config)
]

# Keywords that raise a hunk's risk score (each hit = +1)
RISK_KEYWORDS: list[tuple[str, int]] = [
    # auth / secrets
    ("password",  3), ("passwd",    3), ("secret",    3), ("token",     3),
    ("api_key",   3), ("apikey",    3), ("auth",      2), ("credential",3),
    ("private",   2), ("encrypt",   2), ("decrypt",   2), ("hash",      2),
    ("hmac",      2), ("jwt",       2), ("oauth",     2), ("bearer",    2),
    # dangerous calls
    ("exec(",     3), ("eval(",     3), ("shell",     3), ("subprocess",2),
    ("popen",     3), ("system(",   3), ("__import__",3),
    # SQL / data
    ("sql",       2), ("query",     2), ("execute(",  2), ("cursor",    2),
    ("drop ",     3), ("truncate",  3), ("delete ",   2), ("update ",   1),
    # network / IO
    ("socket",    2), ("urllib",    1), ("requests",  1), ("fetch(",    1),
    ("open(",     1), ("write(",    1), ("unlink",    2), ("remove(",   2),
    # permissions / admin
    ("admin",     2), ("root",      2), ("sudo",      3), ("chmod",     2),
    ("chown",     2), ("privilege", 2), ("superuser", 2),
    # error handling
    ("except:",   1), ("catch(",    1), ("raise ",    1), ("throw ",    1),
    ("panic(",    1),
    # concurrency
    ("thread",    1), ("async ",    1), ("await ",    1), ("lock(",     1),
    ("mutex",     2), ("semaphore", 2),
]

# ── data model ────────────────────────────────────────────────────────────────

@dataclass
class Hunk:
    file: str
    header: str           # @@ -a,b +c,d @@  (original)
    start_line: int       # new-file line where hunk starts
    added: list[str]      # raw added lines (with leading +)
    removed: list[str]    # raw removed lines (with leading -)
    context: list[str]    # surrounding context lines
    risk_score: int = 0
    summarized: bool = False
    summary_text: str = ""

    @property
    def added_count(self) -> int:
        return len(self.added)

    @property
    def all_added_text(self) -> str:
        return "\n".join(self.added)


# ── main class ────────────────────────────────────────────────────────────────

class DiffPreprocessor:
    """
    Transforms a raw unified diff into a compact, LLM-ready summary.

    Usage
    -----
    preprocessor = DiffPreprocessor()
    optimized_text, stats = preprocessor.process(raw_diff_text)
    """

    def __init__(
        self,
        large_hunk_threshold: int = LARGE_HUNK_THRESHOLD,
        max_output_lines: int = MAX_OUTPUT_LINES,
    ):
        self.large_hunk_threshold = large_hunk_threshold
        self.max_output_lines = max_output_lines
        self._noise_file_re = [re.compile(p, re.IGNORECASE) for p in NOISE_FILE_PATTERNS]
        self._noise_line_re = [re.compile(p) for p in NOISE_LINE_PATTERNS]

    # ── public API ────────────────────────────────────────────────────────────

    def process(self, diff_text: str) -> tuple[str, dict]:
        """
        Returns
        -------
        optimized_text : str
            Compact diff ready for the LLM.
        stats : dict
            Metrics about what was done (for logging/UI).
        """
        hunks = self._parse_hunks(diff_text)
        original_hunk_count = len(hunks)
        original_line_count = sum(h.added_count for h in hunks)

        hunks = self._remove_noise(hunks)
        after_noise = len(hunks)

        hunks = self._score_and_prioritize(hunks)
        hunks = self._summarize_large_hunks(hunks)
        hunks = self._enforce_line_budget(hunks)

        optimized_text = self._serialize(hunks)
        final_line_count = sum(
            h.added_count if not h.summarized else 1
            for h in hunks
        )

        stats = {
            "original_hunks":    original_hunk_count,
            "original_lines":    original_line_count,
            "after_noise_hunks": after_noise,
            "final_hunks":       len(hunks),
            "final_lines":       final_line_count,
            "summarized_hunks":  sum(1 for h in hunks if h.summarized),
            "dropped_hunks":     original_hunk_count - len(hunks),
            "savings_pct": (
                round((1 - final_line_count / max(original_line_count, 1)) * 100, 1)
            ),
        }
        return optimized_text, stats

    # ── stage 1: parse ────────────────────────────────────────────────────────

    def _parse_hunks(self, diff_text: str) -> list[Hunk]:
        hunks: list[Hunk] = []
        current_file = ""
        current_hunk: Hunk | None = None

        for raw_line in diff_text.splitlines():
            # New file
            if raw_line.startswith("diff --git"):
                current_file = ""
                current_hunk = None
                continue

            if raw_line.startswith("+++ "):
                path = raw_line[4:].strip()
                current_file = path[2:] if path.startswith("b/") else path
                continue

            if raw_line.startswith("---"):
                continue

            # New hunk header
            if raw_line.startswith("@@"):
                match = re.search(r"\+(\d+)(?:,(\d+))?", raw_line)
                start = int(match.group(1)) if match else 0
                current_hunk = Hunk(
                    file=current_file,
                    header=raw_line,
                    start_line=start,
                    added=[],
                    removed=[],
                    context=[],
                )
                hunks.append(current_hunk)
                continue

            if current_hunk is None:
                continue

            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                current_hunk.added.append(raw_line[1:])  # strip leading +
            elif raw_line.startswith("-") and not raw_line.startswith("---"):
                current_hunk.removed.append(raw_line[1:])
            else:
                current_hunk.context.append(raw_line)

        return [h for h in hunks if h.added or h.removed]

    # ── stage 2: remove noise ─────────────────────────────────────────────────

    def _remove_noise(self, hunks: list[Hunk]) -> list[Hunk]:
        result = []
        for hunk in hunks:
            # Drop entire file if it matches a noise pattern
            if any(rx.search(hunk.file) for rx in self._noise_file_re):
                continue

            # Filter noise lines within the hunk
            hunk.added = [
                line for line in hunk.added
                if not self._is_noise_line(line)
            ]

            # Keep hunk only if it still has meaningful content
            if hunk.added or hunk.removed:
                result.append(hunk)

        return result

    def _is_noise_line(self, line: str) -> bool:
        return any(rx.match(line) for rx in self._noise_line_re)

    # ── stage 3: score & prioritize ───────────────────────────────────────────

    def _score_and_prioritize(self, hunks: list[Hunk]) -> list[Hunk]:
        for hunk in hunks:
            score = 0
            text = (hunk.all_added_text + " ".join(hunk.removed)).lower()
            for keyword, weight in RISK_KEYWORDS:
                if keyword in text:
                    score += weight
            hunk.risk_score = score

        # High-risk first, then by added line count descending
        return sorted(hunks, key=lambda h: (-h.risk_score, -h.added_count))

    # ── stage 4: summarize large low-risk hunks ───────────────────────────────

    def _summarize_large_hunks(self, hunks: list[Hunk]) -> list[Hunk]:
        for hunk in hunks:
            if hunk.added_count <= self.large_hunk_threshold:
                continue
            if hunk.risk_score > 0:
                continue  # keep risky hunks intact

            # Detect enclosing function/class name from context or first added line
            block_name = self._detect_block_name(hunk)
            hunk.summarized = True
            hunk.summary_text = (
                f"[+{hunk.added_count} lines added"
                + (f" in {block_name}" if block_name else "")
                + f" — low risk, summarized to save tokens]"
            )

        return hunks

    def _detect_block_name(self, hunk: Hunk) -> str:
        """Try to extract function/class name from hunk context or added lines."""
        candidates = hunk.context[:4] + hunk.added[:4]
        for line in candidates:
            # Python / JS / TS / Java / C# function/class
            m = re.search(
                r"(?:def|class|function|func|fn|sub|public|private|protected"
                r"|async def|async function)\s+(\w+)",
                line,
            )
            if m:
                return m.group(1) + "()"
        return ""

    # ── stage 5: enforce line budget ──────────────────────────────────────────

    def _enforce_line_budget(self, hunks: list[Hunk]) -> list[Hunk]:
        """
        Keep as many hunks as fit within max_output_lines.
        Summarized hunks count as 1 line each.
        High-risk hunks are never dropped.
        """
        result = []
        used = 0
        # First pass: include all high-risk hunks regardless of budget
        for hunk in hunks:
            if hunk.risk_score > 0:
                used += 1 if hunk.summarized else hunk.added_count
                result.append(hunk)

        # Second pass: fill remaining budget with low-risk hunks
        for hunk in hunks:
            if hunk.risk_score > 0:
                continue  # already added
            cost = 1 if hunk.summarized else hunk.added_count
            if used + cost <= self.max_output_lines:
                result.append(hunk)
                used += cost

        # Re-sort by original priority
        return sorted(result, key=lambda h: (-h.risk_score, -h.added_count))

    # ── stage 6: serialize ────────────────────────────────────────────────────

    def _serialize(self, hunks: list[Hunk]) -> str:
        """
        Produce a compact, LLM-readable text.
        Format per hunk:

            ### file.py  (risk: 5)
            @@ -10,4 +10,8 @@
            + line1
            + line2
            - removed_line
            [summary if collapsed]
        """
        if not hunks:
            return ""

        lines: list[str] = []
        current_file = None

        for hunk in hunks:
            if hunk.file != current_file:
                current_file = hunk.file
                lines.append(f"\n### {hunk.file}  (risk score: {hunk.risk_score})")

            lines.append(hunk.header)

            if hunk.summarized:
                lines.append(hunk.summary_text)
            else:
                for line in hunk.removed:
                    lines.append(f"- {line}")
                for line in hunk.added:
                    lines.append(f"+ {line}")

        return "\n".join(lines).strip()
