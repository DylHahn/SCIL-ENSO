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
    ("anim1_sst.py", True,
     "Animated month-by-month sea surface temperature anomalies across the tropical Pacific, January to the latest "
     "month, for 2026 and the same months of 1997."),
    ("story1_super_el_nino.py", True,
     "Development of the 2026–27 event in NOAA's Relative Oceanic Niño Index alongside the four strongest El Niño "
     "events since 1950, with NOAA's official forecast."),
    ("eq4_event_timeseries.py", True,
     "Monthly anomaly time series for every El Niño since 1950, aligned by onset year: Niño 3.4 and Niño 1+2 sea "
     "surface temperature and equatorial upper-ocean temperature."),
    ("compare2_surface.py", True,
     "Tropical Pacific sea surface temperature anomalies in the same month of each very strong El Niño year, with "
     "Niño 3.4 and tropical-mean values."),
    ("compare1_underwater.py", True,
     "Equatorial subsurface temperature anomalies at the same stage of each event; the current event holds "
     "substantially more subsurface heat."),
    ("anim2_subsurface.py", False,
     "Animated equatorial depth–longitude sections, January to the latest month, showing subsurface warm "
     "anomalies moving east in 2026 and 1997."),
    ("stats4_event_ranking.py", True,
     "El Niño events since 1950 ranked by peak strength, duration and accumulated intensity, with the current event "
     "completed by NOAA's median forecast."),
    ("eq5_forecast_verification.py", True,
     "Each monthly NOAA strength forecast issued since April 2026 compared with the observed RONI, and how "
     "confidence in a very strong peak has evolved."),
    ("story4_global_heat.py", True,
     "Annual global mean surface temperature anomalies; recent record years have coincided with El Niño events."),
    ("eq1_sst_hovmoller.py", True,
     "Sea surface temperature anomalies along the equator, month by month (rows, top to bottom) and from the "
     "western Pacific to South America (left to right), for four very strong events."),
    ("eq2_heat_hovmoller.py", False,
     "The same layout for the average temperature of the upper 200 m; warm bands sloping down to the right are "
     "Kelvin waves carrying heat east beneath the surface."),
    ("eq3_nino_regions.py", True,
     "Location of the four Niño regions and their monthly anomalies, showing where along the equator the warming "
     "is concentrated."),
]


def build_set(series, out, page_title, theme="dark", refresh=False):
    """Run each script into `out` as NN_name.png (reading order), then write a preview index."""
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*"):          # rebuild from scratch so retired graphics don't linger
        old.unlink()
    failed, built = [], []
    for i, (script, refreshable, caption) in enumerate(series, 1):
        name = f"{i:02d}_{script}"
        cmd = [sys.executable, str(HERE / script), "--theme", theme,
               "--out", str(out / name.replace(".py", ".png"))]
        if refresh and refreshable:
            cmd.append("--refresh")
        print("\n>>", " ".join(cmd[1:]))
        if subprocess.call(cmd) != 0:
            failed.append(script)
        built.append((name, refreshable, caption))
    write_index(built, out, page_title, theme)
    print("\nDone." if not failed else f"\nFinished with errors in: {', '.join(failed)}")
    return failed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true", help="re-download NOAA data first")
    args = ap.parse_args()
    build_set(CURRENT, OUT, "2026 El Niño vs. the past", args.theme, args.refresh)


if __name__ == "__main__":
    main()
