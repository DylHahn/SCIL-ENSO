"""
GODAS potential-temperature anomalies as NetCDF files, e.g. for loading into iCHARM.

Built only from NOAA PSL's public yearly GODAS files (pottmp.YYYY.nc, 40 depths, global
1/3° x 1°, monthly), so anyone can reproduce it. Anomalies are departures from the
1991-2020 monthly normals, the same baseline used everywhere on the SCIL ENSO site.

    python godas_anomalies.py                              # 1980-present, all depths, global
    python godas_anomalies.py --max-depth 300              # upper 300 m only (smaller files)
    python godas_anomalies.py --start 2015 --merge         # also write one file for 2015-present
    python godas_anomalies.py --region tropical-pacific    # 20°S-20°N, 120°E-80°W only

Output (data/godas_anom/, not in the repository):
    pottmp_clim_1991-2020.nc       monthly normals (month, level, lat, lon), °C
    pottmp_anom.YYYY.nc            anomalies (time, level, lat, lon), °C, one file per year
    pottmp_anom.START-END.nc       all years in one file (with --merge)

The first run downloads every yearly file (~65-80 MB each, ~3.5 GB for 1980-present) into
data/godas_raw/; later runs reuse them, and --refresh re-downloads the current year only.
"""
import argparse
import datetime as dt

import numpy as np
import xarray as xr

from enso_common import HERE, download_godas_year

OUT = HERE / "data" / "godas_anom"
CLIM = (1991, 2020)
REGIONS = {"global": None, "tropical-pacific": dict(lat=slice(-20, 20), lon=slice(120, 280))}


def open_year(year, args, refresh=False):
    ds = xr.open_dataset(download_godas_year(year, refresh=refresh))
    da = ds["pottmp"].sel(level=slice(None, args.max_depth))
    if REGIONS[args.region]:
        da = da.sel(**REGIONS[args.region])
    return (da - 273.15).astype("float32")           # kelvin -> °C


def climatology(args):
    """Monthly 1991-2020 normals, accumulated one year at a time to keep memory small."""
    path = OUT / f"pottmp_clim_{CLIM[0]}-{CLIM[1]}_{args.region}_{args.max_depth or 'all'}m.nc"
    if path.exists():
        return xr.open_dataarray(path).load()
    total = count = None
    for y in range(CLIM[0], CLIM[1] + 1):
        print(f"climatology: {y}", flush=True)
        da = open_year(y, args).load()
        assert da.sizes["time"] == 12, f"pottmp.{y}.nc has {da.sizes['time']} months"
        v = da.values
        if total is None:
            total, count = np.zeros_like(v, dtype="float64"), np.zeros(v.shape, dtype="int16")
            template = da
        total += np.nan_to_num(v)
        count += np.isfinite(v)
    with np.errstate(invalid="ignore"):
        mean = (total / count).astype("float32")
    clim = xr.DataArray(mean, dims=("month", "level", "lat", "lon"),
                        coords=dict(month=np.arange(1, 13), level=template["level"], lat=template["lat"],
                                    lon=template["lon"]), name="pottmp_clim")
    clim.attrs = dict(long_name=f"GODAS potential temperature, {CLIM[0]}-{CLIM[1]} monthly mean", units="degC")
    write(clim.to_dataset(), path, "pottmp_clim")
    return clim


def anomalies(year, clim, args):
    da = open_year(year, args, refresh=args.refresh and year == dt.date.today().year).load()
    anom = da.groupby("time.month") - clim
    anom = anom.drop_vars("month").rename("pottmp_anom")
    anom.attrs = dict(long_name="GODAS potential temperature anomaly", units="degC",
                      comment=f"Departure from the {CLIM[0]}-{CLIM[1]} monthly mean")
    return anom


def write(ds, path, var):
    for name, units, long in [("level", "m", "Depth"), ("lat", "degrees_north", "Latitude"),
                              ("lon", "degrees_east", "Longitude")]:
        if name in ds.coords:
            ds[name].attrs.update(units=units, long_name=long)
    ds["level"].attrs.update(positive="down", axis="Z")
    ds.attrs = dict(
        title="GODAS potential temperature anomalies (SCIL ENSO)",
        source="NOAA NCEP GODAS (bias-corrected), monthly, via NOAA PSL: "
               "https://www.psl.noaa.gov/data/gridded/data.godas.html",
        baseline=f"{CLIM[0]}-{CLIM[1]} monthly climatology",
        Conventions="CF-1.8",
        history=f"{dt.date.today():%Y-%m-%d} created by godas_anomalies.py, https://github.com/DylHahn/SCIL-ENSO",
    )
    tmp = path.with_suffix(".tmp.nc")
    ds.to_netcdf(tmp, encoding={var: dict(zlib=True, complevel=4, shuffle=True, dtype="float32",
                                          _FillValue=np.float32(-9.99e33))})
    tmp.replace(path)                                 # never leave a half-written file behind
    print(f"wrote {path} ({path.stat().st_size / 1e6:.0f} MB)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", type=int, default=1980)
    ap.add_argument("--end", type=int, default=dt.date.today().year)
    ap.add_argument("--max-depth", type=float, default=None, help="deepest level to keep, in metres")
    ap.add_argument("--region", choices=REGIONS, default="global")
    ap.add_argument("--merge", action="store_true", help="also write all years into one file")
    ap.add_argument("--refresh", action="store_true", help="re-download the current year's GODAS file")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    clim = climatology(args)
    tag = f"{args.region}_{args.max_depth or 'all'}m"
    files = []
    for y in range(args.start, args.end + 1):
        path = OUT / f"pottmp_anom.{y}_{tag}.nc"
        if not path.exists() or y == dt.date.today().year:     # current year grows each month
            write(anomalies(y, clim, args).to_dataset(), path, "pottmp_anom")
        files.append(path)
    if args.merge:
        with xr.open_mfdataset(files, combine="by_coords") as ds:
            write(ds.load(), OUT / f"pottmp_anom.{args.start}-{args.end}_{tag}.nc", "pottmp_anom")


if __name__ == "__main__":
    main()
