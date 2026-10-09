"""
Equatorial 1 — Sea surface temperature anomalies along the equator (Hovmöller)

Monthly SST anomalies averaged over 2°S–2°N from 130°E to 80°W, January of each
onset year to January of the following year, for 1982–83, 1997–98, 2015–16 and
the current event. Anomalies are relative to the 1991–2020 monthly climatology.
Source: NOAA ERSST v5 (as hosted on iCHARM).

    python hovmoller_sst.py
    python hovmoller_sst.py --refresh      # re-download ERSST (~160 MB)
"""
import argparse

import numpy as np
import pandas as pd

from enso_common import FIG_DIR, apply_style, join_and
from enso_equatorial import EVENTS, LON_RANGE, event_months, hovmoller_figure
from enso_stats import load_gridded

LAT_BAND = (-2.1, 2.1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", type=int, nargs="+", default=EVENTS)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "equatorial" / "hovmoller_sst.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    sst = load_gridded("sst", args.refresh).sel(lat=slice(*LAT_BAND), lon=slice(LON_RANGE[0] - 2, LON_RANGE[1] + 2))
    band = sst.weighted(np.cos(np.deg2rad(sst["lat"]))).mean("lat")
    clim = band.sel(time=slice("1991", "2020")).groupby("time.month").mean("time")
    anom = (band.groupby("time.month") - clim).load()
    have = pd.to_datetime(anom["time"].values)

    fields, peaks = {}, {}
    for y in args.years:
        months = [m for m in event_months(y) if m in have]
        vals = anom.sel(time=months).values
        fields[y] = (months, anom["lon"].values, band.sel(time=months).values)   # colours: actual SST
        east = anom["lon"].values >= 210
        peaks[y] = (months[-1], float(np.nanmax(vals[-1][east])))
    now = args.years[-1]
    last = fields[now][0][-1]
    same = {y: float(np.nanmax(anom.sel(time=f"{y}-{last.month:02d}-01").values[anom['lon'].values >= 210]))
            for y in args.years[:-1]}

    levels = np.arange(20, 31.01, 0.5)
    hovmoller_figure(
        fields, levels, "turbo", "Sea surface temperature (°C), 2°S–2°N",
        title="Equatorial Pacific sea surface temperature during major El Niño events",
        subtitle=f"Monthly sea surface temperature along the equator (2°S–2°N). By {last:%B} {now}, the maximum anomaly in "
                 f"the eastern Pacific reached {peaks[now][1]:+.1f} °C,\ncompared with "
                 + join_and(f"{v:+.1f} °C in {y}" for y, v in same.items()) + " at the same stage of those events.",
        source="Data: NOAA Extended Reconstructed SST v5 (ERSST), monthly, 2° grid. Values in the text are anomalies "
               "relative to the 1991–2020 monthly climatology.",
        out=args.out, highlight=now, cbar_ticks=np.arange(20, 32, 2),
        alt=f"Longitude–time diagrams of sea surface temperature anomalies along the equatorial Pacific for "
            + ", ".join(f"{y}–{str(y + 1)[-2:]}" for y in args.years)
            + f". Maximum eastern Pacific anomaly in {last:%B}: {now} {peaks[now][1]:+.1f} °C; "
            + "; ".join(f"{y} {v:+.1f} °C" for y, v in same.items()) + ".")


if __name__ == "__main__":
    main()
