# SCIL ENSO

Figures and website explaining the 2026–27 El Niño and its effects on Southern California,
built entirely from public NOAA data. By Dylan Hahn.

**Website:** https://dylhahn.github.io/SCIL-ENSO/

| Tab | Contents |
|---|---|
| El Niño 2026 | "What's happening now" summary, animations, comparisons with 1982, 1997 and 2015, Hovmöller diagrams, Niño regions, event ranking, forecast verification, global temperature |
| Southern California Heat | Warming since 1895, marine heatwaves in the Southern California Bight, summer 2026 anomaly maps, station warm nights and hot days |
| Southern California Precipitation | NOAA seasonal outlook, precipitation in strong El Niño winters, station rainfall by ENSO phase |
| Methods & data | Data sources, definitions, methods by figure, limitations, citation |

## Monthly update

Use the `enso` conda environment (`conda env create -f environment.yml` on a new computer).
NOAA's ENSO update comes out on the 2nd Thursday of the month and its seasonal outlooks on the
3rd Thursday; update after the 3rd Thursday to pick up both.

```bash
cd ~/Projects/enso_viz
conda activate enso
python update_site.py --refresh          # download the latest data, rebuild every figure and page
git add docs && git commit -m "Update for <month>" && git push
```

GitHub Pages republishes the site a minute or two after the push. Other options:

```bash
python update_site.py                       # rebuild from cached data
python update_site.py --pages socal-heat    # rebuild one tab's figures (el-nino, socal-heat, socal-precip)
python update_site.py --site-only           # rewrite the pages only (e.g. after editing text)
python summary.py                           # print the "What's happening now" summary
python hovmoller_sst.py                     # build any single figure into figures_public/
```

## Repository layout

```
update_site.py          one command: build all figures, then write docs/
site_config.py          tabs, figures (in order), short titles, captions and page text
summary.py              "What's happening now", computed from the latest data
site/page.html          page layout and styles;  site/methods.html  Methods & data text
docs/                   the published website (GitHub Pages)

Figures, El Niño tab              Figures, Southern California tabs
  anim_sst.py                       socal_warming_since_1895.py
  anim_upper_ocean.py               socal_marine_heat.py
  roni_vs_past_events.py            socal_summer_anomalies.py
  event_timeseries.py               socal_station_heat.py
  surface_comparison.py             socal_precip_outlook.py   (uses socal_outlook.py)
  subsurface_comparison.py          socal_precip_el_nino_winters.py
  hovmoller_sst.py                  socal_station_precip.py
  hovmoller_upper_ocean.py
  nino_regions.py
  event_ranking.py
  forecast_verification.py
  global_temperature.py

Shared modules
  enso_common.py      style, colour scales, NOAA index and forecast loaders, GODAS helpers
  enso_stats.py       gridded datasets (ERSST, GPCP, NOAAGlobalTemp)
  enso_equatorial.py  Hovmöller layout
  enso_marine.py      OISST: Southern California Bight daily, tropical Pacific monthly
  enso_nclimgrid.py   nClimGrid for Southern California (read remotely, cached)
  enso_socal.py       GHCN-Daily stations, ENSO categories
  enso_anim.py        animated WebP output

archive/                earlier figures no longer on the site (see archive/README.md)
data/                   downloaded data, not in the repository (see below)
figures_public/         local build output, not in the repository
```

To add a figure: write a script that accepts `--theme`, `--out` (and optionally `--refresh`) and
saves with `enso_common.save(fig, out, alt=...)`, then add it to a page in `site_config.py`.

## Data

All sources are public NOAA products, downloaded on first use and cached in `data/`
(about 400 MB); `--refresh` re-downloads. Details, definitions and limitations are on the
[Methods & data](https://dylhahn.github.io/SCIL-ENSO/methods/) page.

| Folder | Contents |
|---|---|
| `data/noaa_cache/` | CPC RONI, ONI, Niño indices, outlooks and strength probabilities; NCEI global temperature |
| `data/gridded/` | ERSST v5, NOAAGlobalTemp, GPCP |
| `data/godas_raw/` | NOAA PSL yearly GODAS files for the current year |
| `data/godas/` | GODAS depth files `godasClimatologyData_{depth}m.nc` for 1980–2025 (local, not public) |
| `data/oisst/`, `data/oisst_monthly/` | OISST daily (Southern California Bight) and monthly (tropical Pacific) |
| `data/nclimgrid/`, `data/ghcn/` | nClimGrid Southern California window; GHCN-Daily stations |
| `data/cpc_outlook/`, `data/fire_outlook/` | CPC seasonal outlook GIS files; NIFC fire outlook (archive only) |

The figures that compare past years below the surface (`subsurface_comparison.py`,
`hovmoller_upper_ocean.py`, `anim_upper_ocean.py`, `event_timeseries.py`) need the GODAS depth
files in `data/godas/`, which are not part of this repository.

## Citation

Hahn, D. (2026). *SCIL ENSO: The 2026–27 El Niño in historical context.* https://dylhahn.github.io/SCIL-ENSO/
