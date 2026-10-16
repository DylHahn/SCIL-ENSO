"""
Animation 6 — Layers of warm water in the equatorial Pacific: how much water is warmer than 20,
24, 26, 28 and 29 °C, month by month, for 2026, the past very strong El Niños and normal

Left: depth–longitude sections along the equator (2°S–2°N, 5–205 m) from NCEP GODAS, coloured
by temperature layer: 20–24, 24–26, 26–28, 28–29 and above 29 °C. Water above about 28 °C is
warm enough to sustain deep atmospheric convection, so the upper layers show the hottest water
pooling.
Right: the volume of water in each layer over 5°S–5°N, 120°E–80°W (the warm water volume box
used by NOAA PMEL), in 10¹⁴ m³; the full bar is the warm water volume above 20 °C.

Months run from July of the year before onset to the latest GODAS month. Frames are interpolated
between months for smooth playback.

    python anim_warm_layers.py
"""
import argparse
import calendar

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

from anim_warm_water import R_EARTH, WWV_BOX, d20, load_temps, monthly_normal
from enso_anim import AnimationFrames, interpolate_months
from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, join_and, lon_label

NOW = 2026
ISOTHERMS = [20, 24, 26, 28, 29]                          # lower edges of the layers, °C
LAYER_NAMES = ["20–24 °C", "24–26 °C", "26–28 °C", "28–29 °C", "above 29 °C"]
EQ = (-2, 2)
LON_MIN = 130


def layer_colors():
    """The site's turbo scale (12–31 °C, as in the upper-ocean animation) sampled in each layer,
    with a dark blue for water below 20 °C."""
    cmap = plt.get_cmap("turbo")
    mid = [22, 25, 27, 28.5, 30]
    return ["#1b2a5a"] + [cmap((t - 12) / (31 - 12)) for t in mid]


def volumes(temps, lat, lon, depths):
    """(time, layer) volume in 10¹⁴ m³ of water in each layer over the PMEL box."""
    la = (lat >= WWV_BOX["lat"][0]) & (lat <= WWV_BOX["lat"][1])
    lo = (lon >= WWV_BOX["lon"][0]) & (lon <= WWV_BOX["lon"][1])
    sub = temps[:, :, la][:, :, :, lo]
    dlat, dlon = np.deg2rad(np.abs(np.diff(lat).mean())), np.deg2rad(np.abs(np.diff(lon).mean()))
    area = R_EARTH ** 2 * np.cos(np.deg2rad(lat[la]))[:, None] * dlat * dlon
    above = np.stack([np.nansum(d20(sub, depths, th) * area, axis=(-2, -1)) / 1e14 for th in ISOTHERMS], axis=1)
    return above - np.concatenate([above[:, 1:], np.zeros((len(above), 1))], axis=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--compare", type=int, nargs="+", default=[2015, 1997, 1982])
    ap.add_argument("--steps", type=int, default=4, help="interpolated frames per month")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "anim" / "anim_warm_layers.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    span = pd.date_range(f"{NOW - 1}-07-01", f"{NOW}-12-01", freq="MS")
    temps, months, lat, lon, depths = load_temps(span, args.refresh)
    offsets = [(m.year - NOW, m.month) for m in months]
    rows = [(str(NOW), temps)]
    for y in args.compare:
        t, got, _, _, _ = load_temps([pd.Timestamp(y + dy, mo, 1) for dy, mo in offsets])
        assert len(got) == len(months), f"GODAS months missing for {y}"
        rows.append((str(y), t))
    normal = monthly_normal([mo for _, mo in offsets])
    rows.append(("Normal (1991–2020)", normal))
    n = len(months)

    eq = (lat >= EQ[0]) & (lat <= EQ[1])
    west = lon >= LON_MIN                                                      # east of the Maritime Continent
    sections = [np.nanmean(t[:, :, eq, :], axis=2)[:, :, west] for _, t in rows]   # (time, depth, lon)
    vols = [volumes(t, lat, lon, depths) for _, t in rows]                     # (time, layer)
    lon = lon[west]

    colors = layer_colors()
    cmap = ListedColormap(colors)
    bounds = [0] + ISOTHERMS + [40]
    norm = BoundaryNorm(bounds, cmap.N)

    top_in, row_in, sec_in, bottom_in = 1.95, 2.45, 1.95, 1.75
    H = top_in + row_in * len(rows) + bottom_in
    fig = plt.figure(figsize=(13, H))
    vmax = max(float(v.sum(axis=1).max()) for v in vols) * 1.08
    sec_axes, bar_axes, labels, bars, totals = [], [], [], [], []
    for k, (name, _) in enumerate(rows):
        y0 = 1 - (top_in + row_in * k + sec_in) / H
        ax = fig.add_axes([0.07, y0, 0.62, sec_in / H])
        ax.set_facecolor("black")
        ax.set_xlim(lon.min(), lon.max())
        ax.set_ylim(depths.max(), depths.min())
        ax.set_yticks([50, 100, 150, 200])
        ax.set_ylabel("Depth (m)", fontsize=10)
        ax.xaxis.set_major_formatter(FuncFormatter(lon_label))
        ax.set_xticks([140, 160, 180, 200, 220, 240, 260])
        if k < len(rows) - 1:
            ax.set_xticklabels([])
        cur = k == 0
        ax.set_title(name, fontsize=14, fontweight="bold", loc="left", pad=5,
                     color=COLORS["el_nino"] if cur else COLORS["text"])
        labels.append(ax.text(1.0, 1.03, "", transform=ax.transAxes, ha="right", va="bottom", fontsize=12.5,
                              fontweight="bold", color=COLORS["text"]))
        for sp in ax.spines.values():
            sp.set_visible(cur)
            sp.set_edgecolor(COLORS["el_nino"])
            sp.set_linewidth(2)
        sec_axes.append(ax)

        bx = fig.add_axes([0.73, y0 + 0.25 * sec_in / H, 0.24, 0.5 * sec_in / H])
        bx.set_xlim(0, vmax)
        bx.set_ylim(-0.5, 0.5)
        bx.set_yticks([])
        bx.spines[["left", "top", "right"]].set_visible(False)
        bx.tick_params(axis="x", labelsize=9.5)
        if k < len(rows) - 1:
            bx.set_xticklabels([])
        else:
            bx.set_xlabel("Volume, 5°S–5°N (10$^{14}$ m³)", fontsize=10)
        bx.xaxis.grid(True, color=COLORS["grid"], lw=0.6)
        bx.set_axisbelow(True)
        bars.append(bx.barh([0] * len(ISOTHERMS), [0] * len(ISOTHERMS), left=[0] * len(ISOTHERMS), height=0.8,
                            color=colors[1:][::-1], edgecolor=COLORS["surface"], linewidth=1))
        totals.append(bx.text(0, 0.62, "", fontsize=10.5, color=COLORS["text_2"], va="bottom"))
        bar_axes.append(bx)

    sec_axes[0].text(0.0, 1.32, "← West (Asia)", transform=sec_axes[0].transAxes, fontsize=10.5,
                     color=COLORS["text_2"])
    sec_axes[0].text(1.0, 1.32, "East (South America) →", transform=sec_axes[0].transAxes, fontsize=10.5,
                     color=COLORS["text_2"], ha="right")
    handles = ([Patch(color=c, label=nm) for c, nm in zip(colors[1:], LAYER_NAMES)][::-1]
               + [Patch(color=colors[0], label="below 20 °C")])
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.42 / H), ncol=6, fontsize=10.5,
               labelcolor=COLORS["text_2"], handlelength=1.4, columnspacing=1.1, frameon=False)
    add_title(fig, f"Layers of warm water in the equatorial Pacific: {NOW} compared with "
                   f"{join_and(str(y) for y in args.compare)}",
              "Slices along the equator, coloured by temperature layer; water above about 28 °C is warm enough to "
              "drive heavy tropical rainfall.\nBars: the volume of water in each layer between 5°S and 5°N.")
    add_source(fig, "Data: NCEP GODAS (NOAA), monthly, 1° × 10 m to 205 m. Sections: 2°S–2°N; volumes: 5°S–5°N, "
               "120°E–80°W. Normal: 1991–2020 mean temperature. Frames interpolated.")

    seqs = [interpolate_months(s, args.steps) for s in sections]
    vseqs = [interpolate_months(v, args.steps) for v in vols]
    drawn = [[] for _ in rows]
    frames = AnimationFrames(fig, dpi=110)
    for i, pos in enumerate(seqs[0][1]):
        kk = int(round(pos))
        dy, mo = offsets[kk]
        for r, ax in enumerate(sec_axes):
            for art in drawn[r]:
                art.remove()
            field = seqs[r][0][i]
            cf = ax.contourf(lon, depths, np.where(np.isfinite(field), field, 0), levels=bounds, cmap=cmap, norm=norm)
            drawn[r] = [cf]
            v = vseqs[r][0][i]
            left = 0.0
            for rect, w in zip(bars[r], v[::-1]):                      # warmest layer first, from the left
                rect.set_x(left)
                rect.set_width(w)
                left += w
            totals[r].set_text(f"total {v.sum():.1f}  ·  above 28 °C {v[3:].sum():.1f}")
            year = rows[r][0]
            labels[r].set_text(f"{calendar.month_name[mo]} {int(year) + dy}" if r < len(rows) - 1
                               else calendar.month_name[mo])
        frames.grab(800 if abs(pos - round(pos)) < 1e-9 else 90)
    frames.durations[-1] = 3500

    last = [v[-1] for v in vols]
    names = [nm for nm, _ in rows]
    frames.save(args.out, quality=86,
                alt=f"Animated equatorial Pacific sections coloured by temperature layer from {months[0]:%B %Y} to "
                    f"{months[-1]:%B %Y} for {join_and(names)}, with bars of warm water volume by layer. In "
                    f"{months[-1]:%B}, water above 28 °C between 5°S and 5°N totalled "
                    + join_and(f"{v[3:].sum():.1f} × 10¹⁴ m³ in {nm}" for nm, v in zip(names, last))
                    + "; water above 20 °C totalled "
                    + join_and(f"{v.sum():.1f}" for v in last) + " × 10¹⁴ m³ respectively.")


if __name__ == "__main__":
    main()
