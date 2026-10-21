# SDSU Climate Informatics Lab · ENSO Visualizations

Figures and website explaining the 2026/2027 El Niño and its effects on Southern California,
built entirely from public NOAA data. By Dylan Hahn.

**Website:** https://dylhahn.github.io/SCIL-ENSO/

| Tab | Contents |
|---|---|
| **El Niño 2026/2027** › Overview | "What's happening now", "Why this El Niño stands out", development compared with every El Niño since 1950 (animation and interactive explorer), NOAA forecast |
| › Sea Surface Temperature | Sea surface animation, maps by event, Niño regions, equatorial SST Hovmöller |
| › Ocean Heat Below the Surface | 3D animation and interactive 3D model, warm water and warm-water layers, equatorial sections and Hovmöller |
| › Kelvin Waves & Sea Level | Kelvin wave tracker and interactive 3D sea level |
| › Records & Forecasts | Event ranking, forecast verification, global temperature |
| **Southern California** › Heat | Summer 2026 anomalies, station warm nights and hot days, marine heatwaves, warming since 1895 |
| › Rainfall | NOAA seasonal outlook, strong El Niño winters, station rainfall by ENSO phase |
| Methods & Data | Data sources, definitions, glossary, methods by figure, limitations, citation |

Every page has a search box that finds figures (and glossary terms) across all tabs.

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

After the update, re-read the bold takeaways in `site_config.py` (FIGURE_NOTES): they describe the
current data and may need rewording as the event evolves.

GitHub Pages republishes the site a minute or two after the push. Other options:

```bash
python update_site.py                       # rebuild from cached data
python update_site.py --pages socal-heat    # rebuild one tab's figures (el-nino, surface, ocean, kelvin, records, socal-heat, socal-precip)
python update_site.py --site-only           # rewrite the pages only (e.g. after editing text)
python update_site.py --pages el-nino --figures anim_3d.py   # rebuild only some figures
python summary.py                           # print the "What's happening now" summary
python hovmoller_sst.py                     # build any single figure into figures_public/
```

## Repository layout

```
update_site.py          one command: build all figures, then write docs/
site_config.py          tabs, figures (in order), short titles, captions, page text, per-figure
                        takeaways and "How to read" notes (FIGURE_NOTES), hover glossary (GLOSSARY)
summary.py              "What's happening now" and "Why this El Niño is different", from the latest data
site/explorer.html      interactive event explorer (data from interactive_data.py)
site/page.html          page layout, styles, glossary tooltips and click-to-play animations
site/methods.html       Methods & data text;  site/explainer.html  "Start here" diagram and text
docs/                   the published website (GitHub Pages)

Figures, El Niño tabs             Figures, Southern California tabs
  anim_timeseries.py                socal_warming_since_1895.py
  interactive_data.py               socal_marine_heat.py
  anim_sst.py                       socal_summer_anomalies.py
  anim_upper_ocean.py               socal_station_heat.py
  warm_water_before_onset.py
  anim_warm_water.py
  anim_warm_layers.py
  hovmoller_winds.py    (uses enso_winds.py)
  anim_kelvin.py        (uses enso_sealevel.py)
  interactive_sealevel_data.py  (3D sea level view: site/sealevel3d.html)
  anim_sealevel_3d.py   animated version (not on the site; for iCHARM or slides)
  anim_3d.py
  interactive_3d_data.py   (3D view: site/ocean3d.html)
  roni_vs_past_events.py            socal_precip_outlook.py   (uses socal_outlook.py)
  forecast_verification.py          socal_precip_el_nino_winters.py
  surface_comparison.py             socal_station_precip.py
  subsurface_comparison.py
  hovmoller_sst.py
  hovmoller_upper_ocean.py
  nino_regions.py
  el_nino_type.py
  event_ranking.py
  global_temperature.py
  event_timeseries.py   static version, not on the site; its series feed the two at the top

Shared modules
  enso_common.py      style, colour scales, NOAA index and forecast loaders, GODAS helpers
  enso_stats.py       gridded datasets (ERSST, GPCP, NOAAGlobalTemp)
  enso_equatorial.py  Hovmöller layout
  enso_marine.py      OISST: Southern California Bight daily, tropical Pacific monthly
  enso_nclimgrid.py   nClimGrid for Southern California (read remotely, cached)
  enso_socal.py       GHCN-Daily stations, ENSO categories
  enso_anim.py        animated WebP output
  enso_sealevel.py    daily satellite sea level along the equator (Kelvin waves)
  enso_winds.py       daily equatorial surface winds (NCEI Blended Sea Winds; read remotely, cached)

archive/                earlier figures no longer on the site (see archive/README.md)
data/                   downloaded data, not in the repository (see below)
figures_public/         local build output, not in the repository
```

An interactive chart is a script whose name starts with `interactive` and writes a JSON file
(`--out x.json`); `update_site.py` places it in the page with `site/explorer.html`.

To export GODAS potential-temperature anomalies as NetCDF (e.g. for iCHARM), see
`godas_anomalies.py`.

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
| `data/sealevel/` | NOAA blended altimetry: equatorial band and 15°S–15°N (daily since July 2025; 2017–2024 baseline) |
| `data/nclimgrid/`, `data/ghcn/` | nClimGrid Southern California window; GHCN-Daily stations |
| `data/cpc_outlook/`, `data/fire_outlook/` | CPC seasonal outlook GIS files; NIFC fire outlook (archive only) |

The figures that compare past years below the surface (`subsurface_comparison.py`,
`hovmoller_upper_ocean.py`, `anim_upper_ocean.py`, `event_timeseries.py`) need the GODAS depth
files in `data/godas/`, which are not part of this repository.

## Citation

Hahn, D. (2026). *ENSO Visualizations: The 2026/2027 El Niño in historical context.* SDSU Climate Informatics Lab. https://dylhahn.github.io/SCIL-ENSO/
