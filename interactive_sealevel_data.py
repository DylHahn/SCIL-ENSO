"""
Data for the interactive 3D sea level view on the website (site/sealevel3d.html).

Daily satellite sea level anomaly over 12°S–12°N, 145°E–82°W at 1° (NOAA blended altimetry via
CoastWatch ERDDAP), every second day from July of the year before onset to the latest day, as
  * total: anomaly relative to the 2017–2024 seasonal cycle, 5-day running mean;
  * wave: the total minus its 91-day running mean at each point, which removes the slow build-up
    and leaves Kelvin waves and other fast changes.
Both are lightly smoothed in space for display, and stored in units of 0.5 cm.

    python interactive_sealevel_data.py --out figures_public/ocean/sealevel3d.json
"""
import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

from enso_common import FIG_DIR
from enso_sealevel import band_anomalies, daily_band
from interactive_3d_data import for_display

NOW = 2026
LAT, LON = (-12, 12), (145, 278)
EVERY = 2                                         # days between frames
SCALE = 2                                         # stored value = cm × SCALE


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", default="dark", help="ignored; accepted for update_site.py")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "interactive" / "sealevel3d.json"))
    args = ap.parse_args()

    anom = band_anomalies(daily_band(f"{NOW - 1}-07-01", refresh=args.refresh))
    anom = anom.sel(latitude=slice(*LAT), longitude=slice(*LON)).dropna("time", how="all")
    wave = anom - anom.rolling(time=91, center=True, min_periods=30).mean()
    pick = np.arange(0, anom.sizes["time"], EVERY)
    if pick[-1] != anom.sizes["time"] - 1:
        pick = np.append(pick, anom.sizes["time"] - 1)
    times = pd.to_datetime(anom["time"].values[pick])
    to_int = lambda a: np.where(np.isfinite(a), np.round(a * SCALE), -9999).astype(int).tolist()
    total = for_display(anom.values[pick], coast=1, sigma=1.2)
    waves = for_display(wave.values[pick], coast=1, sigma=1.2)

    out = dict(updated=f"{dt.date.today():%B %-d, %Y}", dates=[f"{t:%Y-%m-%d}" for t in times],
               lat=np.round(anom["latitude"].values, 3).tolist(), lon=np.round(anom["longitude"].values, 3).tolist(),
               scale=SCALE, missing=-9999, total=to_int(total), wave=to_int(waves))
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, separators=(",", ":")))
    print(f"Saved {path} ({path.stat().st_size / 1e6:.1f} MB, {len(times)} days, {times[0]:%d %b %Y}–{times[-1]:%d %b %Y})")


if __name__ == "__main__":
    main()
