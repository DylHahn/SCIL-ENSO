"""
Animation 7 — Kelvin waves: the pulses of warm water that built the 2026 El Niño

An infographic in two parts (the three-step cartoon that used to head it is in
archive/kelvin_schematic.py):
  1. Total sea level along the equator on the day shown: the build-up of warm water in the east.
  2. The Kelvin-wave signal along the equator (1°S–1°N) since July of the year before onset, day by
     day, filled in as the animation runs, with each wave traced and listed once it has crossed.

Data: NOAA blended satellite altimetry (daily, 0.25°). Anomalies are relative to the 2017–2024
seasonal cycle with a 5-day running mean. The wave signal is the anomaly minus its 91-day running
mean, which removes the slow El Niño build-up and leaves the eastward pulses. Waves are traced
automatically as straight eastward paths from 150°E to 95°W at 1.8–4.0 m/s along which the wave
signal averages at least +3 cm, at least 20 days apart at both ends, once they have finished crossing.

    python anim_kelvin.py
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import FuncFormatter

from enso_anim import AnimationFrames
from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, lon_label
from enso_sealevel import anomalies, daily

NOW = 2026
LON_RANGE = (130.0, 267.0)               # stop west of the Galápagos, which disturb the altimetry
X0, X1 = 150.0, 265.0                    # tracking window: 150°E to 95°W
M_PER_DEG = 111.32e3
SPEEDS = np.arange(1.8, 4.01, 0.05)      # m/s; first-mode Kelvin waves travel at roughly 2.5–3 m/s
MIN_CM = 3.0
GAP_DAYS = 20
START = f"{NOW - 1}-10-01"            # first day shown


def wave_signal(anom, window=91):
    """Anomaly minus its centred running mean: the fast, eastward pulses without the slow build-up."""
    return anom - anom.rolling(window, center=True, min_periods=window // 3).mean()


def track_waves(sig):
    """[(start date, speed m/s, mean cm, arrival date)] for eastward ridges crossing X0→X1."""
    lons = np.array(sig.columns, float)
    sel = (lons >= X0) & (lons <= X1)
    xs, A = lons[sel], sig.values[:, sel]
    t = (sig.index - sig.index[0]).days.values.astype(float)
    cand = []
    for i0 in range(len(t)):
        for c in SPEEDS:
            ti = t[i0] + (xs - X0) * M_PER_DEG / c / 86400.0
            if ti[-1] > t[-1]:                               # only waves that have finished crossing
                continue
            k = np.searchsorted(t, ti)
            score = np.nanmean(A[k, np.arange(len(xs))])
            if score >= MIN_CM:
                cand.append((score, i0, c, t[i0] + (X1 - X0) * M_PER_DEG / c / 86400.0))
    waves = []
    for score, i0, c, te in sorted(cand, reverse=True):     # strongest first; keep well-separated paths
        if all(abs(t[i0] - t[j]) >= GAP_DAYS and abs(te - e) >= GAP_DAYS for _, j, _, e in waves):
            waves.append((score, i0, c, te))
    waves.sort(key=lambda w: w[1])
    d0 = sig.index[0]
    return [(sig.index[i0], c, s, d0 + pd.Timedelta(days=te)) for s, i0, c, te in waves]


def refine(sig, waves, half_window=12):
    """Measure each traced wave's speed from the data: at every longitude, the day on which the wave signal
    peaks within `half_window` days of the traced path; a straight line through those (day, distance)
    points gives the speed, its standard error and the fit's r². Returns [(start, speed m/s, mean cm,
    arrival, standard error m/s, r²)], with start and arrival from the fitted line."""
    lons = np.array(sig.columns, float)
    sel = (lons >= X0) & (lons <= X1)
    xs, A = lons[sel], sig.values[:, sel]
    d0, n_days = sig.index[0], len(sig)
    out = []
    for t0, c, amp, t1 in waves:
        ti = (t0 - d0).days + (xs - X0) * M_PER_DEG / c / 86400.0
        pts = []
        for j, x in enumerate(xs):
            lo, hi = int(ti[j] - half_window), int(ti[j] + half_window)
            if lo < 0 or hi >= n_days or np.isnan(A[lo:hi + 1, j]).all():
                continue
            pts.append((lo + int(np.nanargmax(A[lo:hi + 1, j])), (x - X0) * M_PER_DEG))
        day, dist = np.array(pts, float).T
        slope, icpt = np.polyfit(day, dist, 1)                        # m per day
        resid = dist - (icpt + slope * day)
        r2 = 1 - (resid ** 2).sum() / ((dist - dist.mean()) ** 2).sum()
        se = np.sqrt((resid ** 2).sum() / (len(day) - 2) / ((day - day.mean()) ** 2).sum())
        start = d0 + pd.Timedelta(days=float(-icpt / slope))
        end = d0 + pd.Timedelta(days=float(((X1 - X0) * M_PER_DEG - icpt) / slope))
        out.append((start, slope / 86400.0, amp, end, se / 86400.0, r2))
    return out


def kelvin_waves(refresh=False, first="2017-01-01"):
    """Sea level anomaly and Kelvin-wave signal (cm, date × longitude) over the whole satellite record, and
    every wave traced and measured in it. The Kelvin wave animation and the speed chart both use this, so
    each wave has the same dates and speed in both."""
    raw = daily(first, refresh=refresh)
    anom = anomalies(raw).dropna(how="all")
    lons = np.array(anom.columns, float)
    anom = anom.loc[:, (lons >= LON_RANGE[0]) & (lons <= LON_RANGE[1])]
    sig = wave_signal(anom)
    sig = sig.loc[sig.index[0] + pd.Timedelta(days=90):]          # the 91-day filter needs data on both sides
    return anom, sig, refine(sig, track_waves(sig))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--every", type=int, default=4, help="days per animation frame")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--units", choices=["cm", "in"], default="cm", help="units for sea level (the website shows both)")
    ap.add_argument("--out", default=str(FIG_DIR / "anim" / "anim_kelvin.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    anom, sig, waves = kelvin_waves(args.refresh)
    lons = np.array(anom.columns, float)
    anom, sig = anom.loc[START:], sig.loc[START:]                 # shown from October of the year before onset
    # waves that crossed during the period shown, with speeds measured from each wave's peaks
    waves = [w[:4] for w in waves if w[0] + (w[3] - w[0]) / 2 >= pd.Timestamp(START)]
    dates = anom.index
    # waves are traced in centimetres; values are shown in the chosen units
    k, U = (1.0, "cm") if args.units == "cm" else (1 / 2.54, "in")
    anom, sig = anom * k, sig * k

    H = 11.9
    fig = plt.figure(figsize=(13, H))
    W = 0.62
    HOV = (1.1, 6.1)                                              # bottom panel: bottom and height, inches
    prof = fig.add_axes([0.085, 1 - 3.35 / H, W, 1.6 / H])
    hov = fig.add_axes([0.085, HOV[0] / H, W, HOV[1] / H])

    # bottom: the wave signal, revealed day by day
    levels = np.arange(-10, 10.1, 2) if U == "cm" else np.arange(-4, 4.1, 1)
    cmap = plt.get_cmap("jet", len(levels) + 1)                 # rainbow scale for contrast
    norm = BoundaryNorm(levels, cmap.N, extend="both")
    data = np.ma.masked_invalid(sig.values)
    mesh = hov.pcolormesh(lons, dates, np.ma.array(data, mask=True), cmap=cmap, norm=norm, shading="nearest",
                          rasterized=True)
    hov.set_ylim(dates[-1] + pd.Timedelta(days=2), dates[0])
    hov.set_xlim(*LON_RANGE)
    hov.xaxis.set_major_formatter(FuncFormatter(lon_label))
    hov.set_xticks([140, 160, 180, 200, 220, 240, 260])
    hov.yaxis.set_major_locator(mdates.MonthLocator())
    hov.yaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    hov.tick_params(axis="both", labelsize=11)
    for t in hov.get_xticklabels() + hov.get_yticklabels():
        t.set_fontweight("bold")
    hov.set_xlabel("Longitude along the equator", fontsize=12, fontweight="bold", color=COLORS["text"])
    hov.set_ylabel("Date (time runs down)", fontsize=12, fontweight="bold", color=COLORS["text"])
    hov.set_title("Kelvin-wave signal along the equator, day by day: each streak slanting right is one wave",
                  fontsize=13.5, fontweight="bold", loc="left", pad=8, color=COLORS["text"])
    now_line = hov.axhline(dates[0], color="white", lw=1.2, alpha=0.9)
    cax = fig.add_axes([0.085 + W + 0.012, HOV[0] / H, 0.012, HOV[1] / H])     # as tall as the panel
    cb = fig.colorbar(mesh, cax=cax, ticks=levels[::1])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=10.5, length=0)
    for t in cb.ax.get_yticklabels():
        t.set_fontweight("bold")
    cb.set_label(f"Kelvin-wave signal ({U}): sea level above (red) or below (blue) its 91-day average", fontsize=11,
                 fontweight="bold", color=COLORS["text"])

    # middle: total sea level along the equator on the day shown
    prof.axhline(0, color=COLORS["text_2"], lw=0.8)
    top = float(np.nanmax(anom.values))
    step = 10 if U == "cm" else 4
    prof.set_ylim(-2 * step, max(3 * step, np.ceil(top / step) * step + step / 2))
    prof.yaxis.grid(True, color=COLORS["grid"], lw=0.6)
    prof.set_ylabel(f"SSH anomaly ({U})", fontsize=12, fontweight="bold", color=COLORS["text"])
    prof.set_xlim(*LON_RANGE)
    prof.xaxis.set_major_formatter(FuncFormatter(lon_label))
    prof.set_xticks([140, 160, 180, 200, 220, 240, 260])
    prof.set_xlabel("Longitude along the equator", fontsize=12, fontweight="bold", color=COLORS["text"])
    prof.tick_params(axis="both", labelsize=11)
    for t in prof.get_xticklabels() + prof.get_yticklabels():
        t.set_fontweight("bold")
    prof_title = prof.set_title("", fontsize=13.5, fontweight="bold", loc="left", pad=8, color=COLORS["text"])
    line, = prof.plot([], [], color=COLORS["text"], lw=1.5)
    fills = []

    # right: the list of waves, filled in as each one completes its crossing
    lx = 0.085 + W + 0.1
    top_tab = H - (HOV[0] + HOV[1])                                 # level with the top of the bottom panel
    fig.text(lx, 1 - (top_tab + 0.05) / H, "Kelvin waves traced", fontsize=14, fontweight="bold",
             color=COLORS["text"], va="top")
    fig.text(lx, 1 - (top_tab + 0.4) / H, "left 150°E → reached 95°W, speed", fontsize=10.5, fontweight="bold",
             color=COLORS["text_2"], va="top")
    rows, tracks = [], []
    for n, (t0, c, s, t1) in enumerate(waves, 1):
        rows.append((t1, fig.text(lx, 1 - (top_tab + 0.85 + 0.45 * (n - 1)) / H,
                                  f"{n}  {t0:%-d %b} → {t1:%-d %b %Y}\n    {c:.1f} m/s", fontsize=10.5,
                                  fontweight="bold", color=COLORS["text"], alpha=0, va="top", linespacing=1.15)))
        ln, = hov.plot([X0, X1], [t0, t1], color="black", lw=3.0, alpha=0)
        ln2, = hov.plot([X0, X1], [t0, t1], color="white", lw=1.6, ls=(0, (6, 3)), alpha=0)
        num = hov.text(X0 - 1.5, t0, str(n), fontsize=12, fontweight="bold", color="white", ha="right",
                       va="center", alpha=0, bbox=dict(boxstyle="round,pad=0.2", fc="black", ec="none", alpha=0))
        tracks.append((t1, ln, ln2, num))
    note = fig.text(lx, 1 - (top_tab + 1.0 + 0.45 * len(waves)) / H,
                    "A wave is listed once it\nhas crossed the Pacific;\nwaves still travelling\nappear in later "
                    "updates.", fontsize=10.5, color=COLORS["text_2"], va="top", linespacing=1.35)

    add_title(fig, f"Kelvin waves: the pulses of warm water that built the {NOW}/{NOW + 1} El Niño",
              "Bursts of westerly wind in the western Pacific send pulses of warm water east along the equator. Each "
              "raises sea level by a few\n" + ("centimetres" if U == "cm" else "centimetres (about an inch)")
              + " as it passes, so satellites can follow it across the Pacific.")
    add_source(fig, "Data: NOAA blended satellite altimetry (daily, 0.25°, 1°S–1°N), anomalies from the 2017–2024 "
               "seasonal cycle. Wave signal: anomaly minus its 91-day running mean.\nWaves traced automatically "
               "(150°E–95°W, 1.8–4.0 m/s, wave signal ≥ +3 cm, 1.2 in). Top panel: sea surface height (SSH) anomaly.")

    frames = AnimationFrames(fig, dpi=105)
    idx = list(range(0, len(dates), args.every))
    if idx[-1] != len(dates) - 1:
        idx.append(len(dates) - 1)
    for i in idx:
        d = dates[i]
        mesh.set_array(np.ma.array(data, mask=np.ma.getmaskarray(data) | (np.arange(len(dates)) > i)[:, None]).ravel())
        now_line.set_ydata([d, d])
        v = anom.values[i]
        line.set_data(lons, v)
        for f in fills:
            f.remove()
        fills = [prof.fill_between(lons, 0, v, where=v > 0, color="#e8574a", alpha=0.7, lw=0, interpolate=True),
                 prof.fill_between(lons, 0, v, where=v < 0, color="#3987e5", alpha=0.7, lw=0, interpolate=True)]
        prof_title.set_text(f"Sea level height (SSH) along the equator, {d:%-d %B %Y}: The warm water piling up in "
                            "the east")
        for t1, ln, ln2, num in tracks:
            on = 1.0 if d >= t1 else 0.0
            ln.set_alpha(0.55 * on); ln2.set_alpha(on); num.set_alpha(on); num.get_bbox_patch().set_alpha(0.7 * on)
        for t1, txt in rows:
            txt.set_alpha(1.0 if d >= t1 else 0.0)
        frames.grab(70)
    frames.durations[-1] = 4500
    east = lons >= 230
    frames.save(args.out, quality=85,
                alt=f"Animated infographic of Kelvin waves along the equatorial Pacific from {dates[0]:%B %Y} to "
                    f"{dates[-1]:%-d %B %Y}, from daily satellite sea level. {len(waves)} Kelvin waves crossed the "
                    "Pacific: " + "; ".join(f"wave {n} left 150°E on {t0:%-d %B} and reached 95°W on {t1:%-d %B %Y} "
                                            f"at {c:.1f} m/s" for n, (t0, c, s, t1) in enumerate(waves, 1))
                    + f". Sea level east of 130°W rose from {np.nanmean(anom.values[0][east]):+.0f} {U} to "
                      f"{np.nanmean(anom.values[-1][east]):+.0f} {U} over the period.")


if __name__ == "__main__":
    main()
