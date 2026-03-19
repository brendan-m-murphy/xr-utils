from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xr_utils.cdl.parser import parse_cdl


def test_parse_minimal_dataset() -> None:
    text = """
netcdf test {
dimensions:
  time = 3 ;
variables:
  float temp(time) ;
}
"""
    ds = parse_cdl(text)

    assert ds.name == "test"
    assert ds.dims == {"time": 3}
    assert "temp" in ds.variables
    assert ds.variables["temp"].dtype == "float"
    assert ds.variables["temp"].dims == ["time"]


def test_parse_dataset_with_attrs_and_data() -> None:
    text = """
netcdf test {
dimensions:
  time = 3 ;
variables:
  float temp(time) ;
  temp:units = "K" ;
  :title = "example" ;
data:
  temp = 1, 2, 3 ;
}
"""
    ds = parse_cdl(text)

    assert ds.dims == {"time": 3}
    assert ds.attrs["title"] == "example"
    assert ds.variables["temp"].attrs["units"] == "K"
    assert ds.variables["temp"].data == [1, 2, 3]
