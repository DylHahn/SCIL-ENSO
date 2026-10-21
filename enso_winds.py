"""
Equatorial Pacific surface winds from NOAA NCEI's Blended Sea Winds v2 (NBS v2; daily, 0.25°,
July 1987 onward), read from NCEI's THREDDS server.

Only the east–west (zonal) wind at 10 m is used, averaged over 5°S–5°N on a 2° longitude grid
from 120°E to 80°W. Daily anomalies are relative to NCEI's 1991–2020 monthly climatology,
interpolated to each day. The daily files are subset over OPeNDAP and cached month by month in
data/winds/; the climatology file (about 250 MB) is downloaded once.
"""
import re
import subprocess
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

from enso_common import HERE

WIND_DIR = HERE / "data" / "winds"
THREDDS = "https://www.ncei.noaa.gov/thredds"
CLIM_URL = ("https://www.ncei.noaa.gov/data/blended-global-sea-surface-wind-products/access/climatology/"
            "NBS_v02_wind_climmonthly_s1991_e2020_c20221206.nc")
LAT, LON = (-5, 5), (120, 280)
FIRST = pd.Timestamp("1987-08-01")


def _catalog(year):
    """{date: OPeNDAP path} of the daily files NCEI holds for `year`."""
    url = f"{THREDDS}/catalog/uv/reprocessed_winds/{year}/daily/catalog.xml"
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            xml = r.read().decode()
    except urllib.error.HTTPError as e:
        if e.code == 404:                                   # a year NCEI has not started yet
            return {}
        raise
    paths = re.findall(r'urlPath="([^"]*NBS_v02_wind_daily_d(\d{8})_c\d+\.nc)"', xml)
    return {pd.Timestamp(d): p for p, d in paths}


# grid indices of the subset on NBS v2's 0.25° grid (lat −89.75…89.75, lon 0…359.75): 5°S–5°N every 1°,
# 120°E–80°W every 2°
_LAT_I = (int((LAT[0] + 89.75) / 0.25), 4, int((LAT[1] + 89.75) / 0.25))
_LON_I = (int(LON[0] / 0.25), 8, int(LON[1] / 0.25))
SUB_LAT = np.arange(LAT[0], LAT[1] + 0.1, 1.0)
SUB_LON = np.arange(LON[0], LON[1] + 0.1, 2.0)


def _day(path, tries=5):
    """(lon,) zonal wind for one daily file, averaged over 5°S–5°N (cosine-weighted, ignoring land).
    Read as OPeNDAP ASCII, which is safe to request from several threads at once."""
    q = "u_wind%5B0%5D%5B0%5D%5B{0}:{1}:{2}%5D%5B{3}:{4}:{5}%5D".format(*_LAT_I, *_LON_I)
    url = f"{THREDDS}/dodsC/{path}.ascii?{q}"
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                text = r.read().decode()
            break
        except OSError:
            if k == tries - 1:
                raise
            time.sleep(5 * (k + 1))
    body = text.split("---------------------------------------------", 1)[1]
    rows = [line.split(",", 1)[1] for line in body.splitlines() if line.startswith("[0][0][")]
    vals = np.array([[float(v) for v in r.split(",")] for r in rows])          # (lat, lon)
    vals[vals <= -9000] = np.nan
    w = np.cos(np.deg2rad(SUB_LAT))[:, None] * np.isfinite(vals)
    with np.errstate(invalid="ignore"):
        return np.nansum(np.nan_to_num(vals) * w, axis=0) / w.sum(axis=0)


def daily_u(month, refresh=False):
    """Daily 5°S–5°N zonal wind (m/s) as a (time, lon) DataArray for the calendar month starting
    `month`, or None if NCEI has no files for it. Complete months are cached; a month that NCEI has
    not finished is re-read on refresh."""
    import xarray as xr
    month = pd.Timestamp(month)
    path = WIND_DIR / f"u10_{month:%Y_%m}.nc"
    if path.exists() and not refresh:
        return xr.open_dataarray(path).load()
    days = {d: p for d, p in _catalog(month.year).items() if d.month == month.month}
    if not days:
        return None
    with ThreadPoolExecutor(8) as ex:
        parts = list(ex.map(_day, days.values()))
    u = xr.DataArray(np.stack(parts), dims=("time", "lon"), coords=dict(time=list(days), lon=SUB_LON),
                     name="u_wind").sortby("time")
    WIND_DIR.mkdir(parents=True, exist_ok=True)
    if len(days) == month.days_in_month:                      # cache only complete months
        u.to_netcdf(path)
    return u


def monthly_normal():
    """(12, lon) 1991–2020 mean 5°S–5°N zonal wind for each calendar month."""
    import xarray as xr
    band = WIND_DIR / "u10_normal_1991_2020.nc"
    if not band.exists():
        full = WIND_DIR / "clim_monthly.nc"
        WIND_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-sS", "-f", "--retry", "5", "-o", str(full), CLIM_URL], check=True)
        with xr.open_dataset(full) as ds:
            u = ds["u_wind"].squeeze(drop=True).sel(lat=slice(*LAT), lon=slice(*LON))[:, ::4, ::8].load()
        u = u.weighted(np.cos(np.deg2rad(u["lat"]))).mean("lat")
        u.name = "u_wind"
        u.to_netcdf(band)
        full.unlink()
    return xr.open_dataarray(band).load()


def daily_anomaly(start, end, refresh=False):
    """Daily zonal wind anomaly (m/s) over 5°S–5°N from `start` to `end` (or NCEI's latest day), as a
    (time, lon) DataArray; the 1991–2020 monthly normal is interpolated to each day (mid-month anchors)."""
    import xarray as xr
    months = [m for m in pd.date_range(pd.Timestamp(start).replace(day=1), end, freq="MS") if m >= FIRST]
    recent = pd.Timestamp.today().normalize().replace(day=1) - pd.DateOffset(months=2)
    parts = [daily_u(m, refresh=refresh and m >= recent) for m in months]
    u = xr.concat([p for p in parts if p is not None], "time").sel(time=slice(start, end))
    clim = monthly_normal().values                        # (12, lon)
    mid = np.array([15, 45, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349], dtype=float)
    doy = pd.DatetimeIndex(u["time"].values).dayofyear.values.astype(float)
    xs = np.concatenate([mid - 365, mid, mid + 365])
    cv = np.concatenate([clim] * 3)
    normal = np.stack([np.interp(doy, xs, cv[:, j]) for j in range(cv.shape[1])], axis=1)
    return u - normal
