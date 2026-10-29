"""
Marine heatwaves along the Pacific coast of the Americas, from NOAA OISST v2.1 daily sea surface
temperature (0.25°, read every 1° over 25°S–45°N, 150°W–70°W) via NOAA PSL.

Following Hobday et al. (2016), a marine heatwave is SST above the day-of-year 90th percentile of
1991–2020 (11-day window, then a 31-day running mean) for at least five consecutive days, with
gaps of two days or less joined. Categories follow Hobday et al. (2018): the excess over the
climatological mean in multiples of the difference between the 90th percentile and the mean,
I Moderate (1–2×), II Strong (2–3×), III Severe (3–4×), IV Extreme (≥ 4×).

Each year is downloaded once and cached in data/oisst_mhw/; the current year is re-read on refresh.
"""
import subprocess
from concurrent.futures import ThreadPoolExecutor
import time

import numpy as np
import pandas as pd

from enso_common import HERE

CACHE = HERE / "data" / "oisst_mhw"
# NOAA PSL's THREDDS subset service; one month per request (larger requests time out)
NCSS = ("https://psl.noaa.gov/thredds/ncss/grid/Datasets/noaa.oisst.v2.highres/sst.day.mean.{y}.nc?var=sst"
        "&north=45&south=-25.25&west=209.75&east=290&horizStride=4&time_start={t0}T00:00:00Z"
        "&time_end={t1}T00:00:00Z&accept=netcdf")
FILE = "https://downloads.psl.noaa.gov/Datasets/noaa.oisst.v2.highres/sst.day.mean.{y}.nc"
CLIM = (1991, 2020)
CATEGORIES = ["I Moderate", "II Strong", "III Severe", "IV Extreme"]
# Hobday et al. (2018) colours
CAT_COLORS = ["#ffc866", "#ff6900", "#9e0000", "#2d0000"]


def _month(year, month, path):
    t0 = pd.Timestamp(year=year, month=month, day=1)
    t1 = min(t0 + pd.offsets.MonthEnd(0), pd.Timestamp.today().normalize() - pd.Timedelta(days=1))
    if t1 < t0:
        return None
    tmp = path.with_suffix(f".{month:02d}.part")
    for k in range(6):
        r = subprocess.run(["curl", "-sS", "-f", "--http1.1", "-m", "300", "-o", str(tmp),
                            NCSS.format(y=year, t0=f"{t0:%Y-%m-%d}", t1=f"{t1:%Y-%m-%d}")], capture_output=True)
        if r.returncode == 0:
            return tmp
        if year == pd.Timestamp.today().year and b"400" in r.stderr:   # month not published yet
            return None
        time.sleep(10 * (k + 1))
    raise RuntimeError(f"Could not download OISST {year}-{month:02d}: {r.stderr.decode().strip()}")


def _year_bytes(year):
    """The same subset read from NOAA PSL's yearly file over HTTP byte ranges (slower: the file is
    stored one global field per day)."""
    import xarray as xr
    with xr.open_dataset(FILE.format(y=year) + "#mode=bytes") as ds:
        return ds["sst"].sel(lat=slice(-25.25, 45), lon=slice(209.75, 290))[:, ::4, ::4].load()


def _year(year, refresh=False, direct=False):
    """(time, lat, lon) daily SST (°C) for one year, longitudes in °E (−150 to −70); `direct` reads
    the yearly file instead of using the subset service."""
    import xarray as xr
    path = CACHE / f"sst_{year}.nc"
    if refresh or not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        try:
            if direct:
                raise RuntimeError
            with ThreadPoolExecutor(3) as ex:                # curl downloads only; files are read below
                parts = list(ex.map(lambda m: _month(year, m, path), range(1, 13)))
            das = []
            for f in [f for f in parts if f is not None]:
                with xr.open_dataset(f) as ds:
                    das.append(ds["sst"].load())
                f.unlink()
            da = xr.concat(das, "time")
        except RuntimeError:                                 # subset service unavailable: read the file directly
            da = _year_bytes(year)
        da = da.assign_coords(lon=da["lon"].values - 360, time=pd.to_datetime(da["time"].values).normalize())
        da.encoding = {}
        da.to_netcdf(path)
    with xr.open_dataarray(path) as da:
        return da.load()


def daily_sst(start, end=None, refresh=False):
    import xarray as xr
    y0, y1 = pd.Timestamp(start).year, pd.Timestamp(end or pd.Timestamp.today()).year
    now = pd.Timestamp.today().year
    da = xr.concat([_year(y, refresh and y == now) for y in range(y0, y1 + 1)], "time")
    return da.sel(time=slice(start, end))


def _doy(times):
    t = pd.DatetimeIndex(times)
    return np.minimum(t.dayofyear - ((t.is_leap_year) & (t.month > 2)), 365) - 1      # 0..364


def climatology():
    """(365, lat, lon) day-of-year mean and 90th percentile over CLIM, cached."""
    import xarray as xr
    path = CACHE / f"clim_{CLIM[0]}_{CLIM[1]}.nc"
    if path.exists():
        with xr.open_dataset(path) as ds:
            return ds["mean"].load(), ds["p90"].load()
    sst = daily_sst(f"{CLIM[0]}-01-01", f"{CLIM[1]}-12-31")
    vals = sst.values.astype("float32")
    doy = _doy(sst["time"].values)
    mean = np.full((365,) + vals.shape[1:], np.nan, "float32")
    p90 = mean.copy()
    for d in range(365):
        win = np.abs((doy - d + 182) % 365 - 182) <= 5                # 11-day window, wrapping the year
        sel = vals[win]
        mean[d] = np.nanmean(sel, axis=0)
        p90[d] = np.nanpercentile(sel, 90, axis=0)

    def smooth(a):                                                    # 31-day running mean, periodic
        ext = np.concatenate([a[-15:], a, a[:15]])
        c = np.cumsum(np.nan_to_num(ext), axis=0)
        c = np.concatenate([np.zeros((1,) + a.shape[1:]), c])
        out = (c[31:] - c[:-31]) / 31
        return np.where(np.isnan(a), np.nan, out).astype("float32")
    coords = dict(doy=np.arange(365), lat=sst["lat"], lon=sst["lon"])
    ds = xr.Dataset(dict(mean=(("doy", "lat", "lon"), smooth(mean)), p90=(("doy", "lat", "lon"), smooth(p90))),
                    coords=coords)
    ds.to_netcdf(path)
    return ds["mean"], ds["p90"]


def heatwaves(start, end=None, refresh=False):
    """Daily (anomaly, category) over the region from `start` (with 30 days' lead for detection):
    anomaly in °C from the 1991–2020 day-of-year mean; category 0 (no heatwave) to 4 (IV Extreme)."""
    import xarray as xr
    lead = pd.Timestamp(start) - pd.Timedelta(days=30)
    sst = daily_sst(lead, end, refresh)
    mean, p90 = climatology()
    d = _doy(sst["time"].values)
    m, p = mean.values[d], p90.values[d]
    v = sst.values
    anom = v - m
    above = v > p
    # runs of at least 5 days above the threshold, gaps of up to 2 days joined (Hobday et al. 2016)
    n = len(v)
    mhw = np.zeros_like(above)
    flat = above.reshape(n, -1)
    out = mhw.reshape(n, -1)
    for j in np.flatnonzero(flat.any(axis=0)):
        col = flat[:, j]
        runs, s = [], None
        for i, h in enumerate(np.append(col, False)):
            if h and s is None:
                s = i
            elif not h and s is not None:
                runs.append([s, i - 1])
                s = None
        runs = [r for r in runs if r[1] - r[0] + 1 >= 5]
        joined = []
        for r in runs:
            if joined and r[0] - joined[-1][1] - 1 <= 2:
                joined[-1][1] = r[1]
            else:
                joined.append(r)
        for r0, r1 in joined:
            out[r0:r1 + 1, j] = True
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = anom / (p - m)
    cat = np.where(mhw, np.clip(np.floor(ratio), 1, 4), 0)
    cat = np.where(np.isfinite(v), cat, np.nan)
    keep = pd.DatetimeIndex(sst["time"].values) >= pd.Timestamp(start)
    coords = dict(time=sst["time"].values[keep], lat=sst["lat"], lon=sst["lon"])
    return (xr.DataArray(anom[keep], coords=coords, dims=("time", "lat", "lon")),
            xr.DataArray(cat[keep], coords=coords, dims=("time", "lat", "lon")))
