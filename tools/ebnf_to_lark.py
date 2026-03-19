"""Translate a simplified EBNF text file into a Lark grammar scaffold.

This helper intentionally performs only straightforward rewrites:
- `name = ... ;` -> `name: ...`
- Keeps `|`, grouping, and repetition operators unchanged.
- Maps selected token aliases to regex/token placeholders for Lark.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_TOKEN_MAP = {
    "IDENT": "NAME",
    "INT_CONST": "INT",
}

_RULE_RE = re.compile(r"^(\w+)\s*=\s*(.*?)\s*;\s*$")


def convert_ebnf(ebnf_text: str) -> str:
    lines: list[str] = []
    for raw_line in ebnf_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = _RULE_RE.match(line)
        if not match:
            lines.append(raw_line)
            continue

        lhs, rhs = match.group(1), match.group(2)
        for src, dst in _TOKEN_MAP.items():
            rhs = re.sub(rf"\b{src}\b", dst, rhs)

        lines.append(f"{lhs}: {rhs}")

    lines.append("")
    lines.append("// Placeholder terminals used by converted rules")
    lines.append("NAME: /[A-Za-z_][A-Za-z0-9_]*/")
    lines.append("INT: /[0-9]+/")
    lines.append("%import common.WS")
    lines.append("%ignore WS")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    lark_text = convert_ebnf(args.input.read_text(encoding="utf-8"))
    args.output.write_text(lark_text, encoding="utf-8")


if __name__ == "__main__":
    main()
