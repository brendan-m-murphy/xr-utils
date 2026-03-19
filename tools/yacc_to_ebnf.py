"""Convert extracted yacc JSON to a simplified EBNF scaffold.

This pass is deliberately conservative:
- Multiple yacc alternatives become `|` alternatives.
- Immediate left recursion like `A -> A x | y` is rewritten to `A = y (x)*`.

The output is aimed at readability and iteration, not exact grammar preservation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _rewrite_left_recursion(rule: str, productions: list[str]) -> list[str]:
    recursive_suffixes: list[str] = []
    base_alts: list[str] = []

    for prod in productions:
        symbols = prod.split()
        if symbols and symbols[0] == rule:
            tail = " ".join(symbols[1:]).strip()
            if tail:
                recursive_suffixes.append(tail)
        else:
            base_alts.append(prod)

    if not recursive_suffixes or not base_alts:
        return productions

    suffix = " | ".join(recursive_suffixes)
    return [f"({base}) ({suffix})*" for base in base_alts]


def to_ebnf(rules: dict[str, list[str]]) -> str:
    lines: list[str] = []
    for rule_name, productions in rules.items():
        rewritten = _rewrite_left_recursion(rule_name, productions)
        rhs = "\n    | ".join(rewritten) if rewritten else "/* empty */"
        lines.append(f"{rule_name} = {rhs} ;")
    return "\n\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    ebnf_text = to_ebnf(payload.get("rules", {}))
    args.output.write_text(ebnf_text, encoding="utf-8")


if __name__ == "__main__":
    main()
