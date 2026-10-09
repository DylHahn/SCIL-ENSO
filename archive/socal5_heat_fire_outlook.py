"""
SoCal 5 — Official heat and wildfire outlook for Southern California

Top row: National Interagency Fire Center Predictive Services outlook of
significant wildland fire potential (above / normal / below normal) for the
Southern California Geographic Area, month by month for the next four months.
Bottom row: NOAA Climate Prediction Center probability of above-normal
temperature for the next four overlapping 3-month seasons.

Both are official products, read directly from their published services, so the
figure updates when the agencies issue new outlooks (fire: 1st of the month;
temperature: 3rd Thursday).

    python socal5_heat_fire_outlook.py
    python socal5_heat_fire_outlook.py --refresh
"""
import argparse
import json
import urllib.request

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from enso_common import FIG_DIR, COLORS, HERE, add_source, add_title, apply_style, save
from socal_outlook import BANDS, SHADES, load_leads, odds_at, season_text

FIRE_URL = ("https://fsapps.nwcg.gov/psp/arcgis/rest/services/npsg/Outlooks_Monthly_Extended/MapServer/"
            "{layer}/query?where=GACCUnitID%3D%27USCAOSCC%27&outFields=PSANAME,FirePotent,Updatetime"
            "&outSR=4326&f=geojson")
FIRE_DIR = HERE / "data" / "fire_outlook"
FIRE_COLORS = {"Above": "#d64545", "Normal": None, "Below": "#3f9a5a"}
EXTENT = [-121.2, -114.2, 32.4, 36.6]
CITIES = {"Los Angeles": (-118.24, 34.05), "San Diego": (-117.16, 32.72), "Riverside": (-117.40, 33.95),
          "Santa Barbara": (-119.70, 34.42)}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def load_fire(layer, refresh):
    FIRE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIRE_DIR / f"month{layer + 1}.geojson"
    if refresh or not path.exists():
        print(f"Downloading fire potential outlook, month {layer + 1} ...")
        with urllib.request.urlopen(FIRE_URL.format(layer=layer), timeout=60) as r:
            path.write_bytes(r.read())
    return json.loads(path.read_text())


def base_map(fig, rect, ccrs, cfeature):
    pc = ccrs.PlateCarree()
    ax = fig.add_axes(rect, projection=pc)
    ax.set_extent(EXTENT, crs=pc)
    ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor=COLORS["land"], edgecolor="none", zorder=0)
    ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor=COLORS["ocean"], zorder=0)
    return ax, pc


def overlay(ax, pc, cfeature):
    ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor=COLORS["text_2"], linewidth=0.5,
                   facecolor="none", zorder=3)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), edgecolor=COLORS["text_2"], linewidth=0.5, zorder=3)
    for lon, lat in CITIES.values():
        ax.plot(lon, lat, "o", ms=3.5, color="black", mec="white", mew=0.8, transform=pc, zorder=5)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "socal" / "socal5_heat_fire_outlook.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from shapely.geometry import shape

    apply_style(args.theme)
    fig = plt.figure(figsize=(13, 9.0))
    w, gap, x0 = 0.225, 0.015, 0.035

    # --- fire potential, 4 months -------------------------------------------------------
    fire = [load_fire(k, args.refresh) for k in range(4)]
    issued = fire[0]["features"][0]["properties"]["Updatetime"]          # e.g. "October 2026"
    m0, y0 = MONTHS.index(issued.split()[0]), int(issued.split()[1])
    fire_summary = []
    for k, gj in enumerate(fire):
        ax, pc = base_map(fig, [x0 + k * (w + gap), 0.47, w, 0.27], ccrs, cfeature)
        cats = {}
        for f in gj["features"]:
            cat = f["properties"]["FirePotent"]
            cats[f["properties"]["PSANAME"]] = cat
            g = shape(f["geometry"])
            ax.add_geometries([g], crs=pc, facecolor=FIRE_COLORS.get(cat) or "none", alpha=0.75,
                              edgecolor=COLORS["text"], linewidth=0.5, zorder=2)
        overlay(ax, pc, cfeature)
        m = (m0 + k) % 12
        ax.set_title(f"{MONTHS[m]} {y0 + (m0 + k) // 12}", fontsize=13, loc="left", pad=6, color=COLORS["text"])
        above = sorted(n for n, c in cats.items() if c == "Above")
        fire_summary.append((MONTHS[m], above))
    fig.text(x0, 0.775, "Significant wildland fire potential (NIFC Predictive Services)", fontsize=14,
             fontweight="bold", color=COLORS["text"])
    fig.legend(handles=[Patch(facecolor=FIRE_COLORS["Above"], alpha=0.75, label="Above normal"),
                        Patch(facecolor="none", edgecolor=COLORS["text"], label="Normal"),
                        Patch(facecolor=FIRE_COLORS["Below"], alpha=0.75, label="Below normal")],
               loc="lower right", bbox_to_anchor=(0.97, 0.765), ncol=3, fontsize=10.5, labelcolor=COLORS["text_2"])

    # --- temperature outlook, 4 seasons ---------------------------------------------------
    temp = load_leads("temp", args.refresh)
    t_issued = next(iter(temp.values()))[1]
    temp_summary = []
    for k, lead in enumerate(list(temp)[:4]):
        code, _, valid, polys = temp[lead]
        ax, pc = base_map(fig, [x0 + k * (w + gap), 0.10, w, 0.27], ccrs, cfeature)
        for cat, prob, geom in sorted(polys, key=lambda p: p[1]):
            if cat in ("Above", "Below"):
                i = max(j for j, b in enumerate(BANDS) if prob >= b)
                ax.add_geometries([geom], crs=pc, facecolor=SHADES[("temp", cat)][i], edgecolor="none", zorder=2)
        overlay(ax, pc, cfeature)
        ax.set_title(season_text(code, valid), fontsize=13, loc="left", pad=6, color=COLORS["text"])
        temp_summary.append((season_text(code, valid), *odds_at(polys, *CITIES["Los Angeles"])))
    fig.text(x0, 0.405, f"Probability of above-normal temperature (NOAA CPC, issued {t_issued:%B %-d, %Y})",
             fontsize=14, fontweight="bold", color=COLORS["text"])
    fig.legend(handles=[Patch(color=SHADES[("temp", "Above")][i], label=f"{BANDS[i]}–{BANDS[i + 1]}%")
                        for i in range(3)] + [Patch(facecolor=COLORS["land"], label="Equal chances")],
               loc="upper left", bbox_to_anchor=(0.03, 0.095), ncol=4, fontsize=10.5, labelcolor=COLORS["text_2"])

    n_above = sum(bool(a) for _, a in fire_summary)
    fire_line = ("Fire potential is near normal across Southern California for all four months"
                 if n_above == 0 else
                 "Above-normal fire potential: " + "; ".join(f"{m} ({', '.join(a)})" for m, a in fire_summary if a))
    warm = [s for s, c, p in temp_summary if c == "Above"]
    temp_line = (f"Above-normal temperatures are favoured for {' and '.join(warm)}" if warm
                 else "No season is favoured warmer than normal")
    add_title(fig, "Official heat and wildfire outlook for Southern California",
              f"{fire_line} ({issued} outlook). These are probabilities,\nnot forecasts of specific events. "
              f"{temp_line}.")
    add_source(fig, "Data: National Interagency Fire Center Predictive Services monthly outlook (Southern California "
               "Geographic Area); NOAA Climate Prediction Center 3-month temperature outlook.")
    save(fig, args.out,
         alt=f"Maps of the official Southern California outlook. Fire potential ({issued}): "
             + "; ".join(f"{m}: " + (", ".join(a) + " above normal" if a else "normal") for m, a in fire_summary)
             + ". Los Angeles temperature outlook: " + "; ".join(
                 f"{s}: " + (f"{p:.0f}%+ chance above normal" if c == "Above" else "equal chances" if c == "EC"
                             else f"{p:.0f}%+ chance below normal") for s, c, p in temp_summary) + ".")


if __name__ == "__main__":
    main()
