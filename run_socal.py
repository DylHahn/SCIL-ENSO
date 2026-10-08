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
    ("socal3_outlook.py", True,
     "NOAA Climate Prediction Center probabilities for seasonal precipitation and temperature in Southern "
     "California, with season-by-season values for Los Angeles."),
    ("socal1_rain.py", True,
     "Water-year precipitation by ENSO phase at Los Angeles, San Diego, Lake Elsinore and Santa Barbara, "
     "1951 to present."),
    ("socal2_heat.py", True,
     "June–September counts of warm nights (≥ 65 °F) and hot days (≥ 90 °F) at four stations, 1950 to present."),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    build_set(SOCAL, OUT, "Southern California and El Niño", args.theme, args.refresh)


if __name__ == "__main__":
    main()
