"""CDL parser entry points."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files

from lark import Lark

from xr_utils.cdl.ast import Dataset
from xr_utils.cdl.transformer import CdlTransformer


@lru_cache(maxsize=1)
def _get_parser() -> Lark:
    grammar_text = files("xr_utils.cdl").joinpath("grammar.lark").read_text(encoding="utf-8")
    return Lark(grammar_text, parser="lalr", start="start")


def parse_cdl(text: str) -> Dataset:
    """Parse CDL text into the minimal AST representation."""
    tree = _get_parser().parse(text)
    return CdlTransformer().transform(tree)
