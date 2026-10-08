# Public ENSO graphics

Matplotlib scripts that explain the 2026 El Niño to a general audience, for
icharm.sdsu.edu. Everything is built from real observations or NOAA's official
forecasts; there is no demo / synthetic-data mode.

## The current set: "2026 El Niño vs. the past"

`python run_current.py` builds these, in reading order, into `figures_public/current/`
(numbered PNGs, a `.alt.txt` alt text for each, and an `index.html` preview).
They use datasets iCHARM hosts or NOAA's official El Niño index, and each one
shows how this event compares with past El Niños.

| # | Script | Graphic | Data |
|---|---|---|---|
| 1 | `story1_super_el_nino.py` | This El Niño month by month vs. the four biggest since 1950, plus NOAA's forecast | CPC RONI + outlook |
| 1b | `eq4_event_timeseries.py` | Anomaly time series for every El Niño since 1950 (Niño 3.4, Niño 1+2, upper ocean) | ERSST v5, GODAS |
| 2 | `compare2_surface.py` | Tropical Pacific surface now vs. the same month of 1982, 1997, 2015 | NOAAGlobalTemp (iCHARM front page) |
| 3 | `compare1_underwater.py` | Top 200 m along the equator now vs. the same month of past super El Niños | GODAS |
| 4 | `fig6_equatorial_cross_section.py` | This year's warm water building and moving east, every two months | GODAS |
| 5 | `stats4_event_ranking.py` | Every El Niño since 1950 by peak, length and total warmth | CPC RONI + outlook |
| 6 | `story4_global_heat.py` | Global temperature records that came with El Niños | NOAA NCEI global temperature |
| 7 | `eq1_sst_hovmoller.py` | Longitude–time (Hovmöller) SST anomalies along the equator, 1982, 1997, 2015, 2026 | ERSST v5 |
| 8 | `eq2_heat_hovmoller.py` | Hovmöller of upper-200 m temperature anomalies (Kelvin waves) | GODAS |
| 9 | `eq3_nino_regions.py` | Monthly anomalies in Niño 4, 3.4, 3 and 1+2: where the warming is concentrated | CPC Niño indices |

Comparisons default to the latest month with data (GODAS and NOAAGlobalTemp:
August 2026 at the time of writing) and to 1982, 1997, 2015 as past super El Niños;
change with `--month` / `--years`. The yearly GODAS file for the current year
(`data/godas_raw/pottmp.YYYY.nc`, ~65 MB) is downloaded automatically and
re-downloaded with `--refresh` as NOAA adds months.

Everything else (the explainer figures, story and statistics series) still runs;
its earlier output is kept in `figures_public/archive/`.

## Website (GitHub Pages)

The site at https://dylhahn.github.io/SCIL-ENSO is the `docs/` folder of this
repository. To update it after NOAA's monthly releases (2nd Thursday):

```bash
python run_current.py --refresh                      # "El Niño 2026" tab
python run_socal.py --refresh                        # "Southern California" tab
python build_site.py --repo-url https://github.com/DylHahn/SCIL-ENSO
git add docs && git commit -m "Update for <month>" && git push
```

NOAA's ENSO update comes out on the 2nd Thursday of the month and its seasonal
outlook (used on the SoCal tab) on the 3rd Thursday, so a monthly refresh after the
3rd Thursday picks up both.

GitHub republishes the page a minute or two after the push.

Not in the repository: `data/` (NOAA downloads are fetched automatically; the
GODAS depth files `godasClimatologyData_{depth}m.nc` used for past years in
graphics 3–4 are your own preprocessed files) and `figures_public/`.

## The Southern California tab: heat and wildfire

`python run_socal.py` builds these into `figures_public/socal_current/`:

| # | Script | Graphic | Data |
|---|---|---|---|
| 1 | `socal6_warming.py` | Change maps (1996–2025 vs. 1951–1980), warming stripes and regional summer series since 1895 | NOAA nClimGrid monthly |
| 2 | `socal4_heatmap.py` | Summer daytime-high / overnight-low anomaly maps, and regional overnight lows every summer since 1950 | NOAA nClimGrid monthly (SoCal window read over HTTP, cached in `data/nclimgrid/`) |
| 3 | `socal2_heat.py` | Warm nights (≥ 65 °F) and hot days (≥ 90 °F) per summer at four stations | GHCN-Daily |

Archived (scripts kept, not on the site): `socal1_rain.py` (precipitation by ENSO
phase), `socal3_outlook.py` (precipitation and temperature outlook maps) and
`socal5_heat_fire_outlook.py` (official fire-potential and temperature outlooks).

## Folder layout

```
enso_viz/
├── run_current.py           builds the "El Niño 2026" tab  ← start here
├── run_socal.py             builds the "Southern California" tab
├── socal1/2/3_*.py, enso_socal.py   the SoCal graphics and station helpers
├── build_site.py            writes the two-tab website into docs/
├── compare1/2_*.py          this year vs. past El Niños (underwater, surface)
├── eq1/2/3_*.py, enso_equatorial.py   equatorial Pacific Hovmöllers and Niño-region diagnostics
├── story1 … story6_*.py     "Super El Niño, explained" series (run_story.py)
├── stats1 … stats5_*.py     statistics from past events (run_stats.py)
├── fig1 … fig7_*.py         the original seven explainer figures (run_all.py)
├── enso_common.py           shared style, NOAA loaders, GODAS helpers
├── enso_stats.py            seasonal anomalies, event composites, map helpers
├── data/
│   ├── noaa_cache/          NOAA index downloads (refreshed with --refresh)
│   ├── gridded/             GPCP rainfall, NOAAGlobalTemp, ERSST v5 (~260 MB)
│   ├── godas_raw/           NOAA yearly GODAS files for months after your depth files
│   ├── ghcn/                NOAA daily station records (SoCal tab)
│   ├── cpc_outlook/         NOAA seasonal outlook map files (SoCal tab)
│   └── godas/               your GODAS depth files, or a link to them (not in the repo)
└── figures_public/
    ├── current/             the "El Niño 2026" set
    ├── socal_current/       the "Southern California" set
    └── archive/             earlier output
```

Paths are relative to this folder, so the scripts work from any directory.

## Quick start

Use the `enso` conda environment (your base Python doesn't have the packages):

```bash
cd ~/Projects/enso_viz
conda activate enso
python run_current.py --refresh    # the curated set, with NOAA's latest data
```

Without activating: `conda run -n enso python ~/Projects/enso_viz/run_current.py --refresh`.
To set the environment up on another computer: `conda env create -f environment.yml`.

If your GODAS files move, re-point the link:
`ln -sfn /new/path/to/data data/godas`, or pass `--data-dir /path` to fig 4 / fig 6.

## Data notes

- **NOAA files** are downloaded on first use and cached in `data/noaa_cache/`.
  Add `--refresh` to re-download. If a download is blocked, save the file from a
  browser and pass it with `--file` (fig 2), `--roni-file/--oni-file` (fig 3), or
  `--nino-file/--wwv-file` (fig 4).
  - RONI: https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt
  - ONI: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
  - Monthly Niño 3.4: https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices
  - PMEL warm water volume: https://www.pmel.noaa.gov/tao/wwv/data/wwv.dat
- **3-month values** (RONI, ONI) are plotted on the middle month (DJF → January).
- **GODAS depth files** are read from
  `data/godas/godasClimatologyData_{depth}m.nc`, variable `deepTemp`, 0–360° longitude.
  Kelvin is converted to °C automatically.
- **Warm water volume from GODAS** (fig 4 default) = volume of water warmer than
  20 °C in 5°S–5°N, 120°E–80°W, treating each depth file (5, 15 … 205 m) as a
  10 m layer. In the far western Pacific the 20 °C isotherm can sit near or
  below 205 m, so this slightly underestimates the total there; anomalies (what
  the figure plots) are much less affected. Use `--wwv-source pmel` for the
  official PMEL series. Its column layout is printed when loaded; choose the
  column with `--wwv-col` and add `--wwv-is-anomaly` if it is already an anomaly.
- **Forecast probabilities** (fig 7) are read from NOAA CPC's official strength-
  probability table, the same page the story series uses.

## Useful variations

```bash
python fig2_roni_timeline.py --start 1980 --label-top 6
python fig4_wwv_vs_nino34.py --split-year 0                 # one lag curve, all years
python fig4_wwv_vs_nino34.py --nino-source godas            # Niño 3.4 from your 5 m file
python fig6_equatorial_cross_section.py --dates 1997-02 1997-04 1997-06 1997-08
python compare1_underwater.py --month 6 --years 1997 2015 2026
python fig5_walker_circulation.py --layout vertical          # phone / poster friendly
python fig7_forecast_probabilities.py --refresh
```

## "Super El Niño, explained" series (for icharm.sdsu.edu)

Six graphics that walk a general audience from "what is happening" to "what do I
do". Dark theme by default to sit on iCHARM's near-black background
(`--theme light` for anywhere else).

| Script | Graphic | Data |
|---|---|---|
| `story1_super_el_nino.py` | This year's El Niño vs. the past super El Niños, plus NOAA's forecast range | CPC RONI + official RONI outlook & strength probabilities |
| `story2_how_it_works.py` | The wind–ocean feedback loop in four plain steps, with live "right now" numbers | CPC monthly Niño indices + RONI |
| `story3_global_impacts.py` | World maps of typical El Niño droughts, floods and heat (Dec–Feb, Jun–Aug) | none (patterns after NOAA Climate.gov / IRI; edit `REGIONS`) |
| `story4_global_heat.py` | Global temperature since 1950; records that came with El Niño winters | NOAA NCEI global temperature + RONI |
| `story5_timeline.py` | What to expect when: prepare → peak → impacts → global heat → fade | CPC official RONI outlook |
| `story6_prepare.py` | Six preparation cards (heat, drought, fire, floods, health, food) | none (edit `CARDS` to localise) |

```bash
python run_story.py             # build all six + index.html preview
python run_story.py --refresh   # after NOAA's monthly update (2nd Thursday)
```

Output goes to `figures_public/story/`:
- `storyN_*.png`: 2600 px wide, for the web page
- `storyN_*.alt.txt`: alt text for each image (screen readers), written from the live numbers
- `index.html`: the whole sequence with captions, as a preview for the web team

Monthly upkeep: NOAA CPC updates the outlook on the second Thursday of each
month; rerun with `--refresh`. The year-to-date global temperature URL in
`enso_common.URLS["global_ytd"]` names the latest month (`ytd/8/...` = Jan–Aug):
bump that number as NCEI adds months, and the end year of `global_annual` each January.

## "What El Niño has done before": statistics series

Five graphics built from past events, as a data-driven companion to the story
series (same dark theme, alt text and `index.html` preview in `figures_public/stats/`).

| Script | Graphic | Data |
|---|---|---|
| `stats1_rain_change.py` | Average rainfall change (%) in past El Niños, Dec–Feb and Jun–Aug | GPCP v2.3 (1979–) |
| `stats2_rain_odds.py` | How many past El Niños brought a drier / wetter season at each place | GPCP v2.3 |
| `stats3_temperature.py` | El Niño's temperature fingerprint, warming trend removed | NOAAGlobalTemp v6 (1950–) |
| `stats4_event_ranking.py` | Every El Niño since 1950 by peak, length and total warmth; this one finished with NOAA's forecast | CPC RONI + outlook |
| `stats5_how_often.py` | Time spent in El Niño / La Niña / neutral, gaps between El Niños, 2–7-year rhythm | CPC RONI |

Method for the maps (details in `enso_stats.py`): seasonal means → difference
from the 1991–2020 normal → linear trend removed at every grid point → average
(or count) over El Niño seasons, picked as winters with Dec–Feb RONI ≥ +1.0
(`--threshold` to change) and the Jun–Aug before each. Maps 1 and 3 are coloured
only where at least 3 in 4 events agreed on the sign; map 2's middle bin
(3–5 of 8) is left clear because that's what chance alone gives.

```bash
python run_stats.py              # build all five + index.html preview
python run_stats.py --refresh    # re-download (GPCP updates monthly, ~2 months behind)
```
