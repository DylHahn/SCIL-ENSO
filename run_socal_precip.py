"""
Build the "Southern California Precipitation" set for the website's third tab.

    python run_socal_precip.py              # dark theme
    python run_socal_precip.py --refresh    # re-download outlook, station and gridded data

Writes figures_public/socal_precip_current/: numbered PNGs, .alt.txt files and index.html.
"""
import argparse

from run_current import build_set
from run_story import HERE

OUT = HERE / "figures_public" / "socal_precip_current"

# (script, takes --refresh, caption)
SOCAL_PRECIP = [
    ("socal3_outlook_prcp.py", True,
     "NOAA Climate Prediction Center probability of above-, near- or below-normal precipitation for Southern "
     "California, with season-by-season values for Los Angeles."),
    ("socal7_precip_composite.py", True,
     "November–March precipitation across Southern California during the strong El Niño winters since 1951 "
     "(NOAA nClimGrid, ~5 km), and the regional total for every winter."),
    ("socal1_rain.py", True,
     "Water-year precipitation by ENSO phase at Los Angeles, San Diego, Lake Elsinore and Santa Barbara, "
     "1951 to present."),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    build_set(SOCAL_PRECIP, OUT, "Southern California Precipitation", args.theme, args.refresh)


if __name__ == "__main__":
    main()
