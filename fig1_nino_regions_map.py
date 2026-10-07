"""
Figure 1 — "Where is El Niño measured?"

A locator map of the tropical Pacific with the Niño 3.4 box highlighted.
Optional: the other Niño boxes (--all-regions).

Uses cartopy for coastlines when it is installed; otherwise draws the boxes on
a plain longitude/latitude grid.

    python fig1_nino_regions_map.py
    python fig1_nino_regions_map.py --all-regions
"""
import argparse

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import FuncFormatter

from enso_common import (FIG_DIR, COLORS, NINO_BOXES, add_source, add_title,
                         apply_style, lat_label, lon_label, save)

EXTENT = (100, 290, -30, 30)


def draw_box(ax, box, edge, label, transform, fill=False, label_pos="top", fontsize=13):
    (la0, la1), (lo0, lo1) = box["lat"], box["lon"]
    kw = dict(transform=transform) if transform is not None else {}
    ax.add_patch(patches.Rectangle(
        (lo0, la0), lo1 - lo0, la1 - la0,
        facecolor=edge if fill else "none", alpha=0.18 if fill else 1,
        edgecolor="none" if fill else edge, linewidth=0, zorder=5, **kw))
    ax.add_patch(patches.Rectangle(
        (lo0, la0), lo1 - lo0, la1 - la0, facecolor="none",
        edgecolor=edge, linewidth=2.4, zorder=6, **kw))
    y = la1 + 1.2 if label_pos == "top" else la0 - 1.2
    va = "bottom" if label_pos == "top" else "top"
    ax.text((lo0 + lo1) / 2, y, label, ha="center", va=va, fontsize=fontsize,
            fontweight="bold", color=edge, zorder=7, **kw)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all-regions", action="store_true", help="also draw Niño 1+2, 3 and 4")
    ap.add_argument("--no-cartopy", action="store_true", help="skip coastlines even if cartopy is installed")
    ap.add_argument("--out", default=str(FIG_DIR / "fig1_nino_regions_map.png"))
    args = ap.parse_args()

    apply_style()
    fig = plt.figure(figsize=(13, 5.4))

    use_cartopy = not args.no_cartopy
    if use_cartopy:
        try:
            import cartopy.crs as ccrs
            import cartopy.feature as cfeature
        except ImportError:
            print("cartopy not installed — drawing without coastlines.")
            use_cartopy = False

    rect = [0.06, 0.09, 0.92, 0.73]
    if use_cartopy:
        ax = fig.add_axes(rect, projection=ccrs.PlateCarree(central_longitude=180))
        data_crs = ccrs.PlateCarree()
        ax.set_extent(EXTENT, crs=data_crs)
        ax.add_feature(cfeature.OCEAN, facecolor="#e8f1fb", zorder=0)
        ax.add_feature(cfeature.LAND, facecolor="#dcdad3", edgecolor="#a3a29c", linewidth=0.5, zorder=1)
        ax.set_xticks([120, 150, 180, 210, 240, 270], crs=data_crs)
        ax.set_yticks([-20, -10, 0, 10, 20], crs=data_crs)
        transform = data_crs
    else:
        ax = fig.add_axes(rect)
        ax.set_xlim(EXTENT[0], EXTENT[1])
        ax.set_ylim(EXTENT[2], EXTENT[3])
        ax.set_facecolor("#e8f1fb")
        ax.set_xticks([120, 150, 180, 210, 240, 270])
        ax.set_yticks([-20, -10, 0, 10, 20])
        ax.set_aspect("equal")
        transform = None
        for name, x in (("Asia /\nAustralia", 118), ("Americas", 282)):
            ax.text(x, -24, name, ha="center", fontsize=12, color=COLORS["text_2"])

    if use_cartopy:
        # the map is centred on 180°, so tick values are shifted; let cartopy label them
        from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter
        ax.xaxis.set_major_formatter(LongitudeFormatter(degree_symbol="°"))
        ax.yaxis.set_major_formatter(LatitudeFormatter(degree_symbol="°"))
    else:
        ax.xaxis.set_major_formatter(FuncFormatter(lon_label))
        ax.yaxis.set_major_formatter(FuncFormatter(lat_label))
    kw = dict(transform=transform) if transform is not None else {}
    ax.plot([EXTENT[0], EXTENT[1]], [0, 0], color=COLORS["muted"], lw=0.8, ls="--", zorder=2, **kw)
    ax.text(EXTENT[0] + 2, 0.6, "Equator", fontsize=10, color=COLORS["muted"], zorder=2, **kw)

    if args.all_regions:
        others = {"Niño 4": "#6d5bd0", "Niño 3": "#1baf7a", "Niño 1+2": "#c98500"}
        for name, col in others.items():
            pos = "bottom" if name != "Niño 1+2" else "bottom"
            draw_box(ax, NINO_BOXES[name], col, name, transform, label_pos=pos, fontsize=12)

    draw_box(ax, NINO_BOXES["Niño 3.4"], COLORS["el_nino"], "Niño 3.4", transform, fill=True,
             fontsize=15)

    add_title(fig,
              "Where is El Niño measured?",
              "NOAA tracks ocean temperature in the red Niño 3.4 box (5°N–5°S, 170°W–120°W). "
              "Warmer than usual = El Niño; cooler = La Niña.")
    add_source(fig, "Region definitions: NOAA Climate Prediction Center.")
    save(fig, args.out)


if __name__ == "__main__":
    main()
