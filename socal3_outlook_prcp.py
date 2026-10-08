"""SoCal 3 (precipitation only): NOAA seasonal precipitation outlook. Wrapper for socal3_outlook.py --only prcp."""
import sys

import socal3_outlook
from enso_common import FIG_DIR

if __name__ == "__main__":
    if "--out" not in sys.argv:
        sys.argv += ["--out", str(FIG_DIR / "socal" / "socal3_outlook_prcp.png")]
    sys.argv.insert(1, "--only=prcp")
    socal3_outlook.main()
