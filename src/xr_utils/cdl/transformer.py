"""Parse-tree to AST transformer for a minimal CDL subset."""

from __future__ import annotations

import ast as py_ast
from typing import Any

from lark import Transformer

from xr_utils.cdl.ast import Dataset, Variable


class CdlTransformer(Transformer):
    """Convert Lark trees into the internal CDL AST dataclasses."""

    def start(self, items: list[Any]) -> Dataset:
        return items[0]

    def dataset(self, items: list[Any]) -> Dataset:
        name = str(items[0])
        dims: dict[str, int | None] = {}
        variables: dict[str, Variable] = {}
        global_attrs: dict[str, Any] = {}
        data_map: dict[str, list[Any]] = {}

        for section in items[1:]:
            tag = section[0]
            if tag == "dimensions":
                dims.update(section[1])
            elif tag == "variables":
                vars_map, attrs_map, globals_map = section[1], section[2], section[3]
                variables.update(vars_map)
                global_attrs.update(globals_map)
                for var_name, attrs in attrs_map.items():
                    if var_name in variables:
                        variables[var_name].attrs.update(attrs)
            elif tag == "data":
                data_map.update(section[1])

        for var_name, values in data_map.items():
            if var_name in variables:
                variables[var_name].data = values

        return Dataset(name=name, dims=dims, variables=variables, attrs=global_attrs)

    def section(self, items: list[Any]) -> Any:
        return items[0]

    def dimensions_section(self, items: list[Any]) -> tuple[str, dict[str, int | None]]:
        dims: dict[str, int | None] = {}
        for dim_name, dim_size in items:
            dims[dim_name] = dim_size
        return ("dimensions", dims)

    def dimension_decl(self, items: list[Any]) -> tuple[str, int | None]:
        return (str(items[0]), items[1])

    def dim_int(self, items: list[Any]) -> int:
        return int(str(items[0]))

    def dim_unlimited(self, _items: list[Any]) -> None:
        return None

    def variables_section(self, items: list[Any]) -> tuple[str, dict[str, Variable], dict[str, dict[str, Any]], dict[str, Any]]:
        variables: dict[str, Variable] = {}
        var_attrs: dict[str, dict[str, Any]] = {}
        global_attrs: dict[str, Any] = {}

        for stmt in items:
            kind = stmt[0]
            if kind == "decl":
                var = stmt[1]
                variables[var.name] = var
            elif kind == "attr":
                target, key, value = stmt[1], stmt[2], stmt[3]
                if target is None:
                    global_attrs[key] = value
                else:
                    var_attrs.setdefault(target, {})[key] = value

        return ("variables", variables, var_attrs, global_attrs)

    def variable_stmt(self, items: list[Any]) -> Any:
        return items[0]

    def variable_decl(self, items: list[Any]) -> tuple[str, Variable]:
        dtype = str(items[0])
        name = str(items[1])
        dims = items[2] if len(items) > 2 else []
        return ("decl", Variable(name=name, dtype=dtype, dims=dims))

    def name_list(self, items: list[Any]) -> list[str]:
        return [str(item) for item in items]

    def attribute_stmt(self, items: list[Any]) -> tuple[str, str | None, str, Any]:
        if len(items) == 2:
            target = None
            key = str(items[0])
            value = items[1]
        else:
            target = str(items[0])
            key = str(items[1])
            value = items[2]
        return ("attr", target, key, value)

    def data_section(self, items: list[Any]) -> tuple[str, dict[str, list[Any]]]:
        return ("data", dict(items))

    def data_stmt(self, items: list[Any]) -> tuple[str, list[Any]]:
        return (str(items[0]), items[1])

    def data_list(self, items: list[Any]) -> list[Any]:
        return list(items)

    def string(self, items: list[Any]) -> str:
        return py_ast.literal_eval(str(items[0]))

    def number(self, items: list[Any]) -> int | float:
        text = str(items[0])
        if any(ch in text for ch in (".", "e", "E")):
            return float(text)
        return int(text)

    def bare_name(self, items: list[Any]) -> str:
        return str(items[0])

    def fill_value(self, _items: list[Any]) -> str:
        return "_"
