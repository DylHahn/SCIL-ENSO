"""
Build the curated "2026 El Niño vs. the past" set for icharm.sdsu.edu.

Only graphics that use datasets iCHARM hosts (NOAA surface temperature, GODAS,
GPCP rainfall) or NOAA's official El Niño index, and that show how this El Niño
compares with past ones. Everything is real observations or NOAA forecasts.

    python run_current.py              # dark theme
    python run_current.py --refresh    # after NOAA's monthly updates

Writes figures_public/current/: numbered PNGs in reading order, a .alt.txt for
each, and index.html (captioned preview for the web team).
"""
import argparse
import subprocess
import sys

from run_story import HERE, write_index

OUT = HERE / "figures_public" / "current"

# (script, takes --refresh, caption)
CURRENT = [
    ("story1_super_el_nino.py", True,
     "How this El Niño has grown month by month compared with the four biggest since 1950, plus NOAA's forecast."),
    ("compare2_surface.py", True,
     "The tropical Pacific's surface this August vs. the same month of past super El Niños."),
    ("compare1_underwater.py", True,
     "Below the surface, this El Niño is carrying far more extra heat than past giants did at the same point."),
    ("fig6_equatorial_cross_section.py", False,
     "This year's warm water building and sliding east beneath the surface, two months at a time."),
    ("stats4_event_ranking.py", True,
     "Every big El Niño since 1950 ranked by peak, length and total warmth, with this one finished by NOAA's forecast."),
    ("story4_global_heat.py", True,
     "Big El Niños push the whole planet to new heat records, and this year is already running near record warm."),
    ("stats1_rain_change.py", True,
     "What past El Niños did to rainfall around the world (measured data, not a forecast)."),
    ("stats2_rain_odds.py", False,
     "How often past El Niños brought a drier or wetter season, place by place."),
    ("stats3_temperature.py", True,
     "Where El Niño has brought extra warmth or cool, with the long-term warming trend removed."),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true", help="re-download NOAA data first")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*"):          # rebuild from scratch so retired graphics don't linger
        old.unlink()
    failed, series = [], []
    for i, (script, refreshable, caption) in enumerate(CURRENT, 1):
        name = f"{i:02d}_{script}"
        out = OUT / name.replace(".py", ".png")
        cmd = [sys.executable, str(HERE / script), "--theme", args.theme, "--out", str(out)]
        if args.refresh and refreshable:
            cmd.append("--refresh")
        print("\n>>", " ".join(cmd[1:]))
        if subprocess.call(cmd) != 0:
            failed.append(script)
        series.append((name, refreshable, caption))
    write_index(series, OUT, "2026 El Niño vs. the past", args.theme)
    print("\nDone." if not failed else f"\nFinished with errors in: {', '.join(failed)}")


if __name__ == "__main__":
    main()
