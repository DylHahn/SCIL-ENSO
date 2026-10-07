"""
Statistics helpers for the "what El Niño has done before" graphics.

Gridded data (downloaded once into data/gridded/, see GRIDDED):
  * GPCP v2.3 monthly precipitation, 2.5°, 1979–present (mm/day)
  * NOAAGlobalTemp monthly surface temperature anomalies, 5°, 1850–present (°C)

Method, in plain terms
  1. Average each year's months into seasons: Dec–Feb (labelled by the January)
     and Jun–Aug.
  2. Express each season as a difference from the 1991–2020 normal.
  3. Remove the slow long-term trend at every grid point, so the maps show what
     El Niño does on top of climate change rather than the warming itself.
  4. Pick the El Niño seasons from NOAA's RONI: winters whose Dec–Feb RONI is at
     least +1.0 °C (moderate or stronger), and the Jun–Aug before each of them.
  5. Average those seasons (composite) or count how many were wetter / warmer
     than normal (odds).
"""

from __future__ import annotations

import urllib.request

import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap

from enso_common import COLORS, HERE, load_roni

GRIDDED_DIR = HERE / "data" / "gridded"
GRIDDED = {
    "rain": ("https://downloads.psl.noaa.gov/Datasets/gpcp/precip.mon.mean.nc", "precip"),
    "temp": ("https://downloads.psl.noaa.gov/Datasets/noaaglobaltemp/air.mon.anom.nc", "air"),
}
SEASONS = {"Dec–Feb": (12, 1, 2), "Jun–Aug": (6, 7, 8)}


def load_gridded(var, refresh=False) -> xr.DataArray:
    """Monthly field (time, lat, lon), latitude ascending, longitude 0–360."""
    url, name = GRIDDED[var]
    path = GRIDDED_DIR / url.rsplit("/", 1)[-1]
    if refresh or not path.exists():
        GRIDDED_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {url} ...")
        urllib.request.urlretrieve(url, path)
    # GPCP's time_bnds holds fill values that can't be decoded as dates; we don't need it
    with xr.open_dataset(path, drop_variables=["time_bnds"]) as ds:
        da = ds[name].load()
    return da.sortby("lat")


def seasonal_means(da, season) -> xr.DataArray:
    """Seasonal means indexed by `year`; Dec–Feb is labelled by its January."""
    months = SEASONS[season]
    sel = da.where(da["time.month"].isin(months), drop=True)
    year = sel["time.year"] + (sel["time.month"] == 12)        # December counts toward next year
    out = sel.groupby(year.rename("year")).mean("time")
    counts = sel["time"].groupby(year.rename("year")).count()
    return out.sel(year=counts["year"][counts == 3])           # complete seasons only


def seasonal_anomalies(da, season, clim=(1991, 2020), detrend=True):
    """(anomalies[year, lat, lon], normal[lat, lon]) for one season."""
    s = seasonal_means(da, season)
    normal = s.sel(year=slice(*clim)).mean("year")
    anom = s - normal
    if detrend:
        fit = anom.polyfit("year", 1)["polyfit_coefficients"]
        anom = anom - xr.polyval(anom["year"], fit)
    return anom, normal


def el_nino_years(season, threshold=1.0, refresh=False, years_available=None):
    """Season labels (years) that belong to an El Niño of at least `threshold` (Dec–Feb RONI).

    For Dec–Feb that's the January year; for Jun–Aug it's the summer before, while
    the event is building."""
    roni = load_roni(refresh=refresh)
    winters = [t.year for t, v in roni.items() if t.month == 1 and v >= threshold]
    years = winters if season == "Dec–Feb" else [y - 1 for y in winters]
    if years_available is not None:
        years = [y for y in years if y in set(years_available)]
    return years


# ---------------------------------------------------------------------------
# Colour: diverging, two hues with a neutral gray middle that matches the theme
# ---------------------------------------------------------------------------
RAIN_STEPS = ["#8c510a", "#bf812d", "#dfc27d", None, "#80cdc1", "#35978f", "#01665e"]
TEMP_STEPS = ["#2166ac", "#4393c3", "#92c5de", None, "#f4a582", "#d6604d", "#b2182b"]


def diverging(kind, levels, clear_middle=True):
    """Discrete diverging colormap with one bin per gap in `levels`.

    Blends dark → light → neutral gray → light → dark; with an odd number of bins
    the middle bin is exactly the neutral gray ("no clear change")."""
    steps = RAIN_STEPS if kind == "rain" else TEMP_STEPS
    anchors = steps[:3] + [COLORS["map_neutral"]] + steps[4:]
    ramp = LinearSegmentedColormap.from_list(kind, anchors)
    nbins = len(levels) - 1
    colors = [ramp(x) for x in np.linspace(0, 1, nbins)]
    if nbins % 2 and clear_middle:
        colors[nbins // 2] = (0, 0, 0, 0)    # "little change": let the map show through
    cmap = ListedColormap(colors)
    cmap.set_under(steps[0])
    cmap.set_over(steps[-1])
    cmap.set_bad((0, 0, 0, 0))          # missing / masked: let the land or ocean show through
    return cmap, BoundaryNorm(levels, cmap.N)


def draw_pair(fig, fields, levels, kind, panel_titles, notes=None, clear_middle=True, extend="both"):
    """Two stacked Pacific-centred maps; returns the last mappable for a colourbar."""
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.util import add_cyclic_point

    proj = ccrs.PlateCarree(central_longitude=160)
    cmap, norm = diverging(kind, levels, clear_middle)
    rects = [[0.02, 0.535, 0.96, 0.33], [0.02, 0.165, 0.96, 0.33]]
    mappable = None
    for rect, field, title, note in zip(rects, fields, panel_titles, notes or [None, None]):
        ax = fig.add_axes(rect, projection=proj)
        ax.set_extent([-180, 180, -50, 65], crs=proj)
        ax.add_feature(cfeature.OCEAN, facecolor=COLORS["ocean"], zorder=0)
        ax.add_feature(cfeature.LAND, facecolor=COLORS["land"], edgecolor="none", zorder=0)
        ax.spines["geo"].set_visible(False)
        # interpolate the coarse grid to 1° so contour edges look smooth (no new information added)
        wrap = xr.concat([field.isel(lon=[-1]).assign_coords(lon=field["lon"][[-1]] - 360), field,
                          field.isel(lon=[0]).assign_coords(lon=field["lon"][[0]] + 360)], "lon")
        field = wrap.interp(lat=np.arange(-89.5, 90, 1.0), lon=np.arange(0.5, 360, 1.0))
        data, lon = add_cyclic_point(field.values, coord=field["lon"].values)
        mappable = ax.contourf(lon, field["lat"].values, data, levels=levels, cmap=cmap, norm=norm,
                               extend=extend, transform=ccrs.PlateCarree(), zorder=1)
        ax.add_feature(cfeature.COASTLINE, edgecolor=COLORS["text_2"], linewidth=0.5, zorder=2)
        ax.text(0.0, 1.03, title, transform=ax.transAxes, fontsize=16, fontweight="bold",
                color=COLORS["text"], va="bottom")
        if note:
            ax.text(1.0, 1.03, note, transform=ax.transAxes, fontsize=11, color=COLORS["text_2"],
                    va="bottom", ha="right")
    return mappable


def season_years_text(years, season):
    if season == "Dec–Feb":
        return ", ".join(f"{y - 1}–{str(y)[-2:]}" for y in years)
    return ", ".join(str(y) for y in years)


def map_figure(fields, levels, kind, panel_titles, title, subtitle, source, out, alt,
               cbar_label, cbar_ticks=None, cbar_ticklabels=None, extend="both", notes=None,
               clear_middle=True, middle_label="little\nchange"):
    """Two stacked maps + a horizontal colour bar + title/source, saved with alt text."""
    import matplotlib.pyplot as plt
    from enso_common import add_source, add_title, save

    fig = plt.figure(figsize=(13, 12.2))
    m = draw_pair(fig, fields, levels, kind, panel_titles, notes, clear_middle, extend)
    cax = fig.add_axes([0.2, 0.085, 0.6, 0.018])
    cb = fig.colorbar(m, cax=cax, orientation="horizontal",
                      ticks=cbar_ticks if cbar_ticks is not None else levels)
    if cbar_ticklabels is not None:
        cb.set_ticklabels(cbar_ticklabels)
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, labelsize=11.5)
    cb.set_label(cbar_label, fontsize=12.5, color=COLORS["text"], labelpad=8)
    if clear_middle and (len(levels) - 1) % 2:
        mid = len(levels) // 2
        cax.text((levels[mid - 1] + levels[mid]) / 2, 0.5, middle_label, ha="center", va="center",
                 fontsize=9.5, color=COLORS["text_2"], transform=cax.get_xaxis_transform())
    add_title(fig, title, subtitle)
    add_source(fig, source)
    save(fig, out, alt=alt)


def agreement(anoms, composite):
    """Share of events whose anomaly has the same sign as the composite (0–1)."""
    same = (np.sign(anoms) == np.sign(composite)).where(np.isfinite(anoms))
    return same.mean("year")
