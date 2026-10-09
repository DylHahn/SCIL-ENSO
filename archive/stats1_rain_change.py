"""
Stats 1 — "How El Niño has changed rainfall" (data, not a sketch)

Average rainfall during past moderate-or-stronger El Niños, as a percent more or
less than normal, for Dec–Feb and for the Jun–Aug while the event builds.
GPCP satellite + gauge rainfall since 1979. Method: see enso_stats.py.

    python stats1_rain_change.py
    python stats1_rain_change.py --threshold 1.5      # strong El Niños only
"""
import argparse

import numpy as np

from enso_common import FIG_DIR, apply_style
from enso_stats import SEASONS, agreement, el_nino_years, load_gridded, map_figure, seasonal_anomalies, season_years_text

DRY_MASK = 0.5   # mm/day: deserts, where a percent change means little
AGREE = 0.75     # colour only where at least 3 in 4 El Niños changed rainfall the same way


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threshold", type=float, default=1.0, help="Dec–Feb RONI for an El Niño to count")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "stats" / "stats1_rain_change.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    rain = load_gridded("rain", args.refresh)
    fields, titles, used = [], [], {}
    for season in SEASONS:
        anom, normal = seasonal_anomalies(rain, season)
        years = el_nino_years(season, args.threshold, args.refresh, anom["year"].values)
        ev = anom.sel(year=years)
        comp = ev.mean("year")
        pct = 100 * comp / normal
        fields.append(pct.where((normal >= DRY_MASK) & (agreement(ev, comp) >= AGREE)))
        titles.append(season if season == "Dec–Feb" else "Jun–Aug (while El Niño builds)")
        used[season] = years

    n = len(used["Dec–Feb"])
    levels = [-60, -40, -20, -10, 10, 20, 40, 60]
    map_figure(
        fields, levels, "rain", titles,
        title="How El Niño has changed rainfall around the world",
        subtitle=f"Average of the {n} moderate-or-stronger El Niños since 1979, compared with normal. "
                 "Brown = drier, green = wetter.\nColoured only where at least 3 in 4 of those El Niños changed "
                 "rainfall the same way. Measured data, not a forecast.",
        source=f"Data: GPCP v2.3 rainfall (NOAA PSL) vs. 1991–2020, long-term trend removed. El Niño winters: "
               f"NOAA CPC RONI ≥ +{args.threshold:.1f}, {used['Dec–Feb'][0] - 1}–{used['Dec–Feb'][-1]}. "
               "Deserts left blank.",
        out=args.out,
        alt=f"Two world maps of the average rainfall change during {n} past El Niños "
            f"({season_years_text(used['Dec–Feb'], 'Dec–Feb')}). In Dec–Feb it was much "
            "wetter in the central and eastern equatorial Pacific, Peru and Ecuador, and the southern US, "
            "and drier over Indonesia, northern Australia, southern Africa and northern South America. "
            "In Jun–Aug it was drier over Indonesia, India and Central America.",
        cbar_label="Rainfall vs. normal (%)",
        cbar_ticklabels=[f"{v:+d}%" for v in levels],
    )


if __name__ == "__main__":
    main()
