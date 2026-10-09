"""
SoCal 3 — "NOAA's official outlook for this winter"

NOAA Climate Prediction Center's seasonal outlook, zoomed to Southern
California: the chance that rain and temperature land above, near or below
normal. Maps for the core El Niño winter (Dec–Feb), plus a season-by-season
strip for Los Angeles. Read straight from CPC's published outlook files
(seasprcp_latest.zip / seastemp_latest.zip), so it updates with each monthly
release (third Thursday).

    python socal_outlook.py
    python socal_outlook.py --refresh        # after NOAA's monthly release
"""
import argparse
import glob
import re
import urllib.request
import zipfile

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch

from enso_common import FIG_DIR, COLORS, HERE, add_source, add_title, apply_style, save

OUTLOOK_DIR = HERE / "data" / "cpc_outlook"
URL = "https://ftp.cpc.ncep.noaa.gov/GIS/us_tempprcpfcst/seas{var}_latest.zip"
CITIES = {"Los Angeles": (-118.29, 34.02), "San Diego": (-117.18, 32.73),
          "Riverside": (-117.40, 33.95), "Santa Barbara": (-119.70, 34.42)}
# label offsets (degrees) and alignment so neighbouring cities don't collide
LABEL_POS = {"Los Angeles": (-0.12, 0.12, "right"), "San Diego": (0.12, 0.08, "left"),
             "Riverside": (0.12, -0.18, "left"), "Santa Barbara": (0.0, 0.14, "center")}
EXTENT = [-124.5, -113.5, 31.3, 38.0]
MONTHS = "JFMAMJJASOND"


def season_text(code, valid):
    """('DJF', 'DJF 2026-2027') -> 'Dec 2026–Feb 2027'; ('OND', 'OND 2026') -> 'Oct–Dec 2026'."""
    years = valid.split()[-1].split("-")
    first, last = SEASON_NAMES.get(code, code).split("–") if code in SEASON_NAMES else (code, "")
    return f"{first} {years[0]}–{last} {years[-1]}" if len(years) > 1 else f"{first}–{last} {years[0]}"


SEASON_NAMES = {"OND": "Oct–Dec", "NDJ": "Nov–Jan", "DJF": "Dec–Feb", "JFM": "Jan–Mar", "FMA": "Feb–Apr",
                "MAM": "Mar–May"}
# fill colours by category and probability band (lower edge, %)
SHADES = {
    ("prcp", "Above"): ["#cfe8d9", "#8fd0ad", "#4fae80", "#2b8a5c", "#16653f"],
    ("prcp", "Below"): ["#f1dfbf", "#e2bf82", "#c99a4a", "#a8762a", "#7d5418"],
    ("temp", "Above"): ["#f7d2c8", "#efa592", "#e3705a", "#c9483a", "#9c2a22"],
    ("temp", "Below"): ["#d3e3f5", "#a3c6ec", "#6ea2dc", "#3f7cc4", "#22569a"],
}
BANDS = [33, 40, 50, 60, 70]


def fetch(var, refresh):
    z = OUTLOOK_DIR / f"seas{var}_latest.zip"
    if refresh or not z.exists():
        OUTLOOK_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {URL.format(var=var)} ... (~50 MB)")
        urllib.request.urlretrieve(URL.format(var=var), z)
    out = OUTLOOK_DIR / var
    if refresh or not out.exists():
        with zipfile.ZipFile(z) as f:
            f.extractall(out)
    return out


def load_leads(var, refresh):
    """{lead: (season code, issue date, [(cat, prob, geometry), ...])} for 3-month leads."""
    import cartopy.io.shapereader as shpreader
    leads = {}
    for path in glob.glob(str(fetch(var, refresh) / f"lead*_*_{var}.shp")):
        m = re.search(r"lead(\d+)_([A-Z]{3})_", path)
        if not m:
            continue                      # skips the 1-month 'lead14_Oct' file
        recs = list(shpreader.Reader(path).records())
        polys = [(r.attributes["Cat"], float(r.attributes["Prob"]), r.geometry) for r in recs]
        leads[int(m.group(1))] = (m.group(2), recs[0].attributes["Fcst_Date"],
                                  recs[0].attributes["Valid_Seas"], polys)
    return dict(sorted(leads.items()))


def odds_at(polys, lon, lat):
    """(category, probability band) of the most confident polygon containing the point."""
    from shapely.geometry import Point
    pt = Point(lon, lat)
    hits = [(p, c) for c, p, g in polys if g.contains(pt) and c in ("Above", "Below")]
    if not hits:
        return "EC", 33.0
    p, c = max(hits)
    return c, p


def shade(var, cat, prob):
    if cat not in ("Above", "Below"):
        return None
    i = max(k for k, b in enumerate(BANDS) if prob >= b)
    return SHADES[(var, cat)][i]


def phrase(var, cat, prob):
    if cat == "EC":
        return "equal chances"
    word = {("prcp", "Above"): "wetter", ("prcp", "Below"): "drier",
            ("temp", "Above"): "warmer", ("temp", "Below"): "cooler"}[(var, cat)]
    lo = max(b for b in BANDS if prob >= b)
    hi = next((b for b in BANDS if b > lo), 100)
    return f"{lo}–{hi}% chance {word}"     # CPC bands: 33% would be no tilt at all


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", default="DJF", help="season for the two maps (CPC code, e.g. DJF)")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--only", choices=["prcp", "temp"], help="show one variable (larger map)")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "socal" / "socal_outlook.png"))
    args = ap.parse_args()

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    apply_style(args.theme)
    variables = (args.only,) if args.only else ("prcp", "temp")
    data = {v: load_leads(v, args.refresh) for v in variables}
    issued = next(iter(data[variables[0]].values()))[1]
    pc = ccrs.PlateCarree()

    fig = plt.figure(figsize=(13, 10.4))
    for k, var in enumerate(variables):
        lead = next(l for l, v in data[var].items() if v[0] == args.season)
        code, _, valid, polys = data[var][lead]
        rect = [0.03 + k * 0.49, 0.33, 0.46, 0.46] if len(variables) > 1 else [0.12, 0.33, 0.76, 0.46]
        ax = fig.add_axes(rect, projection=ccrs.LambertConformal(
            central_longitude=-119, central_latitude=34.5))
        ax.set_extent(EXTENT, crs=pc)
        ax.add_feature(cfeature.OCEAN, facecolor=COLORS["ocean"], zorder=0)
        ax.add_feature(cfeature.LAND, facecolor=COLORS["land"], edgecolor="none", zorder=0)
        for cat, prob, geom in sorted(polys, key=lambda x: x[1]):     # low bands first, high on top
            col = shade(var, cat, prob)
            if col:
                ax.add_geometries([geom], crs=pc, facecolor=col, edgecolor="none", alpha=0.95, zorder=1)
        ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor=COLORS["text_2"], linewidth=0.6,
                       facecolor="none", zorder=2)
        ax.add_feature(cfeature.COASTLINE.with_scale("50m"), edgecolor=COLORS["text_2"], linewidth=0.6, zorder=2)
        for city, (lon, lat) in CITIES.items():
            ax.plot(lon, lat, "o", ms=5, color="black", mec="white", mew=1.2, transform=pc, zorder=4)
            dx, dy, ha = LABEL_POS[city]
            ax.text(lon + dx, lat + dy, city, transform=pc, fontsize=9.5, color="black", zorder=4, ha=ha,
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=1))
        cat, prob = odds_at(polys, *CITIES["Los Angeles"])
        label = "Rain" if var == "prcp" else "Temperature"
        ax.set_title(f"{label}, {season_text(code, valid)}", fontsize=15, loc="left",
                     pad=26, color=COLORS["text"])
        ax.text(0, 1.015, f"Southern California: {phrase(var, cat, prob)}", transform=ax.transAxes,
                fontsize=11.5, color=COLORS["text_2"], va="bottom")
        # legend: only the bands that actually appear inside the map window
        from shapely.geometry import box
        window = box(EXTENT[0], EXTENT[2], EXTENT[1], EXTENT[3])
        present = sorted({(c, max(i for i, b in enumerate(BANDS) if p >= b)) for c, p, g in polys
                          if c in ("Above", "Below") and g.intersects(window)})
        word = {("prcp", "Above"): "Wetter", ("prcp", "Below"): "Drier",
                ("temp", "Above"): "Warmer", ("temp", "Below"): "Cooler"}
        swatches = [Patch(color=SHADES[(var, c)][i], label=f"{word[(var, c)]}: "
                          f"{BANDS[i]}–{BANDS[i + 1] if i + 1 < len(BANDS) else 100}% chance")
                    for c, i in present]
        ax.legend(handles=swatches + [Patch(facecolor=COLORS["land"], edgecolor=COLORS["text_2"],
                                            label="Equal chances")],
                  loc="lower left", fontsize=9.5, ncol=1, frameon=True, facecolor=COLORS["surface"],
                  edgecolor="none", framealpha=0.85, labelcolor=COLORS["text"])

    # season-by-season strip for Los Angeles
    sax = fig.add_axes([0.03, 0.08, 0.94, 0.20])
    sax.axis("off")
    sax.set_xlim(0, 1)
    sax.set_ylim(0, 1)
    sax.text(0, 1.0, "Los Angeles, season by season", fontsize=14, fontweight="bold", color=COLORS["text"],
             va="top")
    leads = [l for l in data[variables[0]] if l <= 5]
    w = 1 / len(leads)
    for i, lead in enumerate(leads):
        x = i * w
        code, _, valid, _ = data[variables[0]][lead]
        sax.add_patch(FancyBboxPatch((x + 0.004, 0.0), w - 0.008, 0.78, boxstyle="round,pad=0,rounding_size=0.02",
                                     facecolor=COLORS["surface_2"], edgecolor="none", mutation_aspect=4))
        sax.text(x + 0.015, 0.68, season_text(code, valid), fontsize=12,
                 fontweight="bold", color=COLORS["text"], va="top")
        for j, var in enumerate(variables):
            if lead not in data[var]:
                continue
            cat, prob = odds_at(data[var][lead][3], *CITIES["Los Angeles"])
            col = shade(var, cat, prob) or COLORS["text_2"]
            y0 = 0.47 - j * 0.27
            sax.text(x + 0.015, y0, "Rain" if var == "prcp" else "Temperature", fontsize=10,
                     color=COLORS["text_2"], va="center")
            sax.text(x + 0.015, y0 - 0.12, phrase(var, cat, prob), fontsize=11.5, fontweight="bold",
                     color=col if cat != "EC" else COLORS["text_2"], va="center")

    what = {"prcp": "precipitation ", "temp": "temperature "}.get(args.only, "")
    add_title(fig, f"NOAA seasonal {what}outlook for Southern California",
              f"NOAA Climate Prediction Center outlook issued {issued:%B %-d, %Y}: probability of above-, near- "
              f"or below-normal conditions by season.\n“Equal chances” indicates no preferred category. For daily "
              "forecasts and warnings, consult the local National Weather Service office.")
    add_source(fig, "Data: NOAA Climate Prediction Center official 3-month outlooks (GIS files, "
               "seasprcp/seastemp_latest). Normal = 1991–2020.")
    la = {var: [(data[var][l][0], *odds_at(data[var][l][3], *CITIES["Los Angeles"])) for l in leads if l in data[var]]
          for var in variables}
    if args.only:
        word = "precipitation" if args.only == "prcp" else "temperature"
        save(fig, args.out,
             alt=f"Map of NOAA's {SEASON_NAMES.get(args.season, args.season)} {word} outlook for Southern "
                 f"California, issued {issued:%B %-d, %Y}. Los Angeles by season: " + "; ".join(
                     f"{SEASON_NAMES.get(c, c)}: {phrase(args.only, ca, p)}" for c, ca, p in la[args.only]) + ".")
        return
    save(fig, args.out,
         alt=f"Maps of NOAA's {SEASON_NAMES.get(args.season, args.season)} rain and temperature outlook for "
             f"Southern California, issued {issued:%B %-d, %Y}. Los Angeles by season: " + "; ".join(
                 f"{SEASON_NAMES.get(c, c)}: rain {phrase('prcp', ca, p)}, temperature {phrase('temp', ct, pt)}"
                 for (c, ca, p), (_, ct, pt) in zip(la["prcp"], la["temp"])) + ".")


if __name__ == "__main__":
    main()
