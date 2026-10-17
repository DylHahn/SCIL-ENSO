"""
Animation 3 — How the 2026 El Niño has developed compared with every El Niño since 1950

Monthly anomaly time series for every El Niño since 1950, aligned on January of the onset
year and drawn month by month, so that all events advance together through the calendar:
  (a) Niño 3.4 SST anomaly        — ERSST v5
  (b) Niño 1+2 SST anomaly        — ERSST v5 (coastal Peru and Ecuador)
  (c) Upper-200 m temperature anomaly, 2°S–2°N, 180°–80°W — GODAS (1980 onward)
The run first advances every event to the latest month observed in 2026, ranking the current
event against all past events at the same stage, and then completes the past events' paths
to show how they evolved afterwards. Anomalies relative to the 1991–2020 monthly climatology.

    python anim_timeseries.py
"""
import argparse
import calendar

import numpy as np
import matplotlib.pyplot as plt

from enso_anim import AnimationFrames
from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, find_events, load_roni
from enso_stats import load_gridded
from event_timeseries import N_MONTHS, NOW, aligned, box_series, godas_heat_series, onset_year

# the very strong El Niños before 2026, in the site's fixed colour order (1972 predates GODAS)
HIGHLIGHT = {2015: "#c98500", 1997: "#199e70", 1982: "#3987e5", 1972: "#9085e9"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--steps", type=int, default=4, help="interpolated frames per month")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "anim" / "anim_timeseries.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    past_years = sorted({onset_year(e) for e in find_events(load_roni(refresh=args.refresh))} - {NOW})
    past_years = [y for y in past_years if y < NOW]
    sst = load_gridded("sst", args.refresh)
    panels = [("(a) Niño 3.4 sea surface temperature", "central equatorial Pacific · ERSST v5",
               box_series(sst, (-5, 5), (190, 240))),
              ("(b) Niño 1+2 sea surface temperature", "coastal Peru and Ecuador · ERSST v5",
               box_series(sst, (-10, 0), (270, 280))),
              ("(c) Upper-ocean (0–200 m) temperature", "equator, 180°–80°W · GODAS, 1980 onward",
               godas_heat_series())]

    fig, axes = plt.subplots(1, 3, figsize=(13, 7.4), sharex=True)
    fig.subplots_adjust(top=0.70, bottom=0.15, left=0.06, right=0.965, wspace=0.24)
    x = np.arange(N_MONTHS, dtype=float)
    state = []
    for ax, (title, sub, s) in zip(axes, panels):
        years = [y for y in past_years if np.isfinite(aligned(s, y)[:12]).all()]
        data = {y: aligned(s, y) for y in years}
        cur = aligned(s, NOW)
        last = int(np.flatnonzero(np.isfinite(cur))[-1])
        others = {y: ax.plot([], [], color=COLORS["neutral"], lw=0.9, alpha=0.55, zorder=1)[0]
                  for y in years if y not in HIGHLIGHT}
        hi = {y: ax.plot([], [], color=c, lw=2.0, zorder=3)[0] for y, c in HIGHLIGHT.items() if y in data}
        hi_lbl = {y: ax.text(0, 0, "", fontsize=10.5, fontweight="bold", color=COLORS["text_2"], va="center",
                             zorder=6) for y in hi}
        now_line, = ax.plot([], [], color=COLORS["el_nino"], lw=3.4, zorder=4, solid_capstyle="round")
        now_dot, = ax.plot([], [], "o", ms=8, color=COLORS["el_nino"], mec=COLORS["surface"], mew=1.5, zorder=5)
        now_lbl = ax.text(0, 0, "", fontsize=12, fontweight="bold", color=COLORS["text"], va="bottom", zorder=7)
        cursor = ax.axvline(0, color=COLORS["muted"], lw=0.8, ls=(0, (3, 2)))
        rank = ax.text(0.02, 0.97, "", transform=ax.transAxes, fontsize=11, color=COLORS["text"], va="top",
                       linespacing=1.35, bbox=dict(boxstyle="round,pad=0.4", fc=COLORS["surface"], ec="none",
                                                   alpha=0.85), zorder=8)
        ax.axhline(0, color=COLORS["text_2"], lw=0.8)
        allv = np.concatenate([v for v in data.values()] + [cur])
        lo, hi_v = np.nanmin(allv), np.nanmax(allv)
        ax.set_ylim(lo - 0.3, hi_v + 0.15 * (hi_v - lo) + 0.6)       # room for the ranking box
        ax.set_xlim(0, N_MONTHS - 1)
        ax.set_xticks([0, 3, 6, 9, 12, 15, 18, 21])
        ax.set_xticklabels(["Jan\n1st year", "Apr", "Jul", "Oct", "Jan\n2nd year", "Apr", "Jul", "Oct"], fontsize=10)
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
        ax.set_title(title, fontsize=13, loc="left", pad=20)
        ax.text(0, 1.02, f"{sub} · {len(years)} past events", transform=ax.transAxes, fontsize=9.5,
                color=COLORS["text_2"], va="bottom")
        state.append(dict(data=data, cur=cur, last=last, others=others, hi=hi, hi_lbl=hi_lbl, now_line=now_line,
                          now_dot=now_dot, now_lbl=now_lbl, cursor=cursor, rank=rank, ax=ax))
    axes[0].set_ylabel("Anomaly (°C), relative to 1991–2020")

    def partial(y, t):
        """Values for months 0..floor(t), plus a linearly interpolated head at t."""
        k = int(np.floor(t))
        xs, ys = list(x[:k + 1]), list(y[:k + 1])
        if t > k and k + 1 < len(y) and np.isfinite(y[k + 1]):
            f = t - k
            xs.append(t)
            ys.append((1 - f) * y[k] + f * y[k + 1])
        return np.array(xs), np.array(ys)

    def draw(t, phase2):
        for st in state:
            tc = min(t, st["last"])                                    # 2026 stops at its latest month
            for y, ln in st["others"].items():
                ln.set_data(*partial(st["data"][y], t))
            heads = []
            for y, ln in st["hi"].items():
                xs, ys = partial(st["data"][y], t)
                ln.set_data(xs, ys)
                heads.append((y, xs[-1], ys[-1]))
            xs, ys = partial(st["cur"], tc)
            st["now_line"].set_data(xs, ys)
            st["now_dot"].set_data([xs[-1]], [ys[-1]])
            st["now_lbl"].set_position((xs[-1] + 0.25, ys[-1] + 0.08))
            st["now_lbl"].set_text(f"{NOW}/{NOW + 1} {ys[-1]:+.1f}")
            # year labels at the line heads, nudged apart vertically so they do not overlap
            span = np.diff(st["ax"].get_ylim())[0]
            placed = [ys[-1] + 0.03 * span] if not phase2 else []      # keep clear of the 2026 label
            for y, hx, hy in sorted(heads, key=lambda h: h[2]):
                ly = hy
                while any(abs(ly - p) < 0.05 * span for p in placed):
                    ly += 0.02 * span
                placed.append(ly)
                st["hi_lbl"][y].set_position((hx + 0.25, ly))
                st["hi_lbl"][y].set_text(f"{y}/{y + 1}")
            st["cursor"].set_xdata([tc if not phase2 else st["last"]] * 2)
            # ranking at the current month (whole months only, so the text does not flicker)
            k = int(round(tc))
            same = np.array([v[k] for v in st["data"].values()])
            same = same[np.isfinite(same)]
            val = st["cur"][k]
            r = int((same > val).sum()) + 1
            mon = MONTHS[k % 12]
            if r == 1:
                txt = f"{mon} {NOW + k // 12}: {val:+.1f} °C\nwarmest of {len(same) + 1} events at this stage"
            else:
                txt = f"{mon} {NOW + k // 12}: {val:+.1f} °C\n{ordinal(r)} of {len(same) + 1} events at this stage"
            st["rank"].set_text(txt)

    from matplotlib.lines import Line2D
    handles = ([Line2D([], [], color=COLORS["el_nino"], lw=3.4, label=f"{NOW}/{NOW + 1}")]
               + [Line2D([], [], color=c, lw=2, label=f"{y}/{y + 1}") for y, c in HIGHLIGHT.items()]
               + [Line2D([], [], color=COLORS["neutral"], lw=1, label="Other El Niños since 1950")])
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.055, 0.775), ncol=6, fontsize=10.5,
               labelcolor=COLORS["text_2"], handlelength=1.8, columnspacing=1.2)
    status = fig.text(0.965, 0.775 + 0.012, "", ha="right", va="bottom", fontsize=11.5, fontweight="bold",
                      color=COLORS["text"])
    add_title(fig, f"How the {NOW}/{NOW + 1} El Niño has developed compared with every El Niño since 1950",
              "Each line is one El Niño, aligned on January of the year it developed, so all events advance through "
              "the calendar together.\nThe box in each panel ranks the current event against every past event at "
              "the same stage.")
    add_source(fig, "Data: NOAA ERSST v5 and NCEP GODAS; events from NOAA CPC RONI (≥ 5 overlapping seasons at "
               "+0.5 °C or more). Anomalies relative to the 1991–2020 monthly climatology.")

    frames = AnimationFrames(fig, dpi=110)
    last_all = max(st["last"] for st in state)
    ts = np.arange(0, last_all + 1e-9, 1 / args.steps)
    for t in ts:
        status.set_text(f"{calendar.month_name[int(round(t)) % 12 + 1]} {NOW}")
        draw(t, False)
        whole = abs(t - round(t)) < 1e-9
        frames.grab(1400 if whole and round(t) == last_all else 450 if whole else 80)
    # phase 2: the past events continue; 2026 stays at its latest observation
    status.set_text("Past events continue →")
    for t in np.arange(last_all + 1 / args.steps, N_MONTHS - 1 + 1e-9, 1 / args.steps):
        draw(t, True)
        frames.grab(70)
    frames.durations[-1] = 4000

    summary = []
    for (title, _, _), st in zip(panels, state):
        k = st["last"]
        same = [v[k] for v in st["data"].values() if np.isfinite(v[k])]
        summary.append(f"{title[4:]}: {st['cur'][k]:+.1f} °C in {MONTHS[k]}, against a previous maximum of "
                       f"{max(same):+.1f} °C at the same stage")
    frames.save(args.out, quality=88,
                alt="Animated line charts in which every El Niño since 1950 advances month by month from January of "
                    "its onset year. " + "; ".join(summary) + ".")


if __name__ == "__main__":
    main()
