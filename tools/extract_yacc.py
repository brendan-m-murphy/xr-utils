"""Extract a lightweight rule map from a yacc grammar file.

This is intentionally minimal and inspection-oriented:
- It reads only the grammar section between ``%%`` markers.
- It strips semantic action blocks ``{ ... }`` while preserving quoted
  terminals such as ``'{'`` and ``'}'``.
- It emits JSON with rule names and production alternatives.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _grammar_section(yacc_text: str) -> str:
    parts = yacc_text.split("%%")
    if len(parts) >= 3:
        return parts[1]
    if len(parts) == 2:
        return parts[1]
    return yacc_text


def _strip_actions(text: str) -> str:
    """Strip yacc semantic actions while keeping quoted grammar tokens.

    We remove balanced C blocks only when they appear outside string/char
    literals. This keeps grammar tokens like `'{'` intact.
    """

    out: list[str] = []
    in_single = False
    in_double = False
    in_line_comment = False
    in_block_comment = False
    brace_depth = 0
    i = 0

    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                if brace_depth == 0:
                    out.append(ch)
            i += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if in_single:
            if brace_depth == 0:
                out.append(ch)
            if ch == "\\" and i + 1 < len(text):
                if brace_depth == 0:
                    out.append(text[i + 1])
                i += 2
                continue
            if ch == "'":
                in_single = False
            i += 1
            continue

        if in_double:
            if brace_depth == 0:
                out.append(ch)
            if ch == "\\" and i + 1 < len(text):
                if brace_depth == 0:
                    out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_double = False
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue

        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue

        if ch == "'":
            in_single = True
            if brace_depth == 0:
                out.append(ch)
            i += 1
            continue

        if ch == '"':
            in_double = True
            if brace_depth == 0:
                out.append(ch)
            i += 1
            continue

        if ch == "{":
            brace_depth += 1
            i += 1
            continue

        if ch == "}" and brace_depth > 0:
            brace_depth -= 1
            i += 1
            continue

        if brace_depth == 0:
            out.append(ch)

        i += 1

    return "".join(out)


def _split_rule_blocks(text: str) -> list[str]:
    """Split grammar text into `rule: ... ;` blocks at top-level semicolons."""

    blocks: list[str] = []
    buf: list[str] = []
    in_single = False
    in_double = False

    i = 0
    while i < len(text):
        ch = text[i]

        if in_single:
            buf.append(ch)
            if ch == "\\" and i + 1 < len(text):
                buf.append(text[i + 1])
                i += 2
                continue
            if ch == "'":
                in_single = False
            i += 1
            continue

        if in_double:
            buf.append(ch)
            if ch == "\\" and i + 1 < len(text):
                buf.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_double = False
            i += 1
            continue

        if ch == "'":
            in_single = True
            buf.append(ch)
            i += 1
            continue

        if ch == '"':
            in_double = True
            buf.append(ch)
            i += 1
            continue

        if ch == ";":
            block = "".join(buf).strip()
            if block:
                blocks.append(block)
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    trailing = "".join(buf).strip()
    if trailing:
        blocks.append(trailing)

    return blocks


def _split_alternatives(rhs_text: str) -> list[str]:
    """Split RHS into top-level alternatives on `|`."""

    parts: list[str] = []
    buf: list[str] = []
    in_single = False
    in_double = False

    i = 0
    while i < len(rhs_text):
        ch = rhs_text[i]

        if in_single:
            buf.append(ch)
            if ch == "\\" and i + 1 < len(rhs_text):
                buf.append(rhs_text[i + 1])
                i += 2
                continue
            if ch == "'":
                in_single = False
            i += 1
            continue

        if in_double:
            buf.append(ch)
            if ch == "\\" and i + 1 < len(rhs_text):
                buf.append(rhs_text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_double = False
            i += 1
            continue

        if ch == "'":
            in_single = True
            buf.append(ch)
            i += 1
            continue

        if ch == '"':
            in_double = True
            buf.append(ch)
            i += 1
            continue

        if ch == "|":
            alt = "".join(buf).strip()
            parts.append(alt)
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    parts.append("".join(buf).strip())

    normalized: list[str] = []
    for part in parts:
        normalized.append(part if part else "/*empty*/")
    return normalized


def extract_rules(yacc_text: str) -> dict:
    grammar_text = _grammar_section(yacc_text)
    cleaned = _strip_actions(grammar_text)

    rules: dict[str, list[str]] = {}
    for block in _split_rule_blocks(cleaned):
        if ":" not in block:
            continue
        lhs, rhs = block.split(":", 1)
        rule_name = lhs.strip().split()[-1]
        if not rule_name or not rule_name.replace("_", "a").isalnum():
            continue
        rules[rule_name] = _split_alternatives(rhs)

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
