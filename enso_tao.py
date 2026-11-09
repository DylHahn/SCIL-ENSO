"""
Daily measurements from the TAO/TRITON moored buoys on the equator (NOAA PMEL, via NOAA CoastWatch ERDDAP):
the depth of the 20 °C isotherm, dynamic height (0/500 dbar, a measure of surface height computed from the
buoy's temperature profile), sea surface temperature and zonal wind. Eight moorings, 165°E to 95°W, about 10–15°
of longitude apart, are in place through every El Niño since 1997/1998. Records are cached in data/tao/.

A downwelling Kelvin wave deepens the 20 °C isotherm by tens of metres and raises surface height as it passes.
Anomalies are departures from each mooring's 1991–2020 seasonal cycle (three harmonics), smoothed with a 5-day
running mean. The Kelvin-wave signal is the anomaly minus its centred 91-day running mean, as for the
satellite sea level in anim_kelvin.py, and its rate of change is the centred difference over four days.
"""
import io
import time
import urllib.request

import numpy as np
import pandas as pd

from enso_common import HERE

CACHE = HERE / "data" / "tao"
URL = ("https://coastwatch.pfeg.noaa.gov/erddap/tabledap/{ds}.csv?time,longitude,{var}"
       "&latitude%3E=-0.5&latitude%3C=0.5&time%3E=1991-01-01")
VARIABLES = {"d20": ("pmelTaoDyIso", "ISO_6"), "dyn": ("pmelTaoDyDyn", "DYN_13"),
             "sst": ("pmelTaoDySst", "T_25"), "wind": ("pmelTaoDyW", "WU_422")}
LONS = [165, 180, 190, 205, 220, 235, 250, 265]
CLIM = (1991, 2020)
INFILL_DAYS = 10                           # gaps in time filled up to this length; across one mooring at most


def _csv(name, refresh=False):
    """The cached ERDDAP table for one variable, re-read once a day; the last copy is used if the server fails."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.csv"
    today = pd.Timestamp.today().normalize().timestamp()
    if refresh or not path.exists() or path.stat().st_mtime < today:
        ds, var = VARIABLES[name]
        request = urllib.request.Request(URL.format(ds=ds, var=var), headers={"User-Agent": "enso-public-viz/1.0"})
        for attempt in range(1, 6):
            try:
                with urllib.request.urlopen(request, timeout=240) as r:
                    path.write_bytes(r.read())
                break
            except OSError:
                if attempt == 5:
                    if not path.exists():
                        raise
                    print(f"NOAA PMEL buoys unavailable: using the saved {name} data", flush=True)
                else:
                    time.sleep(20 * attempt)
    return pd.read_csv(io.BytesIO(path.read_bytes()), skiprows=[1], parse_dates=["time"])


def daily(name, refresh=False):
    """Daily values, DataFrame (date × mooring longitude, 0–360)."""
    var = VARIABLES[name][1]
    d = _csv(name, refresh)
    d["lon"] = (d["longitude"] % 360).round().astype(int)
    d = d[d["lon"].isin(LONS) & (d[var].abs() < 1e6)]
    df = d.pivot_table(index=d["time"].dt.tz_localize(None).dt.normalize(), columns="lon", values=var)
    return df.reindex(pd.date_range(df.index[0], df.index[-1])).reindex(columns=LONS)


def _harmonics(index):
    w = 2 * np.pi * index.dayofyear.values / 365.25
    return np.column_stack([np.ones(len(w))] + [f(k * w) for k in (1, 2, 3) for f in (np.cos, np.sin)])


def anomalies(name, refresh=False):
    """Departures from each mooring's 1991–2020 seasonal cycle, 5-day running means."""
    df = daily(name, refresh)
    out = {}
    for lon in df:
        s = df[lon]
        base = s.loc[f"{CLIM[0]}":f"{CLIM[1]}"].dropna()
        coef = np.linalg.lstsq(_harmonics(base.index), base.values, rcond=None)[0]
        out[lon] = s - _harmonics(s.index) @ coef
    return pd.DataFrame(out).rolling(5, center=True, min_periods=3).mean().interpolate(limit=INFILL_DAYS,
                                                                                       limit_area="inside")


def wave_signal(a):
    """Anomaly minus its centred 91-day running mean: the fast pulses without the slow build-up."""
    return a - a.rolling(91, center=True, min_periods=31).mean()


def rate_of_change(sig):
    """Centred rate of change per day of the signal: positive while a wave's front arrives, negative behind its peak."""
    return (sig.shift(-2) - sig.shift(2)) / 4.0


def infill_across(df):
    """Fill one missing mooring at a time from its neighbours, so the diagrams can be contoured."""
    return df.interpolate(method="index", axis=1, limit=1, limit_area="inside")
