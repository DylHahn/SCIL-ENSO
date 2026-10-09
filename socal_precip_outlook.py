"""SoCal 3 (precipitation only): NOAA seasonal precipitation outlook. Wrapper for socal_outlook.py --only prcp."""
import sys

import socal_outlook
from enso_common import FIG_DIR

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", str(FIG_DIR / "socal" / "socal_precip_outlook.png")]
    sys.argv.insert(1, "--only=prcp")
    socal_outlook.main()
