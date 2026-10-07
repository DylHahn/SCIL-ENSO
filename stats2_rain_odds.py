"""
Stats 2 — "How often did El Niño bring drought or floods?"

For each place: out of the past moderate-or-stronger El Niños since 1979, how
many gave a wetter-than-normal season? Counting events is easier to grasp than an
average and shows how reliable the pattern is ("7 of 8 El Niños were dry here").

    python stats2_rain_odds.py
"""
import argparse

from enso_common import FIG_DIR, apply_style
from enso_stats import SEASONS, el_nino_years, load_gridded, map_figure, seasonal_anomalies, season_years_text

DRY_MASK = 0.5   # mm/day: skip deserts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threshold", type=float, default=1.0, help="Dec–Feb RONI for an El Niño to count")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "stats" / "stats2_rain_odds.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    rain = load_gridded("rain", args.refresh)
    fields, titles, used = [], [], {}
    for season in SEASONS:
        anom, normal = seasonal_anomalies(rain, season)
        years = el_nino_years(season, args.threshold, args.refresh, anom["year"].values)
        share_wetter = (anom.sel(year=years) > 0).mean("year")
        fields.append(share_wetter.where(normal >= DRY_MASK))
        titles.append(season if season == "Dec–Feb" else "Jun–Aug (while El Niño builds)")
        used[season] = years

    n = len(used["Dec–Feb"])
    # 5 bins on the share of El Niños that were wetter. With ~8 events, 3–5 wet ones is what
    # chance alone gives, so that middle bin is left clear; 6+ (or 2 or fewer) is a real tilt.
    eps = 1e-6
    levels = [0 - eps, 0.125 + eps, 0.25 + eps, 0.75 - eps, 0.875 - eps, 1 + eps]
    centres = [(a + b) / 2 for a, b in zip(levels[:-1], levels[1:])]
    labels = ["almost always\ndrier", "usually\ndrier", "", "usually\nwetter", "almost always\nwetter"]
    map_figure(
        fields, levels, "rain", titles,
        title="How often did El Niño bring a drier or wetter season?",
        subtitle=f"Out of the {n} moderate-or-stronger El Niños since 1979, how many brought more rain than "
                 "normal? “Almost always” = at least\n7 in 8 of them, “usually” = at least 3 in 4. "
                 "Uncoloured: about a coin flip, so El Niño doesn't tip the odds much there.",
        source=f"Data: GPCP v2.3 rainfall (NOAA PSL) vs. 1991–2020, long-term trend removed. El Niño winters: "
               f"NOAA CPC RONI ≥ +{args.threshold:.1f}, {used['Dec–Feb'][0] - 1}–{used['Dec–Feb'][-1]}. "
               "Deserts left blank.",
        out=args.out,
        alt=f"Two world maps counting how many of {n} past El Niños "
            f"({season_years_text(used['Dec–Feb'], 'Dec–Feb')}) brought a wetter-than-normal season. "
            "In Dec–Feb the central and eastern equatorial Pacific was wetter nearly every time, while "
            "Indonesia, northern Australia, southern Africa and northern South America were drier in most "
            "events. In Jun–Aug Indonesia and parts of Central America were drier in most events.",
        cbar_label=f"Out of {n} past El Niño seasons",
        cbar_ticks=centres,
        cbar_ticklabels=labels,
        extend="neither",
        middle_label="coin\nflip",
    )


if __name__ == "__main__":
    main()
