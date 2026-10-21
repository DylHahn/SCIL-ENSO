"""
Data for the interactive El Niño event explorer on the website (site/explorer.html).

Writes one JSON file with, for every El Niño since 1950 and for the current event, 24 monthly
values aligned on January of the onset year, for six measures:
  Niño 3.4, Niño 1+2, Niño 3 and Niño 4 SST anomalies (ERSST v5), the upper-200 m temperature
  anomaly along the equator, 180°–80°W (GODAS, 1980 onward), and NOAA's RONI (with the current
  official outlook median appended for the current event).
Anomalies are relative to the 1991–2020 monthly climatology.

    python interactive_data.py --out figures_public/el-nino/events.json
"""
import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np

from enso_common import FIG_DIR, event_label, find_events, load_cpc_outlook, load_roni
from enso_stats import load_gridded
from event_timeseries import N_MONTHS, NOW, aligned, box_series, godas_heat_series, onset_year

HIGHLIGHT = [2023, 2015, 1997, 1982]


def clean(values):
    return [None if not np.isfinite(v) else round(float(v), 2) for v in values]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", default="dark", help="ignored; accepted for update_site.py")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "interactive" / "events.json"))
    args = ap.parse_args()

    roni = load_roni(refresh=args.refresh)
    events = {onset_year(e): e for e in find_events(roni)}
    years = sorted(y for y in events if y < NOW)
    sst = load_gridded("sst", args.refresh)
    measures = [
        ("nino34", "Niño 3.4 SST", "Sea surface temperature anomaly, 5°S–5°N, 170°W–120°W (ERSST v5)",
         box_series(sst, (-5, 5), (190, 240))),
        ("nino12", "Niño 1+2 SST", "Sea surface temperature anomaly off Peru and Ecuador, 10°S–0°, 90°W–80°W "
         "(ERSST v5)", box_series(sst, (-10, 0), (270, 280))),
        ("nino3", "Niño 3 SST", "Sea surface temperature anomaly, 5°S–5°N, 150°W–90°W (ERSST v5)",
         box_series(sst, (-5, 5), (210, 270))),
        ("nino4", "Niño 4 SST", "Sea surface temperature anomaly, 5°S–5°N, 160°E–150°W (ERSST v5)",
         box_series(sst, (-5, 5), (160, 210))),
        ("upper", "Upper ocean 0–200 m", "Temperature anomaly averaged over the upper 200 m, 2°S–2°N, 180°–80°W "
         "(NCEP GODAS, 1980 onward)", godas_heat_series()),
        ("roni", "RONI", "NOAA Relative Oceanic Niño Index, 3-month means plotted on the middle month; the "
         "current event continues with NOAA's official outlook median (dashed)", roni),
    ]
    outlook = load_cpc_outlook(args.refresh)

    out = dict(updated=f"{dt.date.today():%B %-d, %Y}", now=NOW, n_months=N_MONTHS, highlight=HIGHLIGHT,
               measures=[], events=[])
    for y in years + [NOW]:
        ev = events.get(y)
        out["events"].append(dict(year=y, label=f"{y}/{y + 1}",
                                  peak=None if y == NOW else round(float(ev.max()), 2)))
    for key, name, desc, s in measures:
        series = {str(y): clean(aligned(s, y)) for y in years + [NOW]}
        series = {y: v for y, v in series.items() if any(x is not None for x in v[:12])}
        m = dict(key=key, name=name, description=desc, series=series)
        if key == "roni":
            idx = [(t.year - NOW) * 12 + t.month - 1 for t in outlook.index]
            m["forecast"] = [[i, round(float(v), 2)] for i, v in zip(idx, outlook["p50"]) if 0 <= i < N_MONTHS]
            m["forecast_issued"] = outlook.attrs["issued"]
        out["measures"].append(m)

    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(f"Saved {path} ({path.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
