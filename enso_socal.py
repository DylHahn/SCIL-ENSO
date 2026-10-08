"""
Southern California helpers: NOAA GHCN-Daily station records and El Niño categories.

Stations (long, near-complete records through the present):
  * Los Angeles Downtown/USC   USW00093134   (1906–)
  * San Diego Intl Airport     USW00023188   (1939–)
  * March Air Reserve Base     USW00023119   (1949–)  Inland Empire heat (gap 1971–2011)
  * Lake Elsinore              USC00042805   (1897–)  Inland Empire rain
  * Santa Barbara              USC00047902   (1893–)

Rainy season = water year, 1 Oct to 30 Sep, labelled by the year it ends
(the 2026–27 season is "2027"), as NWS Los Angeles and San Diego report it.
Its El Niño category comes from NOAA's Dec–Feb RONI inside that season.
"""

from __future__ import annotations

import urllib.request

import numpy as np
import pandas as pd

from enso_common import COLORS, HERE, load_roni

GHCN_DIR = HERE / "data" / "ghcn"
GHCN_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/{id}.csv.gz"

STATIONS = {
    "Los Angeles": "USW00093134",
    "San Diego": "USW00023188",
    "Inland Empire": "USW00023119",
    "Santa Barbara": "USC00047902",
}
STATION_NOTES = {
    "Los Angeles": "Downtown/USC",
    "San Diego": "Lindbergh Field",
    "Inland Empire": "March Air Reserve Base, near Riverside",
    "Santa Barbara": "downtown",
}
# Rain uses Lake Elsinore inland: March ARB's record has a 1971–2011 gap, while
# Elsinore's rain record is nearly complete. (Heat keeps March ARB: it is the only
# inland station with a complete 2026 summer so far.)
RAIN_STATIONS = dict(STATIONS, **{"Inland Empire": "USC00042805"})
RAIN_NOTES = dict(STATION_NOTES, **{"Inland Empire": "Lake Elsinore"})

# El Niño categories by Dec–Feb RONI (°C); order = display order
CATEGORIES = [
    ("La Niña", -np.inf, -0.5),
    ("Neutral", -0.5, 0.5),
    ("Weak–moderate\nEl Niño", 0.5, 1.5),
    ("Strong El Niño", 1.5, np.inf),
]


def category_colors():
    return {"La Niña": COLORS["la_nina"], "Neutral": COLORS["neutral"],
            "Weak–moderate\nEl Niño": COLORS["el_nino_soft"],
            "Strong El Niño": COLORS["el_nino"]}


def categorize(v):
    if v is None or not np.isfinite(v):
        return None
    for name, lo, hi in CATEGORIES:
        if lo <= v < hi:
            return name
    return None


def load_station(station_id, refresh=False) -> pd.DataFrame:
    """Daily PRCP (mm), TMAX and TMIN (°C) with failed-quality-check values removed."""
    path = GHCN_DIR / f"{station_id}.csv.gz"
    if refresh or not path.exists():
        GHCN_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {GHCN_URL.format(id=station_id)} ...")
        urllib.request.urlretrieve(GHCN_URL.format(id=station_id), path)
    d = pd.read_csv(path, header=None, usecols=[1, 2, 3, 5], names=["date", "el", "v", "q"],
                    dtype={"date": str}, low_memory=False)
    d = d[d["el"].isin(["PRCP", "TMAX", "TMIN"]) & d["q"].isna()]
    d["date"] = pd.to_datetime(d["date"])
    return d.pivot_table(index="date", columns="el", values="v") / 10.0   # tenths -> mm / °C


def water_year_totals(daily, min_wet_days=145):
    """Rain per water year (mm). A season counts only if Nov–Mar (151 days) is nearly
    complete: summer gaps hide little rain, winter gaps would."""
    pr = daily["PRCP"]
    wy = pr.index.year + (pr.index.month >= 10)
    total = pr.groupby(wy).sum()
    wet = pr[pr.index.month.isin([11, 12, 1, 2, 3])]
    wet_count = wet.groupby(wet.index.year + (wet.index.month >= 10)).count()
    ok = wet_count.reindex(total.index).fillna(0) >= min_wet_days
    return total[ok]


def season_so_far(daily, season_end_year):
    """Rain so far in the season ending `season_end_year`, and the last date with data."""
    pr = daily["PRCP"].loc[f"{season_end_year - 1}-10-01":f"{season_end_year}-09-30"]
    return float(pr.sum()), (pr.index.max() if len(pr) else None)


def winter_roni(refresh=False):
    """{season end year: Dec–Feb RONI}, from NOAA's RONI (stored on January)."""
    roni = load_roni(refresh=refresh)
    return {t.year: v for t, v in roni.items() if t.month == 1}
