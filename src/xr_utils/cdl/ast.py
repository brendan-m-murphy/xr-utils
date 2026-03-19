"""AST types for the supported subset of CDL."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Variable:
    name: str
    dtype: str
    dims: list[str] = field(default_factory=list)
    attrs: dict[str, Any] = field(default_factory=dict)
    data: list[Any] | None = None


@dataclass
class Dataset:
    name: str
    dims: dict[str, int | None] = field(default_factory=dict)
    variables: dict[str, Variable] = field(default_factory=dict)
    attrs: dict[str, Any] = field(default_factory=dict)
