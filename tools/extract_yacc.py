"""Extract a lightweight rule map from a yacc grammar file.

This is intentionally minimal and inspection-oriented:
- It finds the grammar section between %% markers.
- It strips inline C actions (`{ ... }`) to retain only productions.
- It emits JSON with rule names and production alternatives.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_RULE_HEAD = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:")


def _strip_c_blocks(text: str) -> str:
    """Remove balanced C code blocks used for yacc actions."""
    out: list[str] = []
    depth = 0
    for ch in text:
        if ch == "{":
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def extract_rules(yacc_text: str) -> dict:
    parts = yacc_text.split("%%")
    grammar_text = parts[1] if len(parts) >= 2 else yacc_text
    cleaned = _strip_c_blocks(grammar_text)

    rules: dict[str, list[str]] = {}
    current_rule: str | None = None

    for raw_line in cleaned.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = _RULE_HEAD.match(line)
        if match:
            current_rule = match.group(1)
            rhs = line.split(":", 1)[1].strip()
            rules.setdefault(current_rule, [])
            if rhs and rhs != ";":
                rules[current_rule].append(rhs.rstrip("; "))
            continue

        if current_rule is None:
            continue

        if line.startswith("|"):
            alt = line[1:].strip().rstrip("; ")
            if alt:
                rules[current_rule].append(alt)
            continue

        if line.endswith(";"):
            current_rule = None

    return {"rules": rules}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    data = extract_rules(args.input.read_text(encoding="utf-8"))
    args.output.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
