"""
Animation 4 — Warm water moving across the tropical Pacific: thickness of the warm upper layer,
month by month, for 2026, the past very strong El Niños (2015, 1997, 1982) and normal

Maps of the depth of the 20 °C isotherm (D20) from NCEP GODAS over 20°S–20°N, 120°E–80°W.
D20 is the thickness of the warm upper layer: where it is deep, a large volume of warm water
is stored. Before an El Niño, warm water builds up in the western Pacific; during the event it
surges east along the equator, deepening the warm layer off South America. Each panel also
reports the equatorial warm water volume (WWV, the volume above the 20 °C isotherm over
5°S–5°N, 120°E–80°W, after NOAA PMEL) and its departure from normal.

Each event runs from January of its first year to December of the next; the current event holds at
the latest GODAS month. The normal is D20 of the 1991–2020 monthly mean temperature. Frames are
interpolated between months for smooth playback.

    python anim_warm_water.py
    python anim_warm_water.py --compare 1997 2015
"""
import argparse
import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm

from enso_anim import (EVENT_MONTHS, AnimationFrames, event_months, event_name, hold_last, interpolate_months,
                       month_label)
from enso_common import (FIG_DIR, GODAS_DEPTHS, GODAS_DIR, COLORS, add_source, add_title, apply_style,
                         download_godas_year, godas_path, join_and)

LAT, LON = (-20, 20), (120, 280)
WWV_BOX = dict(lat=(-5, 5), lon=(120, 280))
R_EARTH = 6.371e6


def load_temps(months, refresh=False):
    """(time, depth, lat, lon) temperature in °C for the requested months, from the GODAS depth files
    and, for months after they end, NOAA PSL's yearly files. Returns (temps, lat, lon, depths)."""
    import xarray as xr
    months = pd.DatetimeIndex(months)
    depths = [d for d in GODAS_DEPTHS if godas_path(GODAS_DIR, d).exists()]
    out = np.full((len(months), len(depths), 0, 0), np.nan, dtype="float32")
    lat = lon = None
    for j, d in enumerate(depths):
        with xr.open_dataset(godas_path(GODAS_DIR, d)) as ds:
            da = ds["deepTemp"].sel(lat=slice(*LAT), lon=slice(*LON))
            have = pd.to_datetime(da["time"].values)
            if lat is None:
                lat, lon = da["lat"].values, da["lon"].values
                out = np.full((len(months), len(depths), len(lat), len(lon)), np.nan, dtype="float32")
            pick = [i for i, m in enumerate(months) if m in have]
            if pick:
                vals = da.sel(time=months[pick]).values
                out[pick, j] = vals - 273.15 if np.nanmean(vals) > 100 else vals
    missing = [i for i in range(len(months)) if np.isnan(out[i]).all()]
    for y in sorted({months[i].year for i in missing if months[i].year <= pd.Timestamp.today().year}):
        with xr.open_dataset(download_godas_year(y, refresh)) as ds:
            da = ds["pottmp"].sel(lat=slice(*LAT), lon=slice(*LON), level=[float(d) for d in depths])
            have = pd.to_datetime(da["time"].values)
            for i in missing:
                if months[i].year == y and months[i] in have:
                    out[i] = da.sel(time=months[i]).values - 273.15
    keep = [i for i in range(len(months)) if not np.isnan(out[i]).all()]
    return out[keep], months[keep], lat, lon, np.array(depths, dtype=float)


def monthly_normal(month_numbers):
    """(n, depth, lat, lon) 1991–2020 mean temperature (°C) for each requested calendar month."""
    import xarray as xr
    depths = [d for d in GODAS_DEPTHS if godas_path(GODAS_DIR, d).exists()]
    out = []
    for d in depths:
        with xr.open_dataset(godas_path(GODAS_DIR, d)) as ds:
            da = ds["deepTemp"].sel(lat=slice(*LAT), lon=slice(*LON), time=slice("1991-01-01", "2020-12-31"))
            clim = da.groupby("time.month").mean("time").sel(month=month_numbers).values
        out.append(clim - 273.15 if np.nanmean(clim) > 100 else clim)
    return np.stack(out, axis=1)


def d20(temps, depths, threshold=20.0):
    """Depth (m) of the `threshold` isotherm for (..., depth, lat, lon) temperatures, by linear
    interpolation between levels. 0 where the surface is cooler; the deepest level where the whole
    column is warmer; NaN on land."""
    t = np.moveaxis(temps, -3, -1)                         # (..., lat, lon, depth)
    warm = t >= threshold
    below = ~warm & np.isfinite(t)
    first_cold = np.where(below.any(-1), below.argmax(-1), t.shape[-1] - 1)
    k = np.clip(first_cold, 1, t.shape[-1] - 1)
    t0 = np.take_along_axis(t, (k - 1)[..., None], -1)[..., 0]
    t1 = np.take_along_axis(t, k[..., None], -1)[..., 0]
    z0, z1 = depths[k - 1], depths[k]
    with np.errstate(invalid="ignore", divide="ignore"):
        z = z0 + (t0 - threshold) / (t0 - t1) * (z1 - z0)
    z = np.where(~below.any(-1), depths[-1], z)            # warm all the way down
    z = np.where(~warm[..., 0], 0.0, z)                    # surface already cooler than 20 °C
    return np.where(np.isfinite(t[..., 0]), z, np.nan)


def wwv(field, lat, lon):
    """Warm water volume (10¹⁴ m³) above the 20 °C isotherm over the PMEL box."""
    la = (lat >= WWV_BOX["lat"][0]) & (lat <= WWV_BOX["lat"][1])
    lo = (lon >= WWV_BOX["lon"][0]) & (lon <= WWV_BOX["lon"][1])
    dlat, dlon = np.deg2rad(np.abs(np.diff(lat).mean())), np.deg2rad(np.abs(np.diff(lon).mean()))
    area = R_EARTH ** 2 * np.cos(np.deg2rad(lat[la]))[:, None] * dlat * dlon
    return float(np.nansum(field[la][:, lo] * area) / 1e14)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--compare", type=int, nargs="+", default=[2015, 1997, 1982],
                    help="past onset years to show (GODAS begins in 1980)")
    ap.add_argument("--steps", type=int, default=2, help="interpolated frames per month")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "anim" / "anim_warm_water.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from scipy.ndimage import zoom

    apply_style(args.theme)
    # each El Niño from January of its first year to December of the next; the current event holds at its
    # latest month
    temps, months, lat, lon, depths = load_temps(event_months(args.year), args.refresh)
    latest = months[-1]
    years = [args.year] + list(args.compare)
    stacks = [d20(temps, depths)]
    for y in args.compare:
        t, got, _, _, _ = load_temps(event_months(y))
        assert len(got) == EVENT_MONTHS, f"GODAS months missing for {y}"
        stacks.append(d20(t, depths))
    normal = d20(monthly_normal([m.month for m in event_months(2000)]), depths)
    wwv_rows = [hold_last([wwv(f, lat, lon) for f in st])[0] for st in stacks]
    normal_wwv = [wwv(f, lat, lon) for f in normal]
    rows, haves = [], []
    for y, st in zip(years, stacks):
        sp, have = hold_last(st)
        rows.append((event_name(y), sp)); haves.append(have)
    rows.append(("Normal (1991–2020)", normal)); haves.append(EVENT_MONTHS)
    n = EVENT_MONTHS

    land = np.isnan(rows[0][1][0])
    Z = 3                                                   # resample 3× for a smooth display of the 1° grid
    land_f = zoom(land.astype(float), Z, order=0) > 0.5
    lat_f = np.linspace(lat.min(), lat.max(), len(lat) * Z)
    lon_f = np.linspace(lon.min(), lon.max(), len(lon) * Z)

    def fine(a):
        filled = np.where(np.isfinite(a), a, np.nanmean(a))
        return np.where(land_f, np.nan, zoom(filled, Z, order=1))

    top_in, row_in, map_in, bottom_in = 1.75, 3.05, 2.6, 1.45
    H = top_in + row_in * len(rows) + bottom_in
    fig = plt.figure(figsize=(13, H))
    proj, pc = ccrs.PlateCarree(central_longitude=200), ccrs.PlateCarree()
    levels = np.arange(0, 220.01, 10)
    cmap = plt.get_cmap("turbo", len(levels) + 1)
    norm = BoundaryNorm(levels, cmap.N, extend="both")
    meshes, labels, axes = [], [], []
    for k, (name, stack) in enumerate(rows):
        ax = fig.add_axes([0.06, 1 - (top_in + row_in * k + map_in) / H, 0.90, map_in / H], projection=proj)
        ax.set_extent([LON[0], LON[1], -20, 20], crs=pc)
        meshes.append(ax.pcolormesh(lon_f, lat_f, fine(stack[0]), cmap=cmap, norm=norm, transform=pc,
                                    shading="nearest", rasterized=True, zorder=1))
        ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor="black", edgecolor="none", zorder=2)
        ax.plot([100, 300], [0, 0], transform=pc, color="black", lw=0.8, zorder=3)
        for yb in WWV_BOX["lat"]:                              # the warm-water-volume band
            ax.plot([LON[0], LON[1]], [yb, yb], transform=pc, color="white", lw=0.9, ls=(0, (4, 3)), alpha=0.7,
                    zorder=3)
        cur = k == 0
        ax.set_title(name, fontsize=15, fontweight="bold", loc="left", pad=6,
                     color=COLORS["el_nino"] if cur else COLORS["text"])
        labels.append(ax.text(0.99, 1.03, "", transform=ax.transAxes, ha="right", va="bottom", fontsize=13.5,
                              fontweight="bold", color=COLORS["text"]))
        gl = ax.gridlines(crs=pc, draw_labels=dict(left="y", bottom="x" if k == len(rows) - 1 else False),
                          xlocs=[120, 140, 160, 180, -160, -140, -120, -100, -80], ylocs=[-20, -10, 0, 10, 20],
                          linewidth=0, color="none")
        gl.xlabel_style = gl.ylabel_style = dict(size=10, color=COLORS["text_2"])
        ax.spines["geo"].set_edgecolor(COLORS["el_nino"] if cur else COLORS["grid"])
        ax.spines["geo"].set_linewidth(2 if cur else 0.8)
        axes.append(ax)
    cax = fig.add_axes([0.25, 0.82 / H, 0.5, 0.17 / H])
    cb = fig.colorbar(meshes[0], cax=cax, orientation="horizontal", ticks=np.arange(0, 221, 20))
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    cb.set_label("Depth of the 20 °C isotherm (m): thickness of the warm upper layer · dashed lines: 5°S and 5°N",
                 fontsize=11, color=COLORS["text_2"])
    add_title(fig, f"Warm water across the tropical Pacific: {event_name(args.year)} compared with "
                   f"{join_and(event_name(y) for y in args.compare)}",
              "January of each El Niño's first year to December of the next. Red shows where the warm upper layer is "
              "thickest: it surges east along\nthe equator as El Niño develops and drains away as it ends. WWV: warm "
              "water volume between 5°S and 5°N (10$^{14}$ m³), departure from normal in brackets.")
    add_source(fig, "Data: NCEP GODAS ocean reanalysis (NOAA), monthly, 1° × ⅓°, 10 m levels to 205 m, resampled for "
               "display; normal from the 1991–2020 mean temperature. Frames are interpolated between months.")

    frames = AnimationFrames(fig, dpi=110)
    seqs = [interpolate_months(stack, args.steps) for _, stack in rows]
    for i, pos in enumerate(seqs[0][1]):
        k = int(round(pos))
        f = pos - int(pos)
        for r, (name, _) in enumerate(rows):
            field = seqs[r][0][i]
            meshes[r].set_array(fine(field).ravel())
            if r < len(rows) - 1:
                when = month_label(years[r], k, haves[r])
                p0 = min(pos, haves[r] - 1)                    # an event in progress holds at its latest month
                i0, f0 = int(p0), p0 - int(p0)
                v = (1 - f0) * wwv_rows[r][i0] + f0 * wwv_rows[r][min(i0 + 1, n - 1)]
                vn = (1 - f0) * normal_wwv[i0] + f0 * normal_wwv[min(i0 + 1, n - 1)]
                labels[r].set_text(f"{when}  ·  WWV {v:.1f} ({round(v - vn, 1) + 0.0:+.1f}) × 10$^{{14}}$ m³")
            else:
                labels[r].set_text(f"{calendar.month_name[k % 12 + 1]}  ·  WWV {normal_wwv[k]:.1f} × 10$^{{14}}$ m³")
        frames.grab(600 if abs(pos - round(pos)) < 1e-9 else 90)
    frames.durations[-1] = 3000
    names = [nm for nm, _ in rows[:-1]]
    frames.save(args.out, quality=86,
                alt=f"Animated maps of the depth of the 20 °C isotherm across the tropical Pacific from January of "
                    f"each El Niño's first year to December of the next, for {join_and(names)} (the current event to "
                    f"{latest:%B %Y}) and the 1991–2020 normal. In {latest:%B} of the first year, the equatorial warm "
                    f"water volume departed from normal by "
                    + join_and(f"{w[haves[0] - 1] - normal_wwv[haves[0] - 1]:+.1f} × 10¹⁴ m³ in {nm}"
                               for nm, w in zip(names, wwv_rows))
                    + ".")


if __name__ == "__main__":
    main()
