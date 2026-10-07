"""
Story 3 — "Who feels El Niño, and how"

Two world maps of the typical El Niño weather pattern: December–February
(the peak of a Northern Hemisphere winter event) and June–August.
Regions follow the well-known El Niño impact maps from NOAA Climate.gov and
the IRI (Columbia University). They show what tends to happen, not a forecast.

Each region is a soft ellipse: (label, lon, lat, half-width°, half-height°).
Edit REGIONS to adjust wording or add places relevant to your audience.

    python story3_global_impacts.py
    python story3_global_impacts.py --theme light
"""
import argparse

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Patch

from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, save

KINDS = {
    # name: (dark-theme colour, light-theme colour, legend label)
    "dry": ("#c98500", "#b07400", "Drier: drought, crop & water stress, fire risk"),
    "wet": ("#1fb5a0", "#128a79", "Wetter: heavy rain & flood risk"),
    "warm": ("#e66767", "#d64545", "Warmer than usual"),
}

# (kind, label, lon, lat, half-width, half-height, label offset (dlon, dlat), text alignment)
REGIONS = {
    "Dec–Feb": [
        ("wet", "Southern US &\nnorthern Mexico", -97, 30, 20, 6, (0, -11), "center"),
        ("warm", "Northern US & Canada", -105, 52, 26, 7, (0, 10), "center"),
        ("wet", "Peru & Ecuador\ncoast", -80, -5, 4, 6, (-12, -2), "right"),
        ("dry", "Northern South\nAmerica", -62, 4, 10, 6, (13, 4), "left"),
        ("wet", "Southeast\nSouth America", -56, -30, 9, 7, (-11, -6), "right"),
        ("dry", "Southern Africa", 28, -20, 11, 8, (-14, -10), "right"),
        ("wet", "East Africa\n(Oct–Dec rains)", 40, -2, 6, 7, (10, 4), "left"),
        ("dry", "Indonesia, Philippines\n& northern Australia", 125, -6, 20, 11, (0, -16), "center"),
        ("wet", "Central Pacific\nislands", -165, 0, 16, 5, (0, 7), "center"),
    ],
    "Jun–Aug": [
        ("dry", "India\n(weaker monsoon)", 78, 21, 8, 8, (-10, 10), "right"),
        ("dry", "Indonesia", 117, -3, 15, 7, (0, 10), "center"),
        ("dry", "Eastern Australia\n(into spring)", 147, -29, 7, 9, (10, -9), "left"),
        ("dry", "Central America\n& Caribbean", -82, 14, 13, 6, (-15, 6), "right"),
        ("dry", "Ethiopia", 39, 10, 6, 5, (10, 4), "left"),
        ("wet", "Central Chile", -71, -35, 4, 6, (6, -8), "left"),
        ("wet", "Peru & Ecuador\ncoast", -80, -5, 4, 6, (-12, -2), "right"),
        ("wet", "Central Pacific\nislands", -165, 0, 16, 5, (0, 7), "center"),
    ],
}

NOTES = {
    "Dec–Feb": "Stronger winter storms along the US Gulf and California coasts are more likely.",
    "Jun–Aug": "Fewer Atlantic hurricanes; more hurricanes and typhoons in the central & eastern Pacific.",
}


def draw_map(ax, ccrs, cfeature, season, theme):
    pc = ccrs.PlateCarree()
    # whole way round the world, centred on the Pacific; poles cut (nothing to show there)
    ax.set_extent([-180, 180, -50, 65], crs=ax.projection)
    ax.add_feature(cfeature.OCEAN, facecolor=COLORS["ocean"], zorder=0)
    ax.add_feature(cfeature.LAND, facecolor=COLORS["land"], edgecolor="none", zorder=1)
    ax.spines["geo"].set_visible(False)
    ax.plot([-180, 180], [0, 0], transform=pc, color=COLORS["muted"], lw=0.6, ls=(0, (4, 3)), zorder=2)

    for kind, label, lon, lat, rw, rh, (dx, dy), ha in REGIONS[season]:
        col = KINDS[kind][0 if theme == "dark" else 1]
        ax.add_patch(Ellipse((lon, lat), 2 * rw, 2 * rh, transform=pc, facecolor=col, alpha=0.55,
                             edgecolor=col, lw=1.6, zorder=3))
        va = "bottom" if dy > 0 else ("top" if dy < 0 else "center")
        ax.text(lon + dx, lat + dy, label, transform=pc, ha=ha, va=va, fontsize=10.5,
                color=COLORS["text"], zorder=5, linespacing=1.15,
                bbox=dict(facecolor=COLORS["surface"], alpha=0.6, edgecolor="none", pad=1.5))

    ax.text(0.0, 1.03, season, transform=ax.transAxes, fontsize=16, fontweight="bold",
            color=COLORS["text"], va="bottom")
    ax.text(1.0, 1.03, NOTES[season], transform=ax.transAxes, fontsize=11, color=COLORS["text_2"],
            va="bottom", ha="right")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--out", default=str(FIG_DIR / "story" / "story3_global_impacts.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    apply_style(args.theme)
    fig = plt.figure(figsize=(13, 11.6))
    proj = ccrs.PlateCarree(central_longitude=160)  # keeps the Pacific in one piece
    axes = [fig.add_axes([0.02, 0.535, 0.96, 0.33], projection=proj),
            fig.add_axes([0.02, 0.125, 0.96, 0.33], projection=proj)]
    for ax, season in zip(axes, REGIONS):
        draw_map(ax, ccrs, cfeature, season, args.theme)

    handles = [Patch(facecolor=v[0 if args.theme == "dark" else 1], alpha=0.7, label=v[2])
               for v in KINDS.values()]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.045), fontsize=12,
               labelcolor=COLORS["text_2"])

    add_title(fig, "Who feels El Niño, and how",
              "El Niño shifts where rain falls around the world. These are the usual patterns. "
              "A Super El Niño makes them\nmore likely, but not certain: every event is different.")
    add_source(fig, "Typical El Niño patterns after NOAA Climate.gov and IRI (Columbia University). "
               "Not a forecast: check your national weather service for local outlooks.")
    save(fig, args.out,
         alt="Two world maps of typical El Niño impacts. December to February: wetter in the southern US, "
             "Peru and Ecuador, southeast South America and East Africa; drier in southern Africa, "
             "northern South America, Indonesia, the Philippines and northern Australia; warmer in the "
             "northern US and Canada. June to August: drier in India, Indonesia, eastern Australia, "
             "Central America and Ethiopia; wetter in central Chile and coastal Peru and Ecuador.")


if __name__ == "__main__":
    main()
