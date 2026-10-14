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

PAST = [2015, 1997, 1982]
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
    future = out[out.index > load_roni().index[-1]]          # seasons after the latest observation, as in the figure
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


# ---------------------------------------------------------------------------------------------
# "Why this El Niño is different": the current event against every El Niño since 1950 at the
# same stage, using the same series as the time-series animation and the interactive explorer
# ---------------------------------------------------------------------------------------------
REGIONS = {"Niño 4": ((-5, 5), (160, 210)), "Niño 3.4": ((-5, 5), (190, 240)), "Niño 3": ((-5, 5), (210, 270)),
           "Niño 1+2": ((-10, 0), (270, 280))}


def _same_stage(series, years, now):
    """(month index of the latest current value, current value, {year: value at that stage})."""
    from event_timeseries import aligned
    cur = aligned(series, now)
    k = int(np.flatnonzero(np.isfinite(cur))[-1])
    past = {y: aligned(series, y)[k] for y in years}
    return k, float(cur[k]), {y: float(v) for y, v in past.items() if np.isfinite(v)}


def _lbl(y):
    return f"{y}–{str(y + 1)[-2:]}"


def differences():
    """[(headline, explanation), ...] — only statements that the current data support."""
    from enso_stats import load_gridded
    from event_timeseries import NOW, box_series, godas_heat_series, onset_year
    years = sorted({onset_year(e) for e in find_events(load_roni())} - {NOW})
    sst = load_gridded("sst")
    box = {r: box_series(sst, *v) for r, v in REGIONS.items()}
    out = []
    month = lambda k: pd.Timestamp(NOW + k // 12, k % 12 + 1, 1).strftime("%B")

    k, v, past = _same_stage(box["Niño 3.4"], years, NOW)
    best = max(past, key=past.get)
    if v > past[best]:
        out.append(("Warmest El Niño on record at this stage",
                    f"In {month(k)}, the Niño 3.4 anomaly was {v:+.1f} °C, against a previous high of "
                    f"{past[best]:+.1f} °C ({_lbl(best)}) among the {len(past)} El Niño events since 1950 at the same "
                    "point in the year."))

    from event_timeseries import aligned
    rise = {y: aligned(box["Niño 3.4"], y)[k] - aligned(box["Niño 3.4"], y)[0] for y in years}
    rise = {y: r for y, r in rise.items() if np.isfinite(r)}
    r_now = aligned(box["Niño 3.4"], NOW)[k] - aligned(box["Niño 3.4"], NOW)[0]
    fastest = max(rise, key=rise.get)
    if r_now > rise[fastest]:
        out.append(("Fastest development since 1950",
                    f"Niño 3.4 has warmed by {r_now:.1f} °C since January, more than any previous El Niño over the "
                    f"same months (previous largest: {rise[fastest]:.1f} °C in {_lbl(fastest)})."))

    top = []
    for r, s in box.items():
        _, v_r, past_r = _same_stage(s, years, NOW)
        b = max(past_r, key=past_r.get)
        top.append((r, v_r, b, past_r[b], v_r > past_r[b]))
    record = [t for t in top if t[4]]
    if len(record) >= 3:
        parts = [f"{r} {v_r:+.1f} °C ({pv:+.1f} °C)" for r, v_r, b, pv, _ in record]
        out.append(("Record warmth across the whole equatorial Pacific",
                    f"At their peaks, past very strong events were strongest either near South America (1982, 1997) "
                    f"or farther west (2015). In {month(k)}, the current event is the warmest on record at this stage "
                    f"in {'all four' if len(record) == 4 else f'{len(record)} of the four'} Niño regions (previous high in "
                    "brackets): " + ", ".join(parts) + "."))

    try:
        k_u, v_u, past_u = _same_stage(godas_heat_series(), years, NOW)
        b = max(past_u, key=past_u.get)
        if v_u > past_u[b]:
            out.append(("Far more heat below the surface",
                        f"In {month(k_u)}, the upper 200 m of the equatorial Pacific (180°–80°W) was {v_u:+.1f} °C "
                        f"above normal, against a previous high of {past_u[b]:+.1f} °C ({_lbl(b)}) among the "
                        f"{len(past_u)} El Niño events since 1980. This reservoir of heat can sustain surface warming "
                        "over the coming months."))
    except Exception as exc:                      # GODAS depth files are local only
        print(f"Subsurface difference skipped: {exc}")

    out_fc = load_cpc_outlook()
    rec = max(find_events(load_roni()), key=lambda e: e.max())
    peak = out_fc[out_fc.index > load_roni().index[-1]]["p50"].max()
    if peak > rec.max():
        out.append(("Forecast to set a new record",
                    f"NOAA's {out_fc.attrs['issued']} outlook places the median peak at {peak:+.1f} °C on the RONI "
                    f"scale, above the record of {rec.max():+.1f} °C set in {event_label(rec)}."))
    return out


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
    print("Why this El Niño is different:")
    for head, text in differences():
        print(f"  {head}: {text}")
