"""
Figure 4 — "The ocean's heat 'charges up' before El Niño"

Top: warm water volume (WWV) anomaly and the Niño 3.4 surface anomaly, each
standardized so they share one axis (no dual axes).
Bottom: how well WWV predicts Niño 3.4 N months later (lag correlation),
optionally split before/after a year to show the post-2000 weakening.

WWV sources
  --wwv-source godas   compute from your files data/godasClimatologyData_{depth}m.nc
                       (volume warmer than 20 °C, 5°S–5°N, 120°E–80°W)   [default]
  --wwv-source pmel    NOAA PMEL wwv.dat (pick the column with --wwv-col)
Niño 3.4 sources
  --nino-source cpc    NOAA CPC monthly sstoi.indices                     [default]
  --nino-source godas  box mean of your 5 m GODAS file

    python fig4_wwv_vs_nino34.py --data-dir data
    python fig4_wwv_vs_nino34.py --wwv-source pmel --wwv-col 2
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from enso_common import (FIG_DIR, GODAS_DIR, COLORS, NINO_BOXES, add_source, add_title, apply_style,
                         godas_box_mean, godas_wwv, load_nino34_monthly,
                         load_wwv_pmel, monthly_anomaly, save, zscore)


def lag_corr(lead_series, follow_series, max_lag=18):
    """corr(lead[t], follow[t + lag]) for lag = 0..max_lag months."""
    out = {}
    for lag in range(max_lag + 1):
        a = lead_series
        b = follow_series.shift(-lag)
        df = pd.concat([a, b], axis=1).dropna()
        out[lag] = df.iloc[:, 0].corr(df.iloc[:, 1]) if len(df) > 24 else np.nan
    return pd.Series(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default=str(GODAS_DIR))
    ap.add_argument("--wwv-source", choices=["godas", "pmel"], default="godas")
    ap.add_argument("--wwv-file", help="local copy of PMEL wwv.dat")
    ap.add_argument("--wwv-col", type=int, default=1, help="numeric column in wwv.dat (0 = date)")
    ap.add_argument("--wwv-is-anomaly", action="store_true",
                    help="the chosen PMEL column is already an anomaly")
    ap.add_argument("--nino-source", choices=["cpc", "godas"], default="cpc")
    ap.add_argument("--nino-file", help="local copy of sstoi.indices")
    ap.add_argument("--start", type=int, default=1980)
    ap.add_argument("--split-year", type=int, default=2000,
                    help="draw separate lag curves before/after this year (0 to disable)")
    ap.add_argument("--max-lag", type=int, default=18)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "fig4_wwv_vs_nino34.png"))
    args = ap.parse_args()

    apply_style()

    if args.wwv_source == "godas":
        wwv = monthly_anomaly(godas_wwv(args.data_dir))
        wwv_src = "warm water volume computed from GODAS (water > 20 °C, 5°S–5°N, 120°E–80°W)"
    else:
        wwv = load_wwv_pmel(args.wwv_file, args.refresh, args.wwv_col)
        if not args.wwv_is_anomaly:
            wwv = monthly_anomaly(wwv)
        wwv_src = "warm water volume from NOAA PMEL"
    if args.nino_source == "cpc":
        nino = load_nino34_monthly(args.nino_file, args.refresh)
        nino_src = "Niño 3.4 from NOAA CPC"
    else:
        b = NINO_BOXES["Niño 3.4"]
        nino = godas_box_mean(args.data_dir, 5, b["lat"], b["lon"])
        nino_src = "Niño 3.4 (5 m) from GODAS"

    df = pd.concat([wwv.rename("wwv"), nino.rename("nino")], axis=1).dropna()
    df = df[df.index.year >= args.start]
    df["wwv_s"] = zscore(df["wwv"].rolling(3, center=True, min_periods=1).mean())
    df["nino_s"] = zscore(df["nino"].rolling(3, center=True, min_periods=1).mean())

    fig = plt.figure(figsize=(14, 9.4))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.6, 1], hspace=0.38,
                          top=0.84, bottom=0.11, left=0.08, right=0.97)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    # --- time series ---------------------------------------------------
    ax1.axhline(0, color=COLORS["text_2"], lw=0.8)
    ax1.fill_between(df.index, 0, df["nino_s"], where=df["nino_s"] > 0, color=COLORS["el_nino"],
                     alpha=0.14, linewidth=0, interpolate=True)
    ax1.fill_between(df.index, 0, df["nino_s"], where=df["nino_s"] < 0, color=COLORS["la_nina"],
                     alpha=0.14, linewidth=0, interpolate=True)
    ax1.plot(df.index, df["nino_s"], color=COLORS["text"], lw=1.6,
             label="Surface temperature, Niño 3.4 (shaded: red warm, blue cool)")
    ax1.plot(df.index, df["wwv_s"], color=COLORS["series_2"], lw=2.2,
             label="Heat stored below the surface (warm water volume)")
    ax1.set_ylabel("Above / below normal\n(standardized units)")
    ax1.yaxis.grid(True)
    ax1.set_axisbelow(True)
    ax1.legend(loc="upper left", ncol=2, bbox_to_anchor=(0, 1.12))
    ax1.xaxis.set_major_locator(mdates.YearLocator(5))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.set_xlim(df.index[0], df.index[-1])

    # --- lag correlation ----------------------------------------------
    curves = [("All years", df, COLORS["series_2"], 2.6)]
    if args.split_year:
        early = df[df.index.year < args.split_year]
        late = df[df.index.year >= args.split_year]
        if len(early) > 60 and len(late) > 60:
            curves = [(f"Before {args.split_year}", early, "#1c5cab", 2.2),
                      (f"{args.split_year} onward", late, "#86b6ef", 2.2)]

    for name, d, c, lw in curves:
        lc = lag_corr(d["wwv_s"], d["nino_s"], args.max_lag)
        k = int(lc.idxmax())
        ax2.plot(lc.index, lc.values, color=c, lw=lw, marker="o", ms=5,
                 label=f"{name}: strongest link ≈ {k} months ahead")
        ax2.plot([k], [lc[k]], marker="o", ms=12, mfc="none", mec=c, mew=2)
    ax2.axhline(0, color=COLORS["text_2"], lw=0.8)
    ax2.set_xlim(0, args.max_lag)
    ax2.set_xticks(range(0, args.max_lag + 1, 3))
    ax2.set_xlabel("How many months the subsurface heat comes before the surface temperature")
    ax2.set_ylabel("Correlation")
    ax2.yaxis.grid(True)
    ax2.set_axisbelow(True)
    ax2.set_title("How far ahead does the stored heat give a warning?", fontsize=14)
    ax2.legend(loc="lower left")

    add_title(fig, "The Pacific “charges up” with heat before El Niño",
              "Warm water piles up below the surface months before the surface warms. "
              "When the orange line rises first, the black line\ntends to follow — "
              "that head start is what lets forecasters see El Niño coming.")
    add_source(fig, f"Data: {wwv_src}; {nino_src}. Lines standardized (3-month mean ÷ std. dev.).")
    save(fig, args.out)


if __name__ == "__main__":
    main()
