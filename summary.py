"""
"What's happening now": the short summary at the top of the El Niño page, computed from the
latest data each time the site is built so the text never goes stale.

Each item is computed independently; if one data source is unavailable, that item is left out
and the rest still appear.

    python summary.py            # print the current summary
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from enso_common import (GODAS_DIR, event_label, find_events, godas_equatorial_section, join_and,
                         load_cpc_outlook, load_cpc_strengths, load_nino_regions, load_roni, season_label,
                         season_words)

PAST = [1982, 1997, 2015]
STRENGTH = [(2.0, "very strong"), (1.5, "strong"), (1.0, "moderate"), (0.5, "weak")]


def _strength(v):
    return next((name for lim, name in STRENGTH if v >= lim), "neutral")


def current_state():
    roni = load_roni()
    t, v = roni.index[-1], roni.iloc[-1]
    n34 = load_nino_regions()["Niño 3.4"]
    m = n34.index[-1]
    return ("Current strength",
            f"NOAA's Relative Oceanic Niño Index reached {v:+.1f} °C for {season_words(roni.attrs['season'][t])} "
            f"{t.year}, a {_strength(v)} El Niño. The monthly Niño 3.4 anomaly was {n34.iloc[-1]:+.1f} °C in "
            f"{m:%B}.")


def versus_past():
    df = load_nino_regions()
    m = df.index[-1]
    now = df.loc[m]
    same = {y: df.loc[pd.Timestamp(y, m.month, 1)] for y in PAST}
    ahead = [r for r in ("Niño 3.4", "Niño 1+2") if all(now[r] > same[y][r] for y in PAST)]
    best = {r: max(PAST, key=lambda y: same[y][r]) for r in ("Niño 3.4", "Niño 1+2")}
    if not ahead:
        return None
    parts = [f"{r} ({now[r]:+.1f} °C, against {same[best[r]][r]:+.1f} °C in {best[r]})" for r in ahead]
    return ("Compared with past events",
            f"In {m:%B}, {join_and(parts)} {'is' if len(parts) == 1 else 'are'} warmer than in "
            f"{join_and(str(y) for y in PAST)} at the same point in the year.")


def subsurface():
    import xarray as xr
    from enso_common import download_godas_year
    year = pd.Timestamp.today().year
    with xr.open_dataset(download_godas_year(year)) as ds:
        last = pd.Timestamp(ds["time"].values[-1])
    dates = [last.strftime("%Y-%m-%d")] + [f"{y}-{last.month:02d}-01" for y in PAST]
    _, lons, anoms, _ = godas_equatorial_section(GODAS_DIR, dates)
    east = (lons >= 180) & (lons <= 280)
    vals = [float(np.nanmean(a[:, east])) for a in anoms]
    best = max(range(len(PAST)), key=lambda k: vals[k + 1])
    return ("Below the surface",
            f"In {last:%B}, the upper 200 m of the central and eastern equatorial Pacific was {vals[0]:+.1f} °C above "
            f"normal, compared with at most {vals[best + 1]:+.1f} °C ({PAST[best]}) in past very strong events at the "
            "same stage.")


def forecast():
    out = load_cpc_outlook()
    st = load_cpc_strengths()
    issued = pd.Timestamp(out.attrs["issued"])
    future = out[out.index - pd.DateOffset(months=1) > issued]
    peak_t = future["p50"].idxmax()
    vs = st["en_vstrong"].astype(float)
    record = max(find_events(load_roni()), key=lambda e: e.max())
    text = (f"NOAA's {out.attrs['issued']} outlook gives a {vs.max():.0f}% probability of a very strong event "
            f"(≥ +2.0 °C), with a median forecast peak of {future['p50'].max():+.1f} °C in {season_label(peak_t)}")
    if future["p50"].max() > record.max():
        text += f", above the 1950–present record of {record.max():+.1f} °C ({event_label(record)})"
    return ("Forecast", text + ".")


def southern_california():
    from enso_marine import anomalies_and_mhw, bight_sst
    from socal_outlook import CITIES, load_leads, odds_at, phrase
    parts = []
    sst = bight_sst()
    _, mhw = anomalies_and_mhw(sst)
    last = sst.index.max()
    days = int(mhw.loc[str(last.year)].sum())
    prev = {y: int(mhw.loc[f"{y}-01-01":f"{y}-{last:%m-%d}"].sum()) for y in range(1982, last.year)}
    record = days > max(prev.values())
    parts.append(f"Coastal waters have recorded {days} marine heatwave days in {last.year} through {last:%-d %B}"
                 + (", the most on record for the date" if record else ""))
    leads = load_leads("prcp", False)
    djf = next((v for v in leads.values() if v[0] == "DJF"), None)
    if djf:
        cat, prob = odds_at(djf[3], *CITIES["Los Angeles"])
        if cat != "EC":
            odds = phrase("prcp", cat, prob)                      # e.g. "50–60% chance wetter"
            pct, word = odds.split(" chance ")
            parts.append(f"NOAA's outlook gives Los Angeles a {pct} chance of a {word}-than-normal "
                         "December–February")
    return ("Southern California", ". ".join(parts) + ".")


ITEMS = [current_state, versus_past, subsurface, forecast, southern_california]


def current_summary():
    """[(label, sentence), ...]; items whose data cannot be loaded are skipped with a warning."""
    out = []
    for fn in ITEMS:
        try:
            item = fn()
            if item:
                out.append(item)
        except Exception as exc:          # one missing source should not break the site build
            print(f"Summary item '{fn.__name__}' skipped: {exc}")
    return out


if __name__ == "__main__":
    for label, text in current_summary():
        print(f"{label}: {text}\n")
