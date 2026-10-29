"""
Daily coastal sea level from tide gauges along the Pacific coast of the Americas, from Peru to
Washington: the University of Hawaii Sea Level Center (UHSLC) fast-delivery daily data (quality
controlled, about two months behind real time), via the UHSLC ERDDAP server.

A Kelvin wave that reaches South America splits: part travels north and south along the coast as
a coastal-trapped wave, raising coastal sea level as it passes. Anomalies are each station's
departure from its 1991–2020 mean seasonal cycle (stations without that period use their whole
record), smoothed with a 10-day running mean; they are not corrected for air pressure.
Records are cached in data/tide_gauges/.
"""
import io
import subprocess

import numpy as np
import pandas as pd

from enso_common import HERE

CACHE = HERE / "data" / "tide_gauges"
URL = "https://uhslc.soest.hawaii.edu/erddap/tabledap/global_daily_fast.csv?time,sea_level&uhslc_id={id}"
# south to north along the coast: UHSLC id, name, latitude, longitude (°E)
STATIONS = [
    (92, "Talara, Peru", -4.57, -81.28),
    (91, "La Libertad, Ecuador", -2.22, -80.91),
    (302, "Balboa, Panama", 8.97, -79.57),
    (87, "Quepos, Costa Rica", 9.43, -84.17),
    (82, "Acajutla, El Salvador", 13.57, -89.84),
    (316, "Acapulco, Mexico", 16.84, -99.85),
    (395, "Manzanillo, Mexico", 19.06, -104.30),
    (34, "Cabo San Lucas, Mexico", 22.88, -109.91),
    (317, "Ensenada, Mexico", 31.85, -116.63),
    (569, "San Diego, California", 32.71, -117.17),
    (551, "San Francisco, California", 37.81, -122.47),
    (556, "Crescent City, California", 41.75, -124.18),
    (592, "South Beach, Oregon", 44.63, -124.04),
    (558, "Neah Bay, Washington", 48.37, -124.62),
]
CLIM = (1991, 2020)
# periods excluded: Acajutla's level drops by about 18 cm from 2024 and stays there, a change of
# instrument or datum rather than of the ocean
EXCLUDE = {82: ("2024-01-01", None)}


def alongshore_km():
    """Approximate distance along the coast from La Libertad, Ecuador (km), for each station: great-
    circle legs between consecutive stations (an underestimate of the true coastline)."""
    lat = np.deg2rad([s[2] for s in STATIONS])
    lon = np.deg2rad([s[3] for s in STATIONS])
    d = 6371 * 2 * np.arcsin(np.sqrt(np.sin(np.diff(lat) / 2) ** 2
                                     + np.cos(lat[:-1]) * np.cos(lat[1:]) * np.sin(np.diff(lon) / 2) ** 2))
    km = np.concatenate([[0], np.cumsum(d)])
    return km - km[1]                                       # zero at La Libertad


def station_series(uid, refresh=False):
    """Daily sea level (cm) for one station."""
    path = CACHE / f"d{uid}.csv"
    if refresh or not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".part")
        subprocess.run(["curl", "-sS", "-f", "--retry", "4", "-m", "300", "-o", str(tmp), URL.format(id=uid)],
                       check=True)
        tmp.replace(path)
    df = pd.read_csv(path, skiprows=[1], parse_dates=["time"])
    s = df.set_index("time")["sea_level"].astype(float) / 10.0       # mm → cm
    s.index = s.index.tz_localize(None).normalize()
    s = s[~s.index.duplicated()].sort_index()
    if uid in EXCLUDE:
        s.loc[EXCLUDE[uid][0]:EXCLUDE[uid][1]] = np.nan
    return s


def anomalies(refresh=False, smooth=10):
    """DataFrame (date × station name) of smoothed daily anomalies (cm), and the set of stations whose
    baseline is their whole record rather than 1991–2020."""
    cols, short = {}, set()
    for uid, name, _, _ in STATIONS:
        s = station_series(uid, refresh)
        s = s.reindex(pd.date_range(s.index[0], s.index[-1]))
        doy = np.minimum(s.index.dayofyear, 365)
        base = s.loc[f"{CLIM[0]}":f"{CLIM[1]}"]
        if base.notna().sum() < 5 * 365:                     # too little of 1991–2020: use the whole record
            base, _ = s, short.add(name)
        bd = np.minimum(base.index.dayofyear, 365)
        clim = base.groupby(bd).mean()
        # smooth the daily climatology (31-day, periodic)
        c = clim.reindex(range(1, 366)).interpolate(limit_direction="both").values
        c = np.convolve(np.concatenate([c[-15:], c, c[:15]]), np.ones(31) / 31, mode="valid")
        a = s - c[doy - 1]
        cols[name] = a.rolling(smooth, center=True, min_periods=smooth // 2).mean()
    return pd.DataFrame(cols), short
