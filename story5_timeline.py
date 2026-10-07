"""
Story 5 — "What to expect, and when"

A month-by-month timeline for the coming year. The El Niño rows come straight
from NOAA's current RONI outlook (when the middle estimate is "very strong",
when it peaks, when it falls back to neutral); the impact rows use typical
El Niño timing:
  * global surface temperature lags the El Niño peak by roughly 3–6 months
  * the biggest seasonal rainfall shifts come in Dec–Feb
  * failed rains show up later as poor harvests and low reservoirs

    python story5_timeline.py
    python story5_timeline.py --refresh       # after NOAA's monthly update
"""
import argparse
import textwrap

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from enso_common import (FIG_DIR, COLORS, add_source, add_title, apply_style, load_cpc_outlook, save,
                         season_words)

PREPARE = "#2fa84f"   # "good" status green: the one row that is an action, not a hazard


def season_span(center):
    """3-month season centred on `center` -> (first day, last day)."""
    return center - pd.DateOffset(months=1), center + pd.DateOffset(months=2) - pd.Timedelta(days=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--today", help="date for the 'Now' line (default: today)")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "story" / "story5_timeline.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    fc = load_cpc_outlook(args.refresh)
    today = pd.Timestamp(args.today) if args.today else pd.Timestamp.today().normalize()

    vstrong = fc[fc["p50"] >= 2.0]
    peak = fc["p50"].idxmax()
    below = fc[(fc.index > peak) & (fc["p50"] < 0.5)]
    neutral_at = below.index[0] if len(below) else fc.index[-1]
    fading = fc[(fc.index > peak) & (fc["p50"] < 1.0)]
    fade_from = fading.index[0] if len(fading) else neutral_at

    # the northern winter (Dec–Mar) around the peak is when most El Niño rainfall shifts are strongest
    impacts_start = pd.Timestamp(year=peak.year if peak.month >= 6 else peak.year - 1, month=12, day=1)
    if len(vstrong):
        vs_start, vs_end = season_span(vstrong.index[0])[0], season_span(vstrong.index[-1])[1]
        vs_detail = f"NOAA's middle estimate stays at +2.0 °C or more through {vs_end:%B %Y}"
    else:
        vs_start, vs_end = season_span(peak)
        vs_detail = f"Peak expected around {season_words(fc.loc[peak, 'season'])}"

    rows = [  # (label, detail, start, end, colour, alpha)
        ("Get ready", "Best window to prepare for the winter peak",
         today, impacts_start, PREPARE, 0.9),
        ("Very strong El Niño", vs_detail, vs_start, vs_end, COLORS["el_nino"], 0.95),
        ("Biggest weather shifts", "Droughts and floods most likely in many regions (see map)",
         impacts_start, impacts_start + pd.DateOffset(months=4) - pd.Timedelta(days=1), COLORS["el_nino"], 0.6),
        ("Global heat peaks", "World temperatures usually top out 3–6 months after El Niño does",
         peak + pd.DateOffset(months=3), peak + pd.DateOffset(months=7) - pd.Timedelta(days=1),
         COLORS["heat"], 0.85),
        ("El Niño fades", f"Back to neutral by about {season_words(fc.loc[neutral_at, 'season'])} "
         f"{neutral_at.year}", season_span(fade_from)[0], season_span(neutral_at)[1], COLORS["neutral"], 0.9),
        ("Effects linger", "Poor harvests, low reservoirs and higher food prices can last months longer",
         neutral_at - pd.DateOffset(months=2), neutral_at + pd.DateOffset(months=4), COLORS["neutral"], 0.5),
    ]

    x0 = (today - pd.DateOffset(months=1)).replace(day=1)
    x1 = (neutral_at + pd.DateOffset(months=6)).replace(day=1)

    fig, ax = plt.subplots(figsize=(13, 7.6))
    fig.subplots_adjust(top=0.82, bottom=0.10, left=0.34, right=0.97)
    label_x = -0.02   # axes fraction: the label column sits left of the axes
    n = len(rows)
    for i, (label, detail, a, b, col, alpha) in enumerate(rows):
        y = n - 1 - i
        a, b = max(a, x0), min(b, x1)
        ax.barh(y, (b - a).days, left=a, height=0.5, color=col, alpha=alpha, linewidth=0)
        trans = ax.get_yaxis_transform()
        ax.text(label_x, y + 0.04, label, transform=trans, ha="right", va="bottom", fontsize=14,
                fontweight="bold", color=COLORS["text"])
        ax.text(label_x, y - 0.02, textwrap.fill(detail, 44), transform=trans, ha="right", va="top",
                fontsize=11, color=COLORS["text_2"], linespacing=1.3)

    ax.axvline(today, color=COLORS["text"], lw=1.4)
    ax.text(today, n - 0.35, "  Now", ha="left", va="bottom", fontsize=12, fontweight="bold",
            color=COLORS["text"])

    ax.set_xlim(x0, x1)
    ax.set_ylim(-0.6, n - 0.1)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.xaxis.grid(True, which="major")
    ax.set_axisbelow(True)

    add_title(fig, "What to expect, and when",
              "El Niño is predictable months ahead, which gives communities time to get ready. "
              f"Timing from NOAA's {fc.attrs['issued']} outlook\nand how past El Niños have played out.")
    add_source(fig, f"El Niño rows: NOAA CPC official RONI outlook ({fc.attrs['issued']}). "
               "Impact rows: typical timing from past El Niño events; local timing varies.")
    save(fig, args.out,
         alt="Timeline. Now: best window to prepare. "
             + ". ".join(f"{label}: {a:%b %Y} to {b:%b %Y}" for label, _, a, b, _, _ in rows[1:]) + ".")


if __name__ == "__main__":
    main()
