"""
Build the GitHub Pages site (docs/) from the curated graphics: two tabs.

    python run_current.py --refresh     # 1a. rebuild "El Niño 2026" graphics
    python run_socal.py --refresh       # 1b. rebuild "Southern California" graphics
    python build_site.py --repo-url https://github.com/DylHahn/SCIL-ENSO     # 2. write docs/
    git add docs && git commit -m "Update for <month>" && git push           # 3. publish

GitHub Pages serves docs/ from the main branch, so step 3 is all it takes to
update the live site.
"""
import argparse
import datetime as dt
import html
import shutil

from PIL import Image

import run_current
import run_socal
import run_socal_precip
from run_story import HERE

DOCS = HERE / "docs"

# Short titles for each page's table of contents, by script
TITLES = {
    "story1_super_el_nino.py": "Event development vs. past very strong events",
    "compare2_surface.py": "Surface temperature anomalies by event",
    "compare1_underwater.py": "Subsurface temperature anomalies by event",
    "fig6_equatorial_cross_section.py": "Subsurface evolution, 2026",
    "stats4_event_ranking.py": "Ranking of El Niño events since 1950",
    "story4_global_heat.py": "Global temperature and El Niño",
    "eq1_sst_hovmoller.py": "Equatorial SST evolution (Hovmöller)",
    "eq2_heat_hovmoller.py": "Upper-ocean heat content (Hovmöller)",
    "eq3_nino_regions.py": "Warming across the Niño regions",
    "socal5_heat_fire_outlook.py": "Official heat and wildfire outlook",
    "socal6_warming.py": "Long-term increase in summer heat",
    "socal3_outlook_prcp.py": "NOAA seasonal precipitation outlook",
    "socal7_precip_composite.py": "Precipitation in strong El Niño winters",
    "socal1_rain.py": "Station precipitation by ENSO phase",
    "anim1_sst.py": "Animation: surface anomalies, 2026 and 1997",
    "anim2_subsurface.py": "Animation: subsurface anomalies, 2026 and 1997",
    "eq5_forecast_verification.py": "Verification of NOAA's 2026 forecasts",
    "socal8_marine_heat.py": "Marine heat in the Southern California Bight",
    "eq4_event_timeseries.py": "Anomaly time series across events",
    "socal4_heatmap.py": "Summer 2026 temperature anomalies",
    "socal2_heat.py": "Warm nights and hot days by station",
}

PAGES = [
    dict(
        slug="", tab="El Niño 2026", series=run_current.CURRENT, src=run_current.OUT,
        title="The 2026–27 El Niño in historical context", kicker="El Niño 2026–27",
        h1="The 2026–27 El Niño in historical context",
        lede="A strong El Niño is developing in the equatorial Pacific. These figures compare its surface and "
             "subsurface evolution with the strongest events since 1950, using NOAA observations, reanalysis "
             "and official forecasts.",
        extra="",
        data=["Relative Oceanic Niño Index (RONI), outlook and strength probabilities: NOAA Climate Prediction Center",
              "NCEP GODAS ocean reanalysis: NOAA NCEP, via NOAA PSL",
              "NOAAGlobalTemp v6 and global temperature series: NOAA NCEI",
              "ERSST v5 sea surface temperature: NOAA NCEI, via NOAA PSL",
              "Monthly Niño region indices (OISST v2.1): NOAA Climate Prediction Center"],
    ),
    dict(
        slug="socal", tab="Southern California Heat", series=run_socal.SOCAL, src=run_socal.OUT,
        title="Southern California Heat", kicker="Southern California Heat",
        h1="Southern California heat",
        lede="How summer heat across Southern California has increased since 1895, how the summer of 2026 "
             "compares, and how warm nights and hot days have changed at individual stations.",
        extra="""<section class="note">
  <h2>El Niño and wildfire</h2>
  <p>The influence of El Niño on Southern California wildfire is indirect. Above-normal winter precipitation
  typically reduces fire activity during the wet season but increases the growth of grasses and fine fuels, which
  cure during the following summer and autumn and can elevate the potential for rapidly spreading grass fires.
  There is no robust relationship between ENSO and Santa Ana wind events, which drive the largest autumn fires.
  Fire danger on a given day depends on wind, humidity and fuel moisture; official fire-weather products should
  be used for decisions.</p>
  <h2>Official forecasts and warnings</h2>
  <ul>
    <li>Day-to-day weather, heat and Red Flag (fire weather) warnings:
      <a href="https://www.weather.gov/lox/">NWS Los Angeles/Oxnard</a> ·
      <a href="https://www.weather.gov/sgx/">NWS San Diego</a></li>
    <li>Wildfire outlooks for Southern California:
      <a href="https://gacc.nifc.gov/oscc/predictive/outlooks/">Predictive Services, South Ops</a></li>
    <li>Active fires and evacuations: <a href="https://www.fire.ca.gov/incidents">CAL FIRE incidents</a></li>
    <li>Heat safety: <a href="https://www.weather.gov/safety/heat">National Weather Service</a></li>
    <li>Seasonal outlook maps for the whole US:
      <a href="https://www.cpc.ncep.noaa.gov/products/predictions/long_range/seasonal.php">NOAA Climate Prediction Center</a></li>
  </ul>
</section>""",
        data=["Gridded monthly temperature (nClimGrid) and daily station records (GHCN-Daily): NOAA NCEI",

              "Relative Oceanic Niño Index (RONI): NOAA Climate Prediction Center"],
    ),
    dict(
        slug="socal-precip", tab="Southern California Precipitation", series=run_socal_precip.SOCAL_PRECIP,
        src=run_socal_precip.OUT,
        title="Southern California Precipitation", kicker="Southern California Precipitation",
        h1="Southern California precipitation and El Niño",
        lede="NOAA's seasonal precipitation outlook for the coming winter, and the precipitation Southern "
             "California received during past strong El Niño winters, region-wide and at individual stations.",
        extra="""<section class="note">
  <h2>Interpreting El Niño and Southern California rainfall</h2>
  <p>Strong El Niño winters have usually, but not always, brought above-normal precipitation to Southern
  California; the very strong 2015–16 event was drier than normal. Heavy rain on recently burned slopes raises the
  risk of flooding and debris flows. Seasonal outlooks give probabilities for a whole season and are not forecasts
  of individual storms.</p>
  <h2>Official forecasts and warnings</h2>
  <ul>
    <li>Storm, flood and flash-flood forecasts and warnings:
      <a href="https://www.weather.gov/lox/">NWS Los Angeles/Oxnard</a> ·
      <a href="https://www.weather.gov/sgx/">NWS San Diego</a></li>
    <li>Seasonal outlook maps for the whole US:
      <a href="https://www.cpc.ncep.noaa.gov/products/predictions/long_range/seasonal.php">NOAA Climate Prediction Center</a></li>
  </ul>
</section>""",
        data=["Gridded monthly precipitation (nClimGrid) and daily station records (GHCN-Daily): NOAA NCEI",
              "Official 3-month precipitation outlooks: NOAA Climate Prediction Center",
              "Relative Oceanic Niño Index (RONI): NOAA Climate Prediction Center"],
    ),
]

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SCIL ENSO · {title}</title>
<meta name="description" content="{description}">
<style>
  :root {{ --bg: #0d0d0e; --surface: #1c1c1b; --text: #f4f4f1; --text-2: #c3c2b7; --muted: #8a8984;
           --accent: #e8574a; --line: #2b2b2a; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--text);
          font: 17px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width: 1120px; margin: 0 auto; padding: 24px 16px 72px; }}
  .site {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 4px 16px;
           padding: 8px 0 16px; }}
  .site .brand {{ font-weight: 700; font-size: 20px; letter-spacing: .06em; color: var(--text); text-decoration: none; }}
  .site .brand span {{ color: var(--accent); }}
  .site .author {{ color: var(--text-2); font-size: 15px; }}
  .tabs {{ display: flex; gap: 4px; border-bottom: 1px solid var(--line); margin: 0 0 40px; flex-wrap: wrap; }}
  .tabs a {{ padding: 10px 16px; color: var(--text-2); text-decoration: none; border-bottom: 2px solid transparent;
             margin-bottom: -1px; font-weight: 500; }}
  .tabs a:hover {{ color: var(--text); }}
  .tabs a[aria-current="page"] {{ color: var(--text); border-bottom-color: var(--accent); }}
  header p.kicker {{ color: var(--accent); font-weight: 600; letter-spacing: .04em; text-transform: uppercase;
                     font-size: 14px; margin: 0 0 8px; }}
  h1 {{ font-size: clamp(28px, 4.5vw, 44px); line-height: 1.15; margin: 0 0 16px; }}
  h2 {{ font-size: 22px; margin: 32px 0 8px; }}
  .lede {{ color: var(--text-2); font-size: 19px; max-width: 760px; margin: 0 0 12px; }}
  .meta {{ color: var(--muted); font-size: 14px; margin: 0 0 40px; }}
  .toc ol {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 8px 24px;
             padding: 20px 24px 20px 44px; margin: 0 0 56px; background: var(--surface); border-radius: 10px; }}
  .toc a {{ color: var(--text-2); text-decoration: none; }}
  .toc a:hover {{ color: var(--text); text-decoration: underline; }}
  figure {{ margin: 0 0 64px; scroll-margin-top: 24px; }}
  figure a {{ display: block; }}
  img {{ width: 100%; height: auto; display: block; border-radius: 10px; border: 1px solid var(--line); }}
  figcaption {{ margin-top: 14px; color: var(--text-2); max-width: 820px; }}
  figcaption b {{ color: var(--text); }}
  .note {{ background: var(--surface); border-radius: 10px; padding: 8px 28px 20px; margin: 0 0 56px;
           color: var(--text-2); }}
  .note h2 {{ color: var(--text); }}
  .note a, footer a {{ color: var(--text-2); }}
  .note a:hover, footer a:hover {{ color: var(--text); }}
  footer {{ border-top: 1px solid var(--line); padding-top: 24px; color: var(--muted); font-size: 15px; }}
  footer ul, .note ul {{ padding-left: 20px; }}
</style>
</head>
<body>
<main>
<div class="site">
  <a class="brand" href="{home}">SCIL <span>ENSO</span></a>
  <span class="author">Dylan Hahn</span>
</div>
<nav class="tabs" aria-label="Pages">
{tabs}
</nav>
<header>
  <p class="kicker">{kicker}</p>
  <h1>{h1}</h1>
  <p class="lede">{lede}</p>
  <p class="meta">Updated {updated}. Data: NOAA observations, reanalysis and official forecasts. Select a figure to view it at full resolution.</p>
</header>
<nav class="toc" aria-label="Figures on this page"><ol>
{toc}
</ol></nav>
{figures}
{extra}
<footer>
  <p><b>Data</b> (all public, from NOAA):</p>
  <ul>
{data}
  </ul>
  <p>Explore NOAA datasets yourself on <a href="https://icharm.sdsu.edu/">iCHARM</a>.{repo}</p>
</footer>
</main>
</body>
</html>
"""


def build_page(page, repo_url):
    src, series = page["src"], page["series"]
    missing = [s for i, (s, _, _) in enumerate(series, 1) if not (src / f"{i:02d}_{s.replace('.py', '.png')}").exists()]
    if missing:
        raise SystemExit(f"Build the graphics first (run_current.py / run_socal.py); missing: {', '.join(missing)}")

    page_dir = DOCS / page["slug"] if page["slug"] else DOCS
    img_dir = page_dir / "img"
    if img_dir.exists():
        shutil.rmtree(img_dir)            # drop images of graphics that were retired
    img_dir.mkdir(parents=True)

    toc, figures = [], []
    for i, (script, _, caption) in enumerate(series, 1):
        stem = f"{i:02d}_{script.replace('.py', '')}"
        shutil.copy2(src / f"{stem}.png", img_dir / f"{stem}.png")
        # animations: an animated WebP sits next to the PNG (the PNG stays as the full-size final frame)
        animated = (src / f"{stem}.webp").exists()
        if animated:
            shutil.copy2(src / f"{stem}.webp", img_dir / f"{stem}.webp")
        shown = f"{stem}.webp" if animated else f"{stem}.png"
        alt_file = src / f"{stem}.alt.txt"
        alt = alt_file.read_text().strip() if alt_file.exists() else caption
        short = TITLES.get(script, script.replace(".py", ""))
        toc.append(f'  <li><a href="#g{i}">{html.escape(short)}</a></li>')
        with Image.open(img_dir / shown) as im:
            w, h = im.size
        figures.append(
            f'<figure id="g{i}"><a href="img/{shown}" target="_blank" rel="noopener">'
            # width/height reserve the space before the image arrives; with only a few images
            # everything loads up front so no figure is skipped near the bottom of the page
            f'<img src="img/{shown}" alt="{html.escape(alt)}" width="{w}" height="{h}" decoding="async"></a>'
            f"<figcaption><b>Figure {i}. {html.escape(short)}.</b> {html.escape(caption)}"
            + (f' <a href="img/{stem}.png" target="_blank" rel="noopener">Still image of the final frame.</a>'
               if animated else "") + "</figcaption></figure>")

    up = "../" if page["slug"] else ""
    tabs = []
    for p in PAGES:
        href = up + (f"{p['slug']}/" if p["slug"] else "")
        current = ' aria-current="page"' if p is page else ""
        tabs.append(f'  <a href="{href or "./"}"{current}>{html.escape(p["tab"])}</a>')
    repo = (f' Code and method: <a href="{html.escape(repo_url)}">GitHub repository</a>.' if repo_url else "")
    (page_dir / "index.html").write_text(PAGE.format(
        title=html.escape(page["title"]), home=up or "./", description=html.escape(page["lede"]), tabs="\n".join(tabs),
        kicker=html.escape(page["kicker"]), h1=html.escape(page["h1"]), lede=html.escape(page["lede"]),
        updated=dt.date.today().strftime("%B %-d, %Y"), toc="\n".join(toc), figures="\n".join(figures),
        extra=page["extra"], data="\n".join(f"    <li>{html.escape(d)}</li>" for d in page["data"]), repo=repo))
    print(f"Wrote {page_dir / 'index.html'} with {len(series)} graphics")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-url", help="link to the GitHub repository, shown in the footer")
    args = ap.parse_args()
    DOCS.mkdir(exist_ok=True)
    (DOCS / ".nojekyll").write_text("")   # serve files as-is, no Jekyll processing
    for page in PAGES:
        build_page(page, args.repo_url)


if __name__ == "__main__":
    main()
