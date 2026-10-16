"""
Daily satellite sea level along the equatorial Pacific, for tracking Kelvin waves.

NOAA's blended near-real-time altimetry product (sea surface height anomaly, 0.25°, daily, from
2017; via NOAA CoastWatch ERDDAP, dataset noaacwBLENDEDsshDaily). Only a thin equatorial band is
read (1°S–1°N, every 1° of longitude, 120°E–80°W) and cached in data/sealevel/: daily values by
month for the period shown, and every fifth day for the 2017–2024 baseline.

A downwelling Kelvin wave raises sea level by a few centimetres as it travels east along the
equator, so it appears as a diagonal ridge in a longitude–time diagram.
"""
from __future__ import annotations

import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

from enso_common import HERE

ERDDAP = "https://coastwatch.noaa.gov/erddap/griddap/noaacwBLENDEDsshDaily.nc"
CACHE = HERE / "data" / "sealevel"
LAT = (-1.0, 1.0)
CHUNKS = [(120.125, 179.875), (-179.875, -80.125)]       # the dataset's longitudes run −180 to 180
CLIM = (2017, 2024)                                      # complete years available for a seasonal cycle
SOURCE = "NOAA blended altimetry sea level anomaly (CoastWatch ERDDAP, noaacwBLENDEDsshDaily)"


def _get(path, t0, t1, stride, lon0, lon1):
    q = f"sla[({t0}):{stride}:({t1})][({LAT[0]}):1:({LAT[1]})][({lon0}):4:({lon1})]"
    url = ERDDAP + "?" + urllib.parse.quote(q, safe="")
    tmp = path.with_suffix(".part")
    for attempt in range(1, 4):                          # the server occasionally returns a proxy error
        try:
            urllib.request.urlretrieve(url, tmp)
            break
        except OSError:
            if attempt == 3:
                raise
    tmp.replace(path)


def _read(paths):
    import xarray as xr
    frames = []
    for p in paths:
        with xr.open_dataset(p) as ds:
            frames.append(ds["sla"].mean("latitude").load().to_pandas())
    df = pd.concat(frames, axis=1)
    df.columns = [round(c % 360, 3) for c in df.columns]
    df.index = pd.to_datetime(df.index).normalize()
    return df[~df.index.duplicated()].sort_index() * 100.0              # m → cm


def daily(start, end=None, refresh=False):
    """Daily equatorial sea level (cm), DataFrame (date × longitude 0–360), from `start` to the latest day."""
    CACHE.mkdir(parents=True, exist_ok=True)
    today = pd.Timestamp.today().normalize()
    end = pd.Timestamp(end) if end else today
    out = []
    for m in pd.date_range(pd.Timestamp(start).replace(day=1), end, freq="MS"):
        last = min(m + pd.offsets.MonthEnd(0), end)
        current = m.year == today.year and m.month == today.month
        paths = []
        for lon0, lon1 in CHUNKS:
            p = CACHE / f"daily_{m:%Y_%m}_{int(lon0)}.nc"
            if not p.exists() or (refresh and current) or (current and p.stat().st_mtime < today.timestamp()):
                print(f"Reading NOAA altimetry, {m:%B %Y} ...", flush=True)
                t1 = "last" if current else f"{last:%Y-%m-%d}T00:00:00Z"
                _get(p, f"{m:%Y-%m-%d}T00:00:00Z", t1, 1, lon0, lon1)
            paths.append(p)
        out.append(_read(paths))
    return pd.concat(out).loc[pd.Timestamp(start):end]


def baseline():
    """Every fifth day of 2017–2024, for the seasonal cycle."""
    CACHE.mkdir(parents=True, exist_ok=True)
    out = []
    for y in range(CLIM[0], CLIM[1] + 1):
        paths = []
        for lon0, lon1 in CHUNKS:
            p = CACHE / f"clim_{y}_{int(lon0)}.nc"
            if not p.exists():
                print(f"Reading NOAA altimetry baseline, {y} ...", flush=True)
                _get(p, f"{y}-01-01T00:00:00Z", f"{y}-12-31T00:00:00Z", 5, lon0, lon1)
            paths.append(p)
        out.append(_read(paths))
    return pd.concat(out)


def anomalies(df):
    """Remove each longitude's 2017–2024 mean seasonal cycle (monthly means, interpolated to days),
    which also removes the long-term offset of the sea level record, then smooth with a 5-day running
    mean."""
    base = baseline()
    monthly = base.groupby(base.index.month).mean()
    doy = df.index.dayofyear.values
    centres = np.array([15, 45, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349])
    x = np.concatenate([centres - 365, centres, centres + 365])
    clim = np.stack([np.interp(doy, x, np.tile(monthly[c].values, 3)) for c in df.columns], axis=1)
    return (df - clim).rolling(5, center=True, min_periods=3).mean()
