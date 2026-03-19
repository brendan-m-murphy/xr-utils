"""Conversion from minimal CDL to xarray.Dataset."""

from __future__ import annotations

import numpy as np
import xarray as xr

from xr_utils.cdl.parser import parse_cdl

_DTYPE_MAP: dict[str, str] = {
    "byte": "int8",
    "short": "int16",
    "int": "int32",
    "float": "float32",
    "double": "float64",
    "char": "U1",
}


def _resolve_dim_sizes(ast_dataset) -> dict[str, int]:
    sizes: dict[str, int] = {}
    for dim_name, dim_size in ast_dataset.dims.items():
        sizes[dim_name] = 0 if dim_size is None else dim_size

    for variable in ast_dataset.variables.values():
        if not variable.data:
            continue
        if len(variable.dims) == 1:
            dim_name = variable.dims[0]
            if ast_dataset.dims.get(dim_name) is None and sizes[dim_name] == 0:
                sizes[dim_name] = len(variable.data)

    return sizes


def cdl_to_dataset(text: str) -> xr.Dataset:
    """Parse CDL and produce a simple xarray.Dataset."""
    ast_dataset = parse_cdl(text)
    dim_sizes = _resolve_dim_sizes(ast_dataset)

    coords = {name: np.arange(size) for name, size in dim_sizes.items()}

    data_vars: dict[str, tuple[list[str], np.ndarray, dict]] = {}
    for var_name, variable in ast_dataset.variables.items():
        dims = variable.dims
        dtype = np.dtype(_DTYPE_MAP[variable.dtype])
        shape = tuple(dim_sizes[dim] for dim in dims)
        total_size = int(np.prod(shape, dtype=np.int64)) if shape else 1

        if variable.data is None:
            arr = np.zeros(shape if shape else (), dtype=dtype)
        else:
            cleaned = [0 if value == "_" else value for value in variable.data]
            flat = np.asarray(cleaned, dtype=dtype).reshape(-1)
            if flat.size > total_size:
                flat = flat[:total_size]
            elif flat.size < total_size:
                pad = np.zeros(total_size - flat.size, dtype=dtype)
                flat = np.concatenate([flat, pad])
            arr = flat.reshape(shape if shape else ())

        attrs = dict(variable.attrs)
        data_vars[var_name] = (dims, arr, attrs)

    ds = xr.Dataset(attrs=dict(ast_dataset.attrs))
    ds = ds.assign_coords(coords)

    for name, (dims, arr, attrs) in data_vars.items():
        ds[name] = xr.DataArray(arr, dims=dims, attrs=attrs)

    return ds
