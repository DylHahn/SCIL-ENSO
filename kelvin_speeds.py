"""
Kelvin waves 2 — How fast the Kelvin waves crossed the Pacific, 2017 to the present

Every downwelling Kelvin wave traced in NOAA's daily satellite sea level along the equator since
2017 (see anim_kelvin.py: traced from 150°E to 95°W, then measured from the day the wave signal
peaks at each longitude), with its speed (m/s) and the days it took to cross. The background marks
NOAA's ENSO state (RONI) at the time. Theory puts the first, fastest mode of equatorial Kelvin waves
at about 2.5–3 m/s in the Pacific; slower waves belong to higher modes or are slowed by the currents
they travel through.

    python kelvin_speeds.py
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from anim_kelvin import M_PER_DEG, X0, X1, kelvin_waves
from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, join_and, load_roni, save

NOW = 2026
GROUPS = {f"{NOW}/{NOW + 1}": (pd.Timestamp(f"{NOW - 1}-10-01"), None, COLORS["el_nino"]),
          "2023/2024": (pd.Timestamp("2022-10-01"), pd.Timestamp("2024-01-31"), "#9085e9")}
CROSS_M = (X1 - X0) * M_PER_DEG
MIN_R2 = 0.7                                              # fits below this are drawn faintly


def days_to_cross(v):
    with np.errstate(divide="ignore"):
        return CROSS_M / (np.asarray(v, float) * 86400.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "kelvin" / "kelvin_speeds.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    _, _, waves = kelvin_waves(args.refresh)
    roni = load_roni(refresh=args.refresh)

    def group(t):
        for name, (a, b, col) in GROUPS.items():
            if t >= a and (b is None or t <= b):
                return name, col
        return None, COLORS["neutral"]

    fig = plt.figure(figsize=(13, 7.6))
    ax = fig.add_axes([0.07, 0.15, 0.82, 0.6])
    # ENSO state behind the points
    r = roni.loc["2017-01":]
    for t, v in r.items():
        if abs(v) >= 0.5:
            ax.axvspan(t - pd.Timedelta(days=15), t + pd.Timedelta(days=16), lw=0, zorder=0,
                       color=COLORS["el_nino"] if v > 0 else COLORS["la_nina"], alpha=0.13)
    ax.axhspan(2.5, 3.0, color=COLORS["text_2"], alpha=0.12, lw=0, zorder=0)
    ax.text(pd.Timestamp("2017-03-01"), 4.5, "Grey band: typical speed of first-mode Kelvin waves, 2.5–3 m/s",
            fontsize=10.5, color=COLORS["text_2"], va="top")
    for start, v, amp, end, se, r2 in waves:
        mid = start + (end - start) / 2
        name, col = group(mid)
        strong = r2 >= MIN_R2
        ax.errorbar(mid, v, yerr=1.96 * se, fmt="none", ecolor=col, elinewidth=1.4, alpha=0.9 if strong else 0.35,
                    zorder=3)
        ax.plot(mid, v, "o", ms=6 + 1.6 * amp, color=col if strong else "none", mec=col, mew=1.6,
                alpha=1 if strong else 0.5, zorder=4)
    ax.set_ylim(1.2, 4.6)
    ax.set_xlim(pd.Timestamp("2017-01-01"), pd.Timestamp(f"{NOW}-12-31"))
    ax.set_ylabel("Speed (m/s)")
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    sec = ax.secondary_yaxis("right", functions=(days_to_cross, lambda d: days_to_cross(d)))
    sec.set_yticks([30, 40, 50, 60, 80, 100])
    sec.set_ylabel("Days to cross 150°E → 95°W")
    sec.tick_params(colors=COLORS["text_2"])
    ax.set_xlabel("Date the wave was halfway across")

    handles = [Line2D([], [], marker="o", ls="none", ms=9, color=c, label=f"Waves of the {n} El Niño")
               for n, (_, _, c) in GROUPS.items()]
    handles += [Line2D([], [], marker="o", ls="none", ms=9, color=COLORS["neutral"], label="Other waves"),
                Line2D([], [], marker="o", ls="none", ms=9, mfc="none", mec=COLORS["neutral"], mew=1.6,
                       label="Less clear wave (fit r² < 0.7)"),
                Patch(color=COLORS["el_nino"], alpha=0.25, label="El Niño"),
                Patch(color=COLORS["la_nina"], alpha=0.25, label="La Niña")]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.06, 0.765), ncol=3, fontsize=10.5,
               frameon=False, labelcolor=COLORS["text_2"], handlelength=1.4, columnspacing=1.4)

    cur = [w for w in waves if group(w[0] + (w[3] - w[0]) / 2)[0] == f"{NOW}/{NOW + 1}"]
    others = [w for w in waves if w not in cur and w[5] >= MIN_R2]
    v_now = np.array([w[1] for w in cur])
    v_all = np.array([w[1] for w in others])
    add_title(fig, "How fast the Kelvin waves crossed the Pacific, 2017–2026",
              f"Each dot is one Kelvin wave, measured from daily satellite sea level (size: how much it raised sea "
              f"level; bars: 95% range of the speed). The {len(cur)} waves since\nOctober {NOW - 1} crossed at "
              f"{v_now.min():.1f}–{v_now.max():.1f} m/s (median {np.median(v_now):.1f} m/s, about "
              f"{days_to_cross(np.median(v_now)):.0f} days to cross), against a median of "
              f"{np.median(v_all):.1f} m/s for the other clear waves since 2017.")
    add_source(fig, "Data: NOAA blended satellite altimetry (CoastWatch ERDDAP), 1°S–1°N; ENSO state: NOAA CPC RONI "
               "(±0.5 °C). Waves traced as eastward paths of +3 cm or more, then fitted to each longitude's peak.")
    save(fig, args.out,
         alt=f"Scatter chart of the speed of every Kelvin wave traced along the equatorial Pacific since 2017. The "
             f"{len(cur)} waves of the {NOW}/{NOW + 1} El Niño travelled at "
             + join_and(f"{w[1]:.1f}" for w in cur) + f" m/s, median {np.median(v_now):.1f} m/s; other clear waves "
             f"since 2017 had a median of {np.median(v_all):.1f} m/s.")


if __name__ == "__main__":
    main()
