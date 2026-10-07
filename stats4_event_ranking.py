"""
Stats 4 — "How does this El Niño rank?"

Every El Niño since 1950 from NOAA's RONI, using NOAA's own rule: at least five
overlapping 3-month seasons in a row at +0.5 °C or more. Three measures:
  * peak strength  — highest 3-month value
  * length         — months from first to last season above +0.5
  * total warmth   — sum of all values above +0.5 (strength × duration), a
                     rough measure of how much extra heat the event carried
The current event is completed with NOAA's forecast middle estimate (hatched).

    python stats4_event_ranking.py
    python stats4_event_ranking.py --top 15
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from enso_common import (FIG_DIR, COLORS, add_source, add_title, apply_style, event_label, find_events,
                         load_cpc_outlook, load_roni, save)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=12, help="how many events to show")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "stats" / "stats4_event_ranking.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    roni = load_roni(refresh=args.refresh)
    fc = load_cpc_outlook(args.refresh)

    # observed record + NOAA's forecast median for the seasons not yet observed
    future = fc.loc[fc.index > roni.index[-1], "p50"]
    combined = pd.concat([roni, future])
    is_fc = pd.Series(False, index=combined.index)
    is_fc[future.index] = True

    rows = []
    for ev in find_events(combined):
        above = ev - 0.5
        rows.append(dict(name=event_label(ev), peak=ev.max(), months=len(ev), total=above.sum(),
                         forecast=bool(is_fc[ev.index].any()),
                         ongoing_hi=fc.loc[fc.index.isin(ev.index), "p95"].max() if is_fc[ev.index].any() else np.nan,
                         ongoing_lo=fc.loc[fc.index.isin(ev.index), "p5"].max() if is_fc[ev.index].any() else np.nan))
    df = pd.DataFrame(rows).sort_values("peak", ascending=False).head(args.top).iloc[::-1]

    fig, axes = plt.subplots(1, 3, figsize=(13, 0.48 * len(df) + 2.8), sharey=True,
                             gridspec_kw=dict(width_ratios=[1.25, 1, 1], wspace=0.12))
    fig.subplots_adjust(top=1 - 1.75 / (0.48 * len(df) + 2.8), bottom=0.6 / (0.48 * len(df) + 2.8) + 0.04,
                        left=0.12, right=0.98)
    y = np.arange(len(df))
    panels = [("peak", "Peak strength (°C)", "{:+.1f}"), ("months", "How long (months)", "{:.0f}"),
              ("total", "Total extra warmth (°C × months)", "{:.0f}")]
    for ax, (col, title, fmt) in zip(axes, panels):
        for yi, (_, r) in zip(y, df.iterrows()):
            cur = r["forecast"]
            ax.barh(yi, r[col], height=0.66, color=COLORS["el_nino"] if cur else COLORS["neutral"],
                    hatch="///" if cur else None, edgecolor=COLORS["surface"] if cur else "none", linewidth=0)
            if cur and col == "peak":
                ax.plot([r["ongoing_lo"], r["ongoing_hi"]], [yi, yi], color=COLORS["text"], lw=1.6)
                for v in (r["ongoing_lo"], r["ongoing_hi"]):
                    ax.plot([v, v], [yi - 0.18, yi + 0.18], color=COLORS["text"], lw=1.6)
            x_lbl = r["ongoing_hi"] if (cur and col == "peak") else r[col]   # clear of the range line
            ax.text(x_lbl, yi, " " + fmt.format(r[col]), va="center", ha="left", fontsize=11,
                    color=COLORS["text"] if cur else COLORS["text_2"],
                    fontweight="bold" if cur else "normal")
        ax.set_title(title, fontsize=13.5, loc="left", pad=10)
        ax.xaxis.grid(True)
        ax.set_axisbelow(True)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.set_xlim(0, df[col].max() * 1.25 if col != "peak" else max(df["peak"].max(), df["ongoing_hi"].max()) * 1.18)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([n + ("\n(forecast)" if f else "") for n, f in zip(df["name"], df["forecast"])],
                            fontsize=12)
    for t, f in zip(axes[0].get_yticklabels(), df["forecast"]):
        if f:
            t.set_fontweight("bold")
            t.set_color(COLORS["text"])

    cur = df[df["forecast"]]
    rank = int((df["peak"] > cur["peak"].iloc[0]).sum()) + 1 if len(cur) else None
    headline = (f"If NOAA's forecast holds, {cur['name'].iloc[0]} would be the strongest El Niño on record"
                if rank == 1 else "How does this El Niño rank?") if len(cur) else "The strongest El Niños since 1950"
    add_title(fig, headline,
              f"The {len(df)} strongest El Niños since 1950, ranked by peak. Red hatched = this event, finished "
              "with NOAA's middle forecast; the thin line\nshows NOAA's likely range for its peak. "
              "Total extra warmth combines strength and length.")
    add_source(fig, f"Data: NOAA CPC Relative Oceanic Niño Index (RONI) and official RONI outlook "
               f"({fc.attrs['issued']}). Event = 5+ overlapping seasons at +0.5 °C or more.")
    save(fig, args.out,
         alt=f"Ranked bar charts of the {len(df)} strongest El Niños since 1950 by peak strength, length in "
             "months and total extra warmth. " + "; ".join(
                 f"{r['name']}: peak {r['peak']:+.1f} °C, {r['months']} months"
                 + (" (forecast)" if r["forecast"] else "") for _, r in df.iloc[::-1].iterrows()) + ".")


if __name__ == "__main__":
    main()
