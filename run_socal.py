"""
Build the "Southern California" set for the website's second tab.

    python run_socal.py              # dark theme
    python run_socal.py --refresh    # re-download station records and NOAA's outlook

Writes figures_public/socal_current/: numbered PNGs, .alt.txt files and index.html.
"""
import argparse

from run_current import build_set
from run_story import HERE

OUT = HERE / "figures_public" / "socal_current"

# (script, takes --refresh, caption)
SOCAL = [
    ("socal6_warming.py", True,
     "Change in summer daytime highs and overnight lows since 1951–1980 across Southern California, and the "
     "regional summer temperature record since 1895 (NOAA nClimGrid)."),
    ("socal8_marine_heat.py", True,
     "Daily sea surface temperature and marine heatwave days in the Southern California Bight since 1982 "
     "(NOAA OISST), with 2026 compared with 1997 and 2015."),
    ("socal4_heatmap.py", True,
     "June–September 2026 daytime-high and overnight-low anomalies across Southern California (NOAA nClimGrid, "
     "~5 km), and the regional overnight-low anomaly for every summer since 1950."),
    ("socal2_heat.py", True,
     "Station counts of warm nights (≥ 65 °F) and hot days (≥ 90 °F) each summer since 1950 at Los Angeles, "
     "San Diego, the Inland Empire and Santa Barbara."),
]
# Archived (scripts kept, not published): socal1_rain.py (precipitation by ENSO phase),
# socal3_outlook.py (precipitation and temperature outlook maps), socal5_heat_fire_outlook.py
# (official fire-potential and temperature outlook maps).


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    build_set(SOCAL, OUT, "Southern California: heat and wildfire", args.theme, args.refresh)


if __name__ == "__main__":
    main()
