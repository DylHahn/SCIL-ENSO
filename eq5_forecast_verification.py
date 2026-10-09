"""
Equatorial 5 — How NOAA's 2026 El Niño forecasts compare with what happened

NOAA CPC began issuing official strength probabilities based on the Relative
Oceanic Niño Index (RONI) in 2026. This figure takes every monthly issue in the
CPC archive and checks it against the observed RONI:
  (a) forecasts for Jul–Sep 2026 (the latest observed season), by issue month,
      with the category that occurred outlined
  (b) probability assigned to the observed category, by lead time, for every
      season that has been observed
  (c) how the forecast probability of a very strong event (≥ +2.0 °C) for the
      expected peak season has changed from one issue to the next

    python eq5_forecast_verification.py
    python eq5_forecast_verification.py --refresh
"""
import argparse
import html as _html
import re
import urllib.request

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

from enso_common import (CACHE_DIR, FIG_DIR, COLORS, _season_dates, add_source, add_title, apply_style,
                         load_roni, save, season_label)

ARCHIVE = ("https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/archives/"
           "?type=strengths&month={m:02d}&year={y}")
CURRENT = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/strengths/"
FIRST_ISSUE = pd.Timestamp("2026-04-01")
COLS = ["≤ −2.0", "−2.0 to −1.5", "−1.5 to −1.0", "−1.0 to −0.5", "Neutral",
        "+0.5 to +1.0", "+1.0 to +1.5", "+1.5 to +2.0", "≥ +2.0"]
EDGES = [-np.inf, -2.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0, np.inf]
NAMES = {4: "Neutral", 5: "Weak", 6: "Moderate", 7: "Strong", 8: "Very strong"}
SHADES = {"Neutral": "#77766f", "Weak": "#f4b8a8", "Moderate": "#ea8a72", "Strong": "#d9573f", "Very strong": "#9c2a22"}


def _rows(text):
    text = re.sub(r"(?s)<!--.*?-->", " ", text)
    text = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", text)))
    issued = re.search(r"Issued ([A-Z][a-z]+ \d{4})", text)
    rows = re.findall(r"\b([JFMASOND]{3}) [A-Z][a-z]{2} [A-Z][a-z]{2} [A-Z][a-z]{2}((?: -?\d+(?:\.\d+)?)+)", text)
    return (issued.group(1) if issued else None), [(s, [float(v) for v in n.split()][:9]) for s, n in rows]


def load_issue(month, refresh):
    """DataFrame of strength probabilities (%) for one CPC issue, indexed by season centre month."""
    path = CACHE_DIR / f"cpc_strengths_{month:%Y%m}.html"
    if refresh or not path.exists():
        url = ARCHIVE.format(m=month.month, y=month.year)
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "enso-public-viz/1.0"}),
                                    timeout=60) as r:
            text = r.read().decode("utf-8", "replace")
        issued, rows = _rows(text)
        if issued != f"{month:%B %Y}":                     # the archive may not hold this month (yet)
            with urllib.request.urlopen(CURRENT, timeout=60) as r:
                text = r.read().decode("utf-8", "replace")
            issued, rows = _rows(text)
            if issued != f"{month:%B %Y}":
                return None
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    issued, rows = _rows(path.read_text())
    df = pd.DataFrame([r[1] for r in rows], columns=COLS, index=_season_dates([r[0] for r in rows], issued))
    df["season"] = [r[0] for r in rows]
    return df


def category(v):
    return int(np.searchsorted(EDGES, v, side="right") - 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "equatorial" / "eq5_forecast_verification.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    roni = load_roni(refresh=args.refresh)
    issues = {}
    m = FIRST_ISSUE
    while m <= pd.Timestamp.today().normalize():
        df = load_issue(m, args.refresh)
        if df is not None:
            issues[m] = df
        m += pd.DateOffset(months=1)
    observed = {t: v for t, v in roni.items() if t >= FIRST_ISSUE - pd.DateOffset(months=1)}
    target = max(t for t in observed if any(t in df.index for df in issues.values()))

    fig = plt.figure(figsize=(13, 9.2))

    # (a) stacked forecasts for the latest observed season
    ax = fig.add_axes([0.11, 0.50, 0.85, 0.27])
    use = [(i, df.loc[target]) for i, df in issues.items() if target in df.index]
    obs_cat = category(observed[target])
    for y, (i, row) in enumerate(use[::-1]):
        left = 0.0
        for c in range(4, 9):
            v = float(row[COLS[c]])
            ax.barh(y, v, left=left, height=0.62, color=SHADES[NAMES[c]], edgecolor=COLORS["surface"], lw=1.5)
            if c == obs_cat and v > 0:
                ax.add_patch(Rectangle((left, y - 0.31), v, 0.62, fill=False, edgecolor=COLORS["text"], lw=2.2,
                                       zorder=5))
            if v >= 9:
                ax.text(left + v / 2, y, f"{v:.0f}%", ha="center", va="center", fontsize=10.5, color="white",
                        fontweight="bold")
            left += v
    ax.set_yticks(range(len(use)))
    ax.set_yticklabels([f"{i:%B} issue" for i, _ in use[::-1]], fontsize=11)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_title(f"(a) Forecasts for {season_label(target)}: observed RONI {observed[target]:+.2f} °C "
                 f"({NAMES[obs_cat].lower()} El Niño, outlined)", fontsize=13.5, loc="left", pad=8)
    ax.legend(handles=[Patch(color=SHADES[NAMES[c]], label=f"{NAMES[c]} ({COLS[c]} °C)" if c > 4 else "Neutral")
                       for c in range(4, 9)], loc="lower left", bbox_to_anchor=(0, 1.08), ncol=5, fontsize=10,
              labelcolor=COLORS["text_2"])

    # (b) probability given to the observed category vs lead time
    bx = fig.add_axes([0.07, 0.12, 0.39, 0.25])
    hit_rows = []
    palette = ["#3987e5", "#199e70", "#c98500", "#e8574a", "#9085e9"]
    seasons = sorted(t for t in observed if any(t in df.index for df in issues.values()))
    for k, t in enumerate(seasons):
        cat = category(observed[t])
        pts = sorted(((t.year - i.year) * 12 + t.month - i.month, float(df.loc[t, COLS[cat]]))
                     for i, df in issues.items() if t in df.index)
        if not pts:
            continue
        lead, prob = zip(*pts)
        bx.plot(lead, prob, "o-", color=palette[k % len(palette)], lw=2, ms=6, label=season_label(t))
        hit_rows.extend(prob)
    bx.set_xlabel("Lead time (months from issue to the centre of the season)")
    bx.set_ylabel("Probability (%)")
    bx.set_ylim(0, 100)
    bx.invert_xaxis()
    bx.yaxis.grid(True)
    bx.set_axisbelow(True)
    bx.set_title("(b) Confidence in what actually happened", fontsize=13.5, loc="left", pad=22)
    bx.text(0, 1.02, "Probability given to the observed category", transform=bx.transAxes, fontsize=10.5,
            color=COLORS["text_2"], va="bottom")
    bx.legend(fontsize=9.5, labelcolor=COLORS["text_2"], loc="upper left", title="Target season",
              title_fontsize=9.5)

    # (c) evolution of the very-strong probability for the expected peak season
    cx = fig.add_axes([0.56, 0.12, 0.40, 0.25])
    latest_issue = max(issues)
    latest = issues[latest_issue]
    # expected peak: the season not yet begun with the highest very-strong probability in the latest issue
    future = latest[latest.index - pd.DateOffset(months=1) > latest_issue]
    peak = future[COLS[8]].astype(float).idxmax()
    ev = [(i, float(df.loc[peak, COLS[8]]), float(df.loc[peak, COLS[7]] + df.loc[peak, COLS[8]]))
          for i, df in issues.items() if peak in df.index]
    x = [i for i, _, _ in ev]
    cx.plot(x, [s for _, _, s in ev], "o-", color=SHADES["Strong"], lw=2, ms=6, label="Strong or very strong (≥ +1.5)")
    cx.plot(x, [v for _, v, _ in ev], "o-", color=SHADES["Very strong"], lw=2.6, ms=7, label="Very strong (≥ +2.0)")
    for i, v, _ in ev:
        cx.annotate(f"{v:.0f}%", (i, v), xytext=(0, -14), textcoords="offset points", ha="center", fontsize=9.5,
                    color=COLORS["text_2"])
    cx.set_ylim(0, 105)
    cx.set_xticks(x)
    cx.set_xticklabels([f"{i:%b}" for i in x])
    cx.set_xlabel("Issue month, 2026")
    cx.set_ylabel("Probability (%)")
    cx.yaxis.grid(True)
    cx.set_axisbelow(True)
    cx.set_title("(c) Forecasts for the expected peak season", fontsize=13.5, loc="left", pad=22)
    cx.text(0, 1.02, f"{season_label(peak)}, by issue month", transform=cx.transAxes, fontsize=10.5,
            color=COLORS["text_2"], va="bottom")
    cx.legend(fontsize=9.5, labelcolor=COLORS["text_2"], loc="lower right")

    first_hit = use[0][1][COLS[obs_cat]] if use else np.nan
    add_title(fig, "Verification of NOAA's 2026 El Niño forecasts",
              f"Official NOAA strength probabilities from each monthly issue since {FIRST_ISSUE:%B %Y}, compared with "
              f"the observed RONI. Spring forecasts favoured a weak-to-\nmoderate event: the {use[0][0]:%B} issue gave "
              f"{first_hit:.0f}% to the strength observed in {season_label(target)}. The probability of a very strong "
              f"peak rose from {ev[0][1]:.0f}% to {ev[-1][1]:.0f}%.")
    add_source(fig, "Data: NOAA Climate Prediction Center official ENSO strength probabilities (monthly archive) and "
               "Relative Oceanic Niño Index (RONI). Seasons are 3-month means.")
    save(fig, args.out,
         alt=f"Verification of NOAA's 2026 El Niño strength forecasts. For {season_label(target)} (observed "
             f"{observed[target]:+.2f} °C, {NAMES[obs_cat].lower()}), forecasts by issue month gave the observed "
             "category: " + "; ".join(f"{i:%B} {float(r[COLS[obs_cat]]):.0f}%" for i, r in use)
             + f". Probability of a very strong peak in {season_label(peak)} by issue: "
             + "; ".join(f"{i:%B} {v:.0f}%" for i, v, _ in ev) + ".")


if __name__ == "__main__":
    main()
