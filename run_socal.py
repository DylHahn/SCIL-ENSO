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
     "NOAA's official odds for rain and temperature this fall and winter, zoomed to Southern California."),
    ("socal1_rain.py", True,
     "What El Niño winters have meant for rain in Los Angeles, San Diego, the Inland Empire and Santa Barbara since 1950."),
    ("socal2_heat.py", True,
     "Warm nights and hot days every summer since 1950, with this summer highlighted."),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    build_set(SOCAL, OUT, "Southern California and El Niño", args.theme, args.refresh)


if __name__ == "__main__":
    main()
