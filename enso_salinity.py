"""
Daily satellite sea surface salinity along the equator: NASA's SMAP mission, NOAA CoastWatch near-real-time
product (0.25°, daily, 2015 onward, via NOAA CoastWatch ERDDAP), averaged over 1°S–1°N every 1° of longitude.
Cached in data/salinity/ and re-read once a day; the last copy is used if the server fails.

Salinity changes as rain falls and as currents carry fresher or saltier water. During El Niño the rain belt and
the fresh water of the western Pacific move east, so the central Pacific freshens. The Kelvin-wave signal is the
5-day running mean minus its centred 91-day running mean, as for the other variables; the 91-day filter removes
the seasonal cycle, so no separate climatology is needed.
"""
import time
import urllib.request

import numpy as np
import pandas as pd

from enso_common import HERE

CACHE = HERE / "data" / "salinity"
ERDDAP = "https://coastwatch.noaa.gov/erddap/griddap/noaacwSMAPsssDaily.nc"


def smap_equator(start, refresh=False):
    """Daily equatorial sea surface salinity (psu), DataFrame (date × longitude 0–360), from `start` to the latest day."""
    import xarray as xr
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"smap_eq_{pd.Timestamp(start):%Y%m%d}.nc"
    today = pd.Timestamp.today().normalize().timestamp()
    if refresh or not path.exists() or path.stat().st_mtime < today:
        q = (f"sss%5B({pd.Timestamp(start):%Y-%m-%d}T12:00:00Z):1:(last)%5D%5B(0.0)%5D%5B(-1.0):1:(1.0)%5D"
             f"%5B(-179.875):4:(179.875)%5D")
        tmp = path.with_suffix(".part")
        for attempt in range(1, 6):
            try:
                urllib.request.urlretrieve(f"{ERDDAP}?{q}", tmp)
                tmp.replace(path)
                break
            except OSError:
                if attempt == 5:
                    if not path.exists():
                        raise
                    print("NOAA satellite salinity unavailable: using the saved data", flush=True)
                else:
                    time.sleep(20 * attempt)
    with xr.open_dataset(path) as ds:
        s = ds["sss"].squeeze("altitude", drop=True).mean("latitude").load()
    df = s.to_pandas()
    df.columns = np.round(np.asarray(df.columns, float) % 360, 3)
    df = df.sort_index(axis=1)
    df.index = pd.to_datetime(df.index).normalize()
    return df[~df.index.duplicated()]


def clean(s, lons=(160, 270)):
    """Pacific part of the daily record with retrieval errors removed and short gaps filled: values more than
    1 psu from the 15-day running median at their longitude, and whole days whose Pacific mean departs by more
    than 5 median absolute deviations from its own 15-day running median (bad swaths), are dropped; gaps of up
    to 10 days in time and 3° in longitude are interpolated, and values are smoothed over 3° of longitude."""
    s = s.loc[:, lons[0]:lons[1]].copy()
    med = s.rolling(15, center=True, min_periods=5).median()
    s[(s - med).abs() > 1.0] = np.nan
    day = s.mean(axis=1)
    dev = day - day.rolling(15, center=True, min_periods=5).median()
    s[(dev.abs() > 5 * (dev.abs().median() / 0.6745)).values] = np.nan
    s = s.interpolate(limit=10, limit_area="inside")
    s = s.T.interpolate(method="index", limit=3, limit_area="inside").T
    return s.T.rolling(3, center=True, min_periods=2).mean().T


def salinity_signal(start, refresh=False):
    """Kelvin-wave signal in sea surface salinity (psu): cleaned 5-day means minus their centred 91-day running
    mean."""
    s = clean(smap_equator(start, refresh)).rolling(5, center=True, min_periods=3).mean()
    return s - s.rolling(91, center=True, min_periods=31).mean()
