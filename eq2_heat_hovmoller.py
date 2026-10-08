"""
Equatorial 2 — Upper-ocean heat content anomalies along the equator (Hovmöller)

Monthly temperature anomalies averaged over the upper 200 m (GODAS levels
5–205 m) and 2°S–2°N, from 130°E to 80°W, for each event from January of the
onset year to the following January. This is the subsurface heat that precedes
and sustains warming at the surface; eastward-tilted bands are downwelling
Kelvin waves. Source: NCEP GODAS (as hosted on iCHARM), anomalies relative to
1991–2020.

    python eq2_heat_hovmoller.py
"""
import argparse

import numpy as np
import pandas as pd

from enso_common import (FIG_DIR, GODAS_DIR, GODAS_RAW_DIR, apply_style, download_godas_year,
                         godas_equatorial_section, join_and)
from enso_equatorial import EVENTS, LON_RANGE, event_months, hovmoller_figure


def available_months(year, refresh=False):
    """Months of `year` with GODAS data: the depth files cover through 2025, NOAA's yearly file after."""
    import xarray as xr
    months = event_months(year)
    if year + 1 <= 2025:
        return months
    with xr.open_dataset(download_godas_year(year, refresh)) as ds:
        last = pd.Timestamp(ds["time"].values[-1])
    return [m for m in months if m <= last]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", type=int, nargs="+", default=EVENTS)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "equatorial" / "eq2_heat_hovmoller.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    fields, east_mean = {}, {}
    for y in args.years:
        months = available_months(y, args.refresh and y == args.years[-1])
        depths, lons, anoms, _ = godas_equatorial_section(GODAS_DIR, [m.strftime("%Y-%m-%d") for m in months],
                                                          lon_range=(LON_RANGE[0] - 1, LON_RANGE[1]))
        upper = np.nanmean(anoms, axis=1)                       # equal 10 m layers: plain mean over depth
        fields[y] = (months, lons, upper)
        east = lons >= 180
        east_mean[y] = {m: float(np.nanmean(row[east])) for m, row in zip(months, upper)}
    now = args.years[-1]
    last = fields[now][0][-1]
    same = {y: east_mean[y][pd.Timestamp(f"{y}-{last.month:02d}-01")] for y in args.years[:-1]}

    levels = np.arange(-4.25, 4.5, 0.5)
    hovmoller_figure(
        fields, levels, "RdBu_r", "Mean temperature anomaly, 5–205 m (°C), 2°S–2°N, relative to 1991–2020",
        title="Equatorial Pacific upper-ocean heat content during major El Niño events",
        subtitle=f"Temperature anomalies averaged over the upper 200 m. Eastward-sloping warm bands are "
                 f"downwelling Kelvin waves carrying heat toward South America.\nIn {last:%B} {now}, the "
                 f"central–eastern Pacific (180°–80°W) averaged {east_mean[now][last]:+.1f} °C, compared with "
                 + join_and(f"{v:+.1f} °C in {y}" for y, v in same.items()) + ".",
        source="Data: NCEP Global Ocean Data Assimilation System (GODAS), monthly; anomalies relative to the "
               "1991–2020 monthly climatology.",
        out=args.out, highlight=now, cbar_ticks=np.arange(-4, 4.5, 2),
        alt=f"Longitude–time diagrams of upper-200 m temperature anomalies along the equatorial Pacific for "
            + join_and(f"{y}–{str(y + 1)[-2:]}" for y in args.years)
            + f". Central–eastern Pacific mean in {last:%B}: {now} {east_mean[now][last]:+.1f} °C; "
            + "; ".join(f"{y} {v:+.1f} °C" for y, v in same.items()) + ".")


if __name__ == "__main__":
    main()
