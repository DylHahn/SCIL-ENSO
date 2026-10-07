"""
Stats 5 — "How often does El Niño come back?"

From NOAA's RONI since 1950:
  * share of time spent in El Niño, La Niña and neutral conditions
  * years between the starts of one El Niño and the next (histogram)
  * the rhythm in the record (periodogram): which repeat times dominate

    python stats5_how_often.py
"""
import argparse

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from enso_common import (FIG_DIR, COLORS, add_source, add_title, apply_style, find_events, load_roni, save)


def periodogram(s, smooth=5):
    """Smoothed, Hann-windowed periodogram of a monthly series. Returns (period_years, relative power)."""
    x = s.values - s.values.mean()
    x = x * np.hanning(len(x))
    power = np.abs(np.fft.rfft(x)) ** 2
    freq = np.fft.rfftfreq(len(x), d=1 / 12)          # cycles per year
    power = np.convolve(power, np.ones(smooth) / smooth, mode="same")
    keep = freq > 0
    return 1 / freq[keep], power[keep] / power[keep].max()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "stats" / "stats5_how_often.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    roni = load_roni(refresh=args.refresh)
    el, la = find_events(roni, 0.5), find_events(roni, -0.5)
    n = len(roni)
    in_el = sum(len(e) for e in el) / n
    in_la = sum(len(e) for e in la) / n
    # whole percentages that add up to exactly 100
    pct_el, pct_la = round(100 * in_el), round(100 * in_la)
    pct_neutral = 100 - pct_el - pct_la
    starts = [e.index[0] for e in el]
    gaps = np.array([(b - a).days / 365.25 for a, b in zip(starts[:-1], starts[1:])])

    fig = plt.figure(figsize=(13, 8.6))
    # --- row 1: share of time -------------------------------------------------------
    tiles = [(f"{pct_el}%", "of the time in El Niño", COLORS["el_nino"]),
             (f"{pct_la}%", "of the time in La Niña", COLORS["la_nina"]),
             (f"{pct_neutral}%", "of the time neutral", COLORS["text_2"]),
             (f"{len(el)}", f"El Niños since {roni.index[0].year}", COLORS["el_nino"])]
    tax = fig.add_axes([0.02, 0.70, 0.96, 0.12])
    tax.set_xlim(0, 1)
    tax.set_ylim(0, 1)
    tax.axis("off")
    for k, (big, small, col) in enumerate(tiles):
        x = k * 0.25 + 0.005
        tax.add_patch(FancyBboxPatch((x, 0), 0.235, 1, boxstyle="round,pad=0,rounding_size=0.04",
                                     facecolor=COLORS["surface_2"], edgecolor="none", mutation_aspect=0.25))
        tax.text(x + 0.02, 0.5, big, ha="left", va="center", fontsize=26, fontweight="bold", color=col)
        tax.text(x + 0.105, 0.5, small, ha="left", va="center", fontsize=12, color=COLORS["text_2"],
                 wrap=True)

    # --- row 2 left: gaps between El Niños --------------------------------------------
    ax1 = fig.add_axes([0.06, 0.12, 0.40, 0.46])
    bins = np.arange(0, np.ceil(gaps.max()) + 1, 1)
    ax1.hist(gaps, bins=bins, color=COLORS["el_nino"], rwidth=0.86)
    ax1.set_xlabel("Years from one El Niño to the next")
    ax1.set_ylabel("Number of times")
    ax1.yaxis.grid(True)
    ax1.set_axisbelow(True)
    ax1.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    med = np.median(gaps)
    top = ax1.get_ylim()[1]
    ax1.set_ylim(0, top + 1.2)          # headroom so the label clears the tallest bar
    ax1.axvline(med, color=COLORS["text"], lw=1.4, ls=(0, (4, 3)))
    ax1.text(med, top + 1.1, f"  typical gap: {med:.1f} years", va="top",
             fontsize=11.5, color=COLORS["text"])
    ax1.set_title("Gaps between El Niños", fontsize=14)

    # --- row 2 right: periodogram -----------------------------------------------------
    ax2 = fig.add_axes([0.56, 0.12, 0.40, 0.46])
    period, power = periodogram(roni)
    sel = (period >= 1) & (period <= 12)   # longer periods: too few cycles in 76 years to trust
    ax2.axvspan(2, 7, color=COLORS["el_nino"], alpha=0.12, lw=0)
    ax2.plot(period[sel], power[sel], color=COLORS["text"], lw=2)
    ax2.set_xscale("log")
    ax2.set_xticks([1, 2, 3, 5, 7, 10])
    ax2.set_xticklabels(["1", "2", "3", "5", "7", "10"])
    ax2.set_xlim(1, 12)
    ax2.set_ylim(0, 1.08)
    ax2.set_yticks([])
    ax2.spines["left"].set_visible(False)
    ax2.set_xlabel("Repeat time (years)")
    ax2.text(np.sqrt(2 * 7), 1.04, "2–7 years", ha="center", va="top", fontsize=12, fontweight="bold",
             color=COLORS["el_nino"])
    ax2.set_title("The rhythm hidden in the record", fontsize=14)
    ax2.text(1.05, 0.5, "Taller = that\nrepeat time shows\nup more strongly", transform=ax2.transData,
             fontsize=10.5, color=COLORS["text_2"], va="center")

    lo, hi = np.percentile(gaps, [10, 90])
    add_title(fig, "How often does El Niño come back?",
              f"El Niño has no fixed schedule. It usually returns after {lo:.0f}–{hi:.0f} years, and the longest "
              f"wait since 1950 was {gaps.max():.0f} years.\nThe Pacific swings between El Niño, La Niña and "
              "neutral all the time.")
    add_source(fig, "Data: NOAA CPC Relative Oceanic Niño Index (RONI). El Niño / La Niña = 5+ overlapping "
               "seasons at ≥ +0.5 / ≤ −0.5 °C. Gaps measured between event starts.")
    save(fig, args.out,
         alt=f"Since {roni.index[0].year}: {pct_el}% of the time El Niño, {pct_la}% La Niña, "
             f"{pct_neutral}% neutral; {len(el)} El Niños. Histogram of years between El Niños, "
             f"typically {med:.1f} years, mostly {lo:.0f} to {hi:.0f}. A periodogram peaks between 2 and 7 years.")


if __name__ == "__main__":
    main()
