"""
NOAA nClimGrid monthly (~5 km gridded temperature for the contiguous US), read for
Southern California only.

The full-record files on NCEI are ~1.5 GB each, so this reads just the SoCal window
of the months it needs over HTTP (netCDF byte-range access) and caches them in
data/nclimgrid/socal_<var>.nc. Later runs only fetch months that are missing, so
a monthly refresh downloads a few MB.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

from enso_common import HERE

URL = "https://www.ncei.noaa.gov/data/nclimgrid-monthly/access/nclimgrid_{var}.nc#mode=bytes"
CACHE = HERE / "data" / "nclimgrid"
# Southern California window: Point Conception to the Mexican border, coast to the Colorado River
LAT = (32.45, 35.15)
LON = (-121.0, -114.4)
SUMMER = [6, 7, 8, 9]


def socal_months(var, months, refresh=False) -> xr.DataArray:
    """(time, lat, lon) in °C for the requested first-of-month timestamps, cached locally."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"socal_{var}.nc"
    have = None
    if path.exists() and not refresh:
        with xr.open_dataarray(path) as da:
            have = da.load()
    want = pd.DatetimeIndex(months)
    got = pd.DatetimeIndex([]) if have is None else pd.to_datetime(have["time"].values)
    missing = want.difference(got)
    if len(missing):
        print(f"Reading {len(missing)} months of nClimGrid {var} for Southern California from NCEI ...")
        with xr.open_dataset(URL.format(var=var)) as ds:
            avail = pd.to_datetime(ds["time"].values).to_period("M")
            pick = [t for t in missing if t.to_period("M") in set(avail)]
            idx = [int(np.flatnonzero(avail == t.to_period("M"))[0]) for t in pick]
            new = ds[var].isel(time=idx).sel(lat=slice(LAT[1], LAT[0]), lon=slice(*LON)).load()
        new = new.assign_coords(time=pd.DatetimeIndex(pick))
        have = new if have is None else xr.concat([have, new], "time").sortby("time")
        have.name = var
        have.to_netcdf(path)
    return have.sel(time=have["time"].isin(want.values))


def summer_months(years):
    return [pd.Timestamp(year=y, month=m, day=1) for y in years for m in SUMMER]


def latest_available(var):
    """Last month in NCEI's file (to know whether a summer is complete)."""
    with xr.open_dataset(URL.format(var=var)) as ds:
        return pd.Timestamp(ds["time"].values[-1])
