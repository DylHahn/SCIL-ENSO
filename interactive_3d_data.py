"""
Data for the interactive 3D view of the tropical Pacific on the website (site/ocean3d.html), and
shared loading for the rotating 3D animation (anim_3d.py).

For 2026/2027, the past very strong El Niños (2015/2016, 1997/1998, 1982/1983) and the 1991–2020
normal, monthly from January of each event's first year to December of the next (the current event to
the latest GODAS month):
near-surface (5 m) temperature over 20°S–20°N, 130°E–80°W and the depth of the 20 °C isotherm
beneath it (the base of the warm upper layer), at 1° latitude × 2° longitude.
All values come from NCEP GODAS (public NOAA data).

    python interactive_3d_data.py --out figures_public/el-nino/ocean3d.json
"""
import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

from anim_warm_water import d20, load_temps, monthly_normal
from enso_common import FIG_DIR

NOW = 2026
COMPARE = [2015, 1997, 1982]
LAT_STEP, LON_STEP = 3, 2          # GODAS is 1/3° in latitude and 1° in longitude
EQ = (-2, 2)
LON_MIN = 130
ISOTHERMS = [20, 24, 26, 28, 29]


def for_display(stack, coast=2, sigma=1.0):
    """(time, lat, lon) fields cleaned for 3D display: cells within `coast` grid cells of land are
    dropped (GODAS is unreliable against coastlines and they produce spikes in 3D), then a light
    NaN-aware Gaussian smoothing removes grid-scale noise."""
    from scipy.ndimage import binary_dilation, gaussian_filter
    land = ~np.isfinite(stack[0])
    near = binary_dilation(land, iterations=coast)
    out = np.empty_like(stack, dtype=float)
    for t, a in enumerate(stack):
        w = np.where(near, 0.0, 1.0)
        num = gaussian_filter(np.where(near, 0.0, a), sigma)
        den = gaussian_filter(w, sigma)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[t] = np.where(near, np.nan, num / den)
    return out


def cases(refresh=False):
    """[(name, temps[time, depth, lat, lon])...] plus months, lat, lon, depths and calendar offsets."""
    from enso_anim import EVENT_MONTHS, event_months, event_name
    temps, months, lat, lon, depths = load_temps(event_months(NOW), refresh)
    offsets = [(m.year - 2000, m.month) for m in event_months(2000)]          # all 24 months of an event
    out = [(event_name(NOW), temps)]                                          # in progress: fewer months
    for y in COMPARE:
        t, got, _, _, _ = load_temps(event_months(y))
        assert len(got) == EVENT_MONTHS, f"GODAS months missing for {y}"
        out.append((event_name(y), t))
    out.append(("Normal", monthly_normal([m.month for m in event_months(2000)])))
    return out, months, offsets, lat, lon, depths


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", default="dark", help="ignored; accepted for update_site.py")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "interactive" / "ocean3d.json"))
    args = ap.parse_args()

    data, months, offsets, lat, lon, depths = cases(args.refresh)
    normal = data[-1][1]
    eq = (lat >= EQ[0]) & (lat <= EQ[1])
    li = slice(None, None, LAT_STEP)
    lo = np.flatnonzero(lon >= LON_MIN)[::LON_STEP]           # start east of the Maritime Continent
    to_int = lambda a, k: np.where(np.isfinite(a), np.round(a * k), -9999).astype(int).tolist()

    out = dict(updated=f"{dt.date.today():%B %-d, %Y}", now=NOW,
               months=[[dy, mo] for dy, mo in offsets],          # [year offset from onset year, calendar month]
               lat=np.round(lat[li], 2).tolist(), lon=np.round(lon[lo], 1).tolist(),
               cases=[], scale=dict(sst=10, depth=1), isotherms=ISOTHERMS, missing=-9999)
    from anim_warm_layers import volumes
    for name, temps in data:
        sst = for_display(temps[:, 0])[:, li, lo]                        # 5 m temperature, °C
        case = dict(name=name, sst=to_int(sst, 10))
        for th in ISOTHERMS:                                             # depth of each isotherm, m
            case[f"d{th}"] = to_int(for_display(d20(temps, depths, th))[:, li, lo], 1)
        v = volumes(temps, lat, lon, depths)                             # (time, layer) over 5°S–5°N
        case["v28"] = np.round(v[:, 3:].sum(axis=1), 1).tolist()
        case["v29"] = np.round(v[:, 4], 1).tolist()
        out["cases"].append(case)

    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, separators=(",", ":")))
    print(f"Saved {path} ({path.stat().st_size / 1e6:.1f} MB; current event {months[0]:%b %Y}–{months[-1]:%b %Y})")


if __name__ == "__main__":
    main()
