"""
Daily sea surface temperature for the Southern California Bight from NOAA OISST v2.1
(0.25°, 1981–present), via NOAA CoastWatch ERDDAP.

Each year is downloaded once as a small CSV subset (the box below) and cached in
data/oisst/; only the current year is re-fetched on refresh. Marine heatwaves follow
Hobday et al. (2016): SST above the day-of-year 90th percentile (1991–2020, 11-day
window) for at least five consecutive days.
"""

from __future__ import annotations

import io
import urllib.request

import numpy as np
import pandas as pd

from enso_common import HERE

ERDDAP = ("https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.csv?"
          "sst%5B({t0}):1:({t1})%5D%5B(0.0)%5D%5B({la0}):1:({la1})%5D%5B({lo0}):1:({lo1})%5D")
CACHE = HERE / "data" / "oisst"
# Southern California Bight, offshore of Point Conception to the Mexican border
BOX = dict(lat=(32.5, 34.5), lon=(-120.5, -117.5))
FIRST_YEAR = 1982
CLIM = (1991, 2020)


def _fetch_year(year, end=None):
    t1 = end or f"{year}-12-31T12:00:00Z"
    url = ERDDAP.format(t0=f"{year}-01-01T12:00:00Z", t1=t1, la0=BOX["lat"][0], la1=BOX["lat"][1],
                        lo0=BOX["lon"][0], lo1=BOX["lon"][1])
    with urllib.request.urlopen(url, timeout=300) as r:
        df = pd.read_csv(io.BytesIO(r.read()), skiprows=[1])          # 2nd row holds units
    df["time"] = pd.to_datetime(df["time"]).dt.tz_localize(None).dt.normalize()
    w = np.cos(np.deg2rad(df["latitude"]))
    df = df.dropna(subset=["sst"])
    df["w"] = w.loc[df.index]
    df["ws"] = df["sst"] * df["w"]
    g = df.groupby("time")
    return (g["ws"].sum() / g["w"].sum()).rename("sst")


def bight_sst(refresh=False, current_year=None) -> pd.Series:
    """Area-weighted daily mean SST (°C) over BOX, FIRST_YEAR to the latest available day."""
    CACHE.mkdir(parents=True, exist_ok=True)
    current_year = current_year or pd.Timestamp.today().year
    parts = []
    for y in range(FIRST_YEAR, current_year + 1):
        path = CACHE / f"bight_{y}.csv"
        if path.exists() and not (refresh and y == current_year):
            s = pd.read_csv(path, index_col=0, parse_dates=True)["sst"]
        else:
            print(f"Downloading OISST {y} for the Southern California Bight ...")
            try:
                s = _fetch_year(y)
            except Exception:                                  # current year: request up to the last day
                s = _fetch_year(y, end="last")
            s.to_frame().to_csv(path)
        parts.append(s)
    return pd.concat(parts).sort_index()


def climatology(sst):
    """Day-of-year mean and 90th percentile over CLIM, 11-day window, Feb 29 folded into Feb 28."""
    base = sst.loc[str(CLIM[0]):str(CLIM[1])]
    doy = np.minimum(base.index.dayofyear - ((base.index.is_leap_year) & (base.index.month > 2)), 365)
    mean, p90 = np.zeros(366), np.zeros(366)
    vals, days = base.values, np.asarray(doy)
    for d in range(1, 366):
        dist = np.abs(((days - d + 182) % 365) - 182)
        sel = vals[dist <= 5]
        mean[d], p90[d] = sel.mean(), np.percentile(sel, 90)
    return mean, p90


def doy_index(idx):
    return np.minimum(idx.dayofyear - ((idx.is_leap_year) & (idx.month > 2)), 365)


def anomalies_and_mhw(sst):
    """(daily anomaly series, boolean marine-heatwave series)."""
    mean, p90 = climatology(sst)
    d = doy_index(sst.index)
    anom = pd.Series(sst.values - mean[d], index=sst.index)
    above = pd.Series(sst.values > p90[d], index=sst.index)
    run_id = (above != above.shift()).cumsum()
    run_len = above.groupby(run_id).transform("sum")
    mhw = above & (run_len >= 5)
    return anom, mhw


# ---------------------------------------------------------------------------
# Monthly OISST v2.1 (0.25°) for the tropical Pacific, for the animations
# ---------------------------------------------------------------------------
PSL_OISST = "https://downloads.psl.noaa.gov/Datasets/noaa.oisst.v2.highres/{name}"
PACIFIC = dict(lat=(-25, 25), lon=(110, 290))


def pacific_monthly(months, refresh=False):
    """(time, lat, lon) monthly mean SST (°C) over the tropical Pacific for the requested months.
    Reads only this window from NOAA PSL's 2.2 GB file over HTTP and caches it."""
    import xarray as xr
    path = HERE / "data" / "oisst_monthly" / "pacific_sst.nc"
    path.parent.mkdir(parents=True, exist_ok=True)
    have = None
    if path.exists():
        with xr.open_dataarray(path) as da:
            have = da.load()
    want = pd.DatetimeIndex(months)
    got = pd.DatetimeIndex([]) if have is None else pd.to_datetime(have["time"].values)
    missing = want.difference(got) if not refresh else want
    if len(missing):
        print(f"Reading {len(missing)} months of OISST for the tropical Pacific from NOAA PSL ...")
        with xr.open_dataset(PSL_OISST.format(name="sst.mon.mean.nc") + "#mode=bytes") as ds:
            avail = set(pd.to_datetime(ds["time"].values))
            pick = [t for t in missing if t in avail]
            new = (ds["sst"].sel(time=pick, lat=slice(*PACIFIC["lat"]), lon=slice(*PACIFIC["lon"])).load()
                   if pick else None)
        if new is None:                                    # requested months not published yet
            return have.sel(time=have["time"].isin(want.values))
        if have is not None:
            have = have.drop_sel(time=[t for t in pick if t in set(got)])
        have = new if have is None else xr.concat([have, new], "time").sortby("time")
        have.name = "sst"
        have.to_netcdf(path)
    return have.sel(time=have["time"].isin(want.values))


def pacific_normals():
    """(month, lat, lon) 1991–2020 monthly normal SST (°C), from NOAA PSL's long-term-mean file."""
    import urllib.request
    import xarray as xr
    path = HERE / "data" / "oisst_monthly" / "sst.mon.ltm.1991-2020.nc"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        print("Downloading OISST 1991–2020 monthly normals (46 MB) ...")
        urllib.request.urlretrieve(PSL_OISST.format(name="sst.mon.ltm.1991-2020.nc"), path)
    with xr.open_dataset(path, decode_times=False) as ds:
        ltm = ds["sst"].sel(lat=slice(*PACIFIC["lat"]), lon=slice(*PACIFIC["lon"])).load()
    return ltm.rename(time="month").assign_coords(month=range(1, 13))
