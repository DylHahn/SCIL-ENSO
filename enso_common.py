"""
Shared helpers for the public-facing ENSO graphics.

Everything the individual figure scripts need lives here:
  * a consistent, readable plotting style
  * loaders for NOAA index files (RONI, ONI, monthly Niño 3.4, PMEL warm water volume)
  * loaders for your own GODAS depth files (data/godasClimatologyData_{depth}m.nc)

Every figure is built from real observations or NOAA forecasts; there is no
synthetic / demo mode.
"""

from __future__ import annotations

import io
import os
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------
URLS = {
    # 3-month running means, columns: SEAS YR ANOM  (official NOAA index since Feb 2026)
    "roni": "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt",
    # 3-month running means, columns: SEAS YR TOTAL ANOM  (legacy index)
    "oni": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
    # monthly, columns: YR MON NINO1+2 ANOM NINO3 ANOM NINO4 ANOM NINO3.4 ANOM
    "sstoi": "https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices",
    # monthly warm water volume from NOAA PMEL (format documented in the file header)
    "wwv": "https://www.pmel.noaa.gov/tao/wwv/data/wwv.dat",
    # NOAA NCEI global land+ocean temperature, annual (Jan-Dec) and year-to-date, vs 1901-2000
    "global_annual": "https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/"
                     "time-series/globe/tavg/land_ocean/12/12/1850-2025/data.csv",
    "global_ytd": "https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/"
                  "time-series/globe/tavg/land_ocean/ytd/8/1850-2026/data.csv",
    # CPC official RONI outlook (forecast percentiles) and strength probabilities, updated monthly
    "cpc_outlook": "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/outlook/",
    "cpc_strengths": "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/strengths/",
}
# cache file names for URLs whose last path part isn't a usable name
CACHE_NAMES = {
    "global_annual": "global_annual.csv",
    "global_ytd": "global_ytd.csv",
    "cpc_outlook": "cpc_roni_outlook.html",
    "cpc_strengths": "cpc_roni_strengths.html",
}

# All paths are relative to this folder, so the scripts work from anywhere
HERE = Path(__file__).resolve().parent
CACHE_DIR = Path(os.environ.get("ENSO_VIZ_CACHE", HERE / "data" / "noaa_cache"))
# GODAS depth files (godasClimatologyData_{depth}m.nc): a link to the research project's data folder
GODAS_DIR = HERE / "data" / "godas"
# NOAA's yearly GODAS files (pottmp.YYYY.nc) for months after the depth files end
GODAS_RAW_DIR = HERE / "data" / "godas_raw"
FIG_DIR = HERE / "figures_public"

SEASON_CENTER_MONTH = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
    "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}

_MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def season_words(code):
    """'OND' -> 'Oct–Dec' (3-month season codes are jargon for a general audience)."""
    mid = SEASON_CENTER_MONTH[code] - 1
    return f"{_MONTH_ABBR[(mid - 1) % 12]}–{_MONTH_ABBR[(mid + 1) % 12]}"


def season_label(center):
    """Centre-month timestamp -> 'Oct–Dec 2026' or 'Dec 2026–Feb 2027'."""
    a, b = center - pd.DateOffset(months=1), center + pd.DateOffset(months=1)
    return f"{a:%b}–{b:%b %Y}" if a.year == b.year else f"{a:%b %Y}–{b:%b %Y}"


# Boxes in 0-360 longitude (same convention as your GODAS files)
NINO_BOXES = {
    "Niño 1+2": dict(lat=(-10, 0), lon=(270, 280)),
    "Niño 3": dict(lat=(-5, 5), lon=(210, 270)),
    "Niño 4": dict(lat=(-5, 5), lon=(160, 210)),
    "Niño 3.4": dict(lat=(-5, 5), lon=(190, 240)),
}

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
COLORS = {
    "el_nino": "#d6402f",      # warm pole
    "la_nina": "#2a78d6",      # cool pole
    "neutral": "#b9b8b3",      # gray midpoint
    "series_1": "#2a78d6",     # blue
    "series_2": "#eb6834",     # orange
    "text": "#0b0b0b",
    "text_2": "#52514e",
    "muted": "#8a8984",
    "grid": "#e4e3df",
    "surface": "#fcfcfb",
    "ocean_warm": "#f2a98c",
    "ocean_cool": "#9cc3ee",
    "surface_2": "#f0efec",    # cards / panels
    "land": "#dcdad3",
    "ocean": "#e8f1fb",
    "heat": "#eb6834",
    "map_neutral": "#efeeea",  # middle of diverging map colour scales
}
LIGHT = dict(COLORS)

# Dark theme to sit on icharm.sdsu.edu (near-black background). Same hues,
# stepped for a dark surface.
DARK = {
    "el_nino": "#e8574a",
    "la_nina": "#3987e5",
    "neutral": "#77766f",
    "series_1": "#3987e5",
    "series_2": "#d95926",
    "text": "#f4f4f1",
    "text_2": "#c3c2b7",
    "muted": "#8a8984",
    "grid": "#2b2b2a",
    "surface": "#0d0d0e",
    "ocean_warm": "#b8573c",
    "ocean_cool": "#2d5f96",
    "surface_2": "#1c1c1b",
    "land": "#3a3935",
    "ocean": "#14202e",
    "heat": "#f07a3c",
    "map_neutral": "#3a3a38",
}


def apply_style(theme="light"):
    """theme="dark" swaps COLORS in place, so call this before reading any colour."""
    COLORS.update(DARK if theme == "dark" else LIGHT)
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 13,
        "axes.titlesize": 16,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.labelsize": 13,
        "axes.labelcolor": COLORS["text_2"],
        "axes.edgecolor": COLORS["muted"],
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.facecolor": COLORS["surface"],
        "figure.facecolor": COLORS["surface"],
        "savefig.facecolor": COLORS["surface"],
        "xtick.color": COLORS["text_2"],
        "ytick.color": COLORS["text_2"],
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "grid.color": COLORS["grid"],
        "grid.linewidth": 0.8,
        "legend.frameon": False,
        "legend.fontsize": 12,
        "lines.linewidth": 2.0,
        "text.color": COLORS["text"],
    })


def add_title(fig, title, subtitle=None, y=None):
    """Big plain-language headline + one-line explanation, left aligned.
    Positions are fixed in inches so spacing is the same at any figure height."""
    h = fig.get_figheight()
    y = 1 - 0.1 / h if y is None else y
    fig.text(0.02, y, title, ha="left", va="top", fontsize=19, fontweight="bold",
             color=COLORS["text"])
    if subtitle:
        fig.text(0.02, y - 0.42 / h, subtitle, ha="left", va="top", fontsize=13,
                 color=COLORS["text_2"])


def add_source(fig, text):
    """Source credit at the bottom left."""
    fig.text(0.02, 0.012, text, ha="left", va="bottom", fontsize=10, color=COLORS["muted"])


def save(fig, out_path, alt=None):
    """Write the PNG; with `alt`, also write <name>.alt.txt for the web page's alt attribute."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    if alt:
        out_path.with_suffix(".alt.txt").write_text(alt.strip() + "\n")
    print(f"Saved {out_path}")


def lon_label(x, _pos=None):
    x = float(x) % 360
    if np.isclose(x, 180):
        return "180°"
    if x < 180:
        return f"{int(round(x))}°E"
    return f"{int(round(360 - x))}°W"


def lat_label(y, _pos=None):
    y = int(round(y))
    return f"{y}°N" if y > 0 else (f"{-y}°S" if y < 0 else "0°")


def phase_color(value, threshold=0.5):
    if value >= threshold:
        return COLORS["el_nino"]
    if value <= -threshold:
        return COLORS["la_nina"]
    return COLORS["neutral"]


# ---------------------------------------------------------------------------
# Downloading
# ---------------------------------------------------------------------------
def fetch_text(key: str, local_file: str | None = None, refresh: bool = False) -> str:
    """Return the text of a NOAA file: a local copy if given, else a cached download."""
    if local_file:
        return Path(local_file).read_text()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIR / CACHE_NAMES.get(key, Path(URLS[key]).name)
    if cached.exists() and not refresh:
        return cached.read_text()

    print(f"Downloading {URLS[key]} ...")
    req = urllib.request.Request(URLS[key], headers={"User-Agent": "enso-public-viz/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            f"Could not download {URLS[key]} ({exc}).\n"
            f"Download it in a browser and pass it with --file."
        )
    text = raw.decode("utf-8", errors="replace")
    cached.write_text(text)
    return text


# ---------------------------------------------------------------------------
# NOAA index parsers
# ---------------------------------------------------------------------------
def _parse_seasonal(text: str) -> pd.Series:
    """Parse CPC 3-month files (SEAS YR [TOTAL] ANOM). Anomaly = last column.
    Each 3-month value is placed on the middle month (DJF -> January)."""
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3 or parts[0] not in SEASON_CENTER_MONTH:
            continue
        seas, year, anom = parts[0], int(parts[1]), float(parts[-1])
        if anom < -90:  # missing-value codes
            continue
        rows.append((pd.Timestamp(year=year, month=SEASON_CENTER_MONTH[seas], day=1), anom, seas))
    s = pd.Series({d: a for d, a, _ in rows}).sort_index()
    s.attrs["season"] = {d: seas for d, _, seas in rows}
    return s


def find_events(s, threshold=0.5, min_len=5):
    """NOAA's event rule: runs of >= min_len consecutive seasons at or beyond `threshold`
    (use a negative threshold for La Niña). Returns a list of sub-series."""
    events, run = [], []
    hit = (lambda v: v >= threshold) if threshold >= 0 else (lambda v: v <= threshold)
    for t, v in s.items():
        if hit(v):
            run.append(t)
        else:
            if len(run) >= min_len:
                events.append(s[run])
            run = []
    if len(run) >= min_len:
        events.append(s[run])
    return events


def event_label(ev):
    """'1997–98' style name for an event (a season starting Jan–Feb belongs to the previous winter)."""
    y0 = ev.index[0].year if ev.index[0].month >= 3 else ev.index[0].year - 1
    y1 = ev.index[-1].year
    return f"{y0}–{str(y1)[-2:]}" if y1 > y0 else str(y0)


def load_roni(local_file=None, refresh=False) -> pd.Series:
    s = _parse_seasonal(fetch_text("roni", local_file, refresh))
    s.name = "RONI"
    return s


def load_oni(local_file=None, refresh=False) -> pd.Series:
    s = _parse_seasonal(fetch_text("oni", local_file, refresh))
    s.name = "ONI"
    return s


def load_nino34_monthly(local_file=None, refresh=False) -> pd.Series:
    """Monthly Niño 3.4 anomaly from CPC sstoi.indices (last column)."""
    rows = []
    for line in fetch_text("sstoi", local_file, refresh).splitlines():
        parts = line.split()
        if len(parts) < 10 or not parts[0].isdigit():
            continue
        rows.append((pd.Timestamp(year=int(parts[0]), month=int(parts[1]), day=1), float(parts[-1])))
    s = pd.Series(dict(rows)).sort_index()
    s.name = "Niño 3.4 anomaly (°C)"
    return s


def load_wwv_pmel(local_file=None, refresh=False, column=1) -> pd.Series:
    """Warm water volume from the PMEL text file.

    The file has a commented header followed by numeric rows whose first column
    is the date (YYYYMM, or a decimal year). `column` picks which numeric column
    to use (0 = date). Header lines are printed so you can confirm the choice;
    if your copy of the file is laid out differently, change --wwv-col.
    """
    text = fetch_text("wwv", local_file, refresh)
    header, rows = [], []
    for line in text.splitlines():
        parts = line.replace(",", " ").split()
        if not parts:
            continue
        try:
            first = float(parts[0])
        except ValueError:
            header.append(line)
            continue
        if first > 100000:                       # YYYYMM
            ts = pd.Timestamp(year=int(first) // 100, month=int(first) % 100, day=1)
        else:                                    # decimal year
            yr = int(first)
            month = int(round((first - yr) * 12 + 0.5))
            ts = pd.Timestamp(year=yr, month=min(max(month, 1), 12), day=1)
        rows.append((ts, float(parts[column])))
    if header:
        print("PMEL WWV header (check that column", column, "is the one you want):")
        for h in header[:12]:
            print("   ", h)
    s = pd.Series(dict(rows)).sort_index()
    s.name = "Warm water volume"
    return s


def load_global_temp(refresh=False, ytd=False) -> pd.Series:
    """NOAA NCEI global surface temperature vs the 1901-2000 average, indexed by year."""
    text = fetch_text("global_ytd" if ytd else "global_annual", refresh=refresh)
    df = pd.read_csv(io.StringIO(text), comment="#")
    s = pd.Series(df.iloc[:, 1].values, index=df.iloc[:, 0].astype(int).values)
    s.name = "Global temperature vs 1901-2000 (°C)"
    return s


def _cpc_rows(key, refresh):
    """Strip a CPC table page to text; return (issued 'Month YYYY', [(season, [numbers])])."""
    import html as _html
    import re

    text = fetch_text(key, refresh=refresh)
    text = re.sub(r"(?s)<!--.*?-->", " ", text)            # old issues are left in comments
    text = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", text)))
    issued = re.search(r"Issued ([A-Z][a-z]+ \d{4})", text)
    rows = re.findall(r"\b([JFMASOND]{3}) [A-Z][a-z]{2} [A-Z][a-z]{2} [A-Z][a-z]{2}((?: -?\d+(?:\.\d+)?)+)", text)
    if not issued or not rows:
        raise SystemExit(f"Could not read the CPC table at {URLS[key]} - the page layout may have changed.")
    return issued.group(1), [(seas, [float(v) for v in nums.split()]) for seas, nums in rows]


def _season_dates(seasons, issued):
    """Centre-month timestamps for consecutive CPC seasons, starting near the issue month."""
    issue = pd.Timestamp(issued)
    year = issue.year
    out, prev = [], None
    for seas in seasons:
        m = SEASON_CENTER_MONTH[seas]
        if prev is None and m > issue.month + 1:     # first season can't be later than next month
            year -= 1
        if prev is not None and m < prev:
            year += 1
        out.append(pd.Timestamp(year=year, month=m, day=1))
        prev = m
    return out


def load_cpc_outlook(refresh=False) -> pd.DataFrame:
    """CPC official RONI forecast: percentiles p5..p95 for the next 9 seasons."""
    issued, rows = _cpc_rows("cpc_outlook", refresh)
    cols = ["p5", "p15", "p25", "p50", "p75", "p85", "p95"]
    df = pd.DataFrame([r[1][:7] for r in rows], columns=cols,
                      index=_season_dates([r[0] for r in rows], issued))
    df["season"] = [r[0] for r in rows]
    df.attrs["issued"] = issued
    return df


def load_cpc_strengths(refresh=False) -> pd.DataFrame:
    """CPC strength probabilities (%) per season, columns from strongest La Niña to strongest El Niño."""
    issued, rows = _cpc_rows("cpc_strengths", refresh)
    cols = ["ln_vstrong", "ln_strong", "ln_moderate", "ln_weak", "neutral",
            "en_weak", "en_moderate", "en_strong", "en_vstrong"]
    df = pd.DataFrame([r[1][:9] for r in rows], columns=cols,
                      index=_season_dates([r[0] for r in rows], issued))
    df["season"] = [r[0] for r in rows]
    df.attrs["issued"] = issued
    return df


# ---------------------------------------------------------------------------
# GODAS helpers (your files: data/godasClimatologyData_{depth}m.nc, var "deepTemp")
# ---------------------------------------------------------------------------
GODAS_DEPTHS = list(range(5, 215, 10))


def godas_path(data_dir, depth):
    return Path(data_dir) / f"godasClimatologyData_{int(depth)}m.nc"


def _to_celsius(da):
    return da - 273.15 if float(da.mean()) > 100 else da


def godas_equatorial_section(data_dir, dates, lat_band=(-2, 2), lon_range=(120, 280),
                             depths=None, clim=("1991-01-01", "2020-12-31"), raw_dir=None):
    """Return (depths, lons, anomalies[date, depth, lon], temps[date, depth, lon]) in °C.

    Months come from the depth files (godasClimatologyData_{depth}m.nc); months after
    those files end come from NOAA's yearly GODAS files in `raw_dir` (pottmp.YYYY.nc,
    downloaded by `download_godas_year`). Anomalies always use the depth files'
    1991-2020 monthly normals, so old and new months are directly comparable."""
    import xarray as xr

    raw_dir = Path(raw_dir or GODAS_RAW_DIR)
    depths = depths or [d for d in GODAS_DEPTHS if godas_path(data_dir, d).exists()]
    if not depths:
        raise SystemExit(f"No godasClimatologyData_*m.nc files found in {data_dir}")
    months = [pd.Timestamp(t).to_period("M") for t in dates]
    raw = {}
    for y in sorted({m.year for m in months}):
        p = raw_dir / f"pottmp.{y}.nc"
        if p.exists():
            raw[y] = xr.open_dataset(p)

    def band_mean(da):
        da = _to_celsius(da.sel(lat=slice(*lat_band), lon=slice(*lon_range)))
        return da.weighted(np.cos(np.deg2rad(da["lat"]))).mean("lat").load()

    anoms, temps, lons = [], [], None
    try:
        for d in depths:
            with xr.open_dataset(godas_path(data_dir, d)) as ds:
                band = band_mean(ds["deepTemp"])
            have = set(pd.to_datetime(band["time"].values).to_period("M"))
            extra = [band_mean(raw[y]["pottmp"].sel(level=float(d))) for y in raw
                     if not any(m.year == y for m in have)]
            if extra:
                band = xr.concat([band] + [e.transpose("time", "lon") for e in extra], "time")
            base = band.sel(time=slice(*clim))
            if base.sizes["time"] < 24:   # fall back to whole record
                base = band
            clim_m = base.groupby("time.month").mean("time")
            anom = band.groupby("time.month") - clim_m
            index = pd.to_datetime(band["time"].values).to_period("M")
            a_rows, t_rows = [], []
            for m in months:
                hit = np.flatnonzero(index == m)
                if not len(hit):
                    raise SystemExit(f"No GODAS data for {m} at {d} m. For a year after your depth files "
                                     f"end, run download_godas_year({m.year}) or put pottmp.{m.year}.nc "
                                     f"in {raw_dir}.")
                a_rows.append(anom.isel(time=hit[0]).values)
                t_rows.append(band.isel(time=hit[0]).values)
            anoms.append(a_rows)
            temps.append(t_rows)
            lons = band["lon"].values
    finally:
        for ds in raw.values():
            ds.close()
    anoms = np.transpose(np.array(anoms), (1, 0, 2))
    temps = np.transpose(np.array(temps), (1, 0, 2))
    return np.array(depths), lons, anoms, temps


def download_godas_year(year, refresh=False):
    """Fetch NOAA PSL's yearly GODAS file (all depths, ~65 MB) into data/godas_raw/."""
    p = GODAS_RAW_DIR / f"pottmp.{year}.nc"
    if p.exists() and not refresh:
        return p
    GODAS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    url = f"https://downloads.psl.noaa.gov/Datasets/godas/pottmp.{year}.nc"
    print(f"Downloading {url} ...")
    urllib.request.urlretrieve(url, p)
    return p


def godas_wwv(data_dir, lat=(-5, 5), lon=(120, 280), threshold_c=20.0, layer_m=10.0):
    """Warm water volume from your GODAS depth files: volume of water warmer than
    20 °C in the equatorial band, in units of 10^14 m^3.

    Each file is treated as a layer `layer_m` thick centred on its depth
    (5, 15, ... 205 m -> 10 m layers). This mirrors the PMEL definition
    (volume above the 20 °C isotherm, 5°S-5°N, 120°E-80°W) closely enough for
    a public graphic; quote it as "computed from GODAS".
    """
    import xarray as xr

    R = 6.371e6
    total = None
    for d in GODAS_DEPTHS:
        p = godas_path(data_dir, d)
        if not p.exists():
            continue
        with xr.open_dataset(p) as ds:
            da = _to_celsius(ds["deepTemp"].sel(lat=slice(*lat), lon=slice(*lon))).load()
        dlat = np.deg2rad(float(np.abs(np.diff(da["lat"].values).mean())))
        dlon = np.deg2rad(float(np.abs(np.diff(da["lon"].values).mean())))
        area = (R ** 2) * np.cos(np.deg2rad(da["lat"])) * dlat * dlon     # m^2 per cell, by lat
        warm = (da > threshold_c).where(np.isfinite(da), 0)
        vol = (warm * area).sum(("lat", "lon")) * layer_m
        total = vol if total is None else total + vol
    if total is None:
        raise SystemExit(f"No godasClimatologyData_*m.nc files found in {data_dir}")
    s = (total / 1e14).to_series()
    s.index = pd.to_datetime(s.index).to_period("M").to_timestamp()
    s.name = "Warm water volume (10¹⁴ m³)"
    return s


def godas_box_mean(data_dir, depth, lat, lon):
    """Area-weighted box-mean anomaly (°C) from one GODAS depth file."""
    import xarray as xr

    with xr.open_dataset(godas_path(data_dir, depth)) as ds:
        da = _to_celsius(ds["deepTemp"].sel(lat=slice(*lat), lon=slice(*lon))).load()
    clim = da.groupby("time.month").mean("time")
    anom = da.groupby("time.month") - clim
    s = anom.weighted(np.cos(np.deg2rad(da["lat"]))).mean(("lat", "lon")).to_series()
    s.index = pd.to_datetime(s.index).to_period("M").to_timestamp()
    return s


def monthly_anomaly(s: pd.Series) -> pd.Series:
    return s - s.groupby(s.index.month).transform("mean")


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()
