"""
Stats 3 — "Where El Niño brings extra warmth (and cool)"

Average surface temperature (land and sea) during past moderate-or-stronger
El Niños since 1950, with the long-term warming trend removed so the map shows
El Niño's own fingerprint. Coloured only where at least 3 in 4 events agreed.
NOAAGlobalTemp, 5° grid.

    python stats3_temperature.py
"""
import argparse

from enso_common import FIG_DIR, apply_style
from enso_stats import (SEASONS, agreement, el_nino_years, load_gridded, map_figure, seasonal_anomalies,
                        season_years_text)

AGREE = 0.75


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", type=int, default=1950)
    ap.add_argument("--threshold", type=float, default=1.0, help="Dec–Feb RONI for an El Niño to count")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "stats" / "stats3_temperature.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    temp = load_gridded("temp", args.refresh).sel(time=slice(str(args.start), None))
    fields, titles, used = [], [], {}
    for season in SEASONS:
        anom, _ = seasonal_anomalies(temp, season)
        years = el_nino_years(season, args.threshold, args.refresh, anom["year"].values)
        ev = anom.sel(year=years)
        comp = ev.mean("year")
        fields.append(comp.where(agreement(ev, comp) >= AGREE))
        titles.append(season if season == "Dec–Feb" else "Jun–Aug (while El Niño builds)")
        used[season] = years

    n = len(used["Dec–Feb"])
    levels = [-1.5, -1.0, -0.5, -0.25, 0.25, 0.5, 1.0, 1.5]
    map_figure(
        fields, levels, "temp", titles,
        title="Where El Niño brings extra warmth, and where it brings cool",
        subtitle=f"Average of the {n} moderate-or-stronger El Niños since {args.start}, after removing the "
                 "long-term warming trend, so this is El Niño's own\nfingerprint. Coloured only where at "
                 "least 3 in 4 of those El Niños agreed. Climate change adds its warming on top of this.",
        source=f"Data: NOAAGlobalTemp v6 surface temperature (5° grid) vs. 1991–2020, trend removed. "
               f"El Niño winters: NOAA CPC RONI ≥ +{args.threshold:.1f}, {used['Dec–Feb'][0] - 1}–"
               f"{used['Dec–Feb'][-1]}.",
        out=args.out,
        alt=f"Two world maps of average temperature change during {n} past El Niños, warming trend removed "
            f"({season_years_text(used['Dec–Feb'], 'Dec–Feb')}). The eastern and central tropical Pacific "
            "is much warmer, along with much of the tropics; parts of the North and South Pacific are "
            "cooler.",
        cbar_label="Temperature vs. normal (°C)",
        cbar_ticklabels=[f"{v:+g}" for v in levels],
    )


if __name__ == "__main__":
    main()
