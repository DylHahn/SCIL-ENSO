"""
Build the GitHub Pages site (docs/) from the curated graphics.

    python run_current.py --refresh     # 1. rebuild the graphics with NOAA's latest data
    python build_site.py                # 2. copy them into docs/ and write docs/index.html
    git add docs && git commit -m "Update for <month>" && git push    # 3. publish

GitHub Pages serves docs/ from the main branch, so step 3 is all it takes to
update the live site.
"""
import argparse
import datetime as dt
import html
import shutil

from run_current import CURRENT, OUT
from run_story import HERE

DOCS = HERE / "docs"

# Short titles for the page's table of contents, by script
TITLES = {
    "story1_super_el_nino.py": "This El Niño vs. the biggest on record",
    "compare2_surface.py": "At the surface: now vs. past super El Niños",
    "compare1_underwater.py": "Underwater: now vs. past super El Niños",
    "fig6_equatorial_cross_section.py": "This year's warm water moving east",
    "stats4_event_ranking.py": "Every El Niño since 1950, ranked",
    "story4_global_heat.py": "El Niños and global heat records",
    "stats1_rain_change.py": "What past El Niños did to rainfall",
    "stats2_rain_odds.py": "How often: drier or wetter seasons",
    "stats3_temperature.py": "El Niño's temperature fingerprint",
}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The 2026 El Niño vs. the past</title>
<meta name="description" content="{description}">
<style>
  :root {{ --bg: #0d0d0e; --surface: #1c1c1b; --text: #f4f4f1; --text-2: #c3c2b7; --muted: #8a8984;
           --accent: #e8574a; --line: #2b2b2a; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--text);
          font: 17px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width: 1120px; margin: 0 auto; padding: 48px 16px 72px; }}
  header p.kicker {{ color: var(--accent); font-weight: 600; letter-spacing: .04em; text-transform: uppercase;
                     font-size: 14px; margin: 0 0 8px; }}
  h1 {{ font-size: clamp(28px, 4.5vw, 44px); line-height: 1.15; margin: 0 0 16px; }}
  .lede {{ color: var(--text-2); font-size: 19px; max-width: 760px; margin: 0 0 12px; }}
  .meta {{ color: var(--muted); font-size: 14px; margin: 0 0 40px; }}
  nav ol {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 8px 24px;
            padding: 20px 24px 20px 44px; margin: 0 0 56px; background: var(--surface); border-radius: 10px; }}
  nav a {{ color: var(--text-2); text-decoration: none; }}
  nav a:hover {{ color: var(--text); text-decoration: underline; }}
  figure {{ margin: 0 0 64px; scroll-margin-top: 24px; }}
  figure a {{ display: block; }}
  img {{ width: 100%; height: auto; display: block; border-radius: 10px; border: 1px solid var(--line); }}
  figcaption {{ margin-top: 14px; color: var(--text-2); max-width: 820px; }}
  figcaption b {{ color: var(--text); }}
  footer {{ border-top: 1px solid var(--line); padding-top: 24px; color: var(--muted); font-size: 15px; }}
  footer a {{ color: var(--text-2); }}
  footer ul {{ padding-left: 20px; }}
</style>
</head>
<body>
<main>
<header>
  <p class="kicker">El Niño 2026</p>
  <h1>How “super” is this El Niño?</h1>
  <p class="lede">{lede}</p>
  <p class="meta">Updated {updated}. Built from NOAA observations and NOAA's official forecasts. Click any graphic for full size.</p>
</header>
<nav aria-label="Graphics on this page"><ol>
{toc}
</ol></nav>
{figures}
<footer>
  <p><b>Data</b> (all public, from NOAA):</p>
  <ul>
    <li>Relative Oceanic Niño Index (RONI), outlook and strength probabilities: NOAA Climate Prediction Center</li>
    <li>NCEP GODAS ocean reanalysis: NOAA NCEP, via NOAA PSL</li>
    <li>NOAAGlobalTemp v6 and global temperature series: NOAA NCEI</li>
    <li>GPCP v2.3 precipitation: NOAA PSL</li>
  </ul>
  <p>Explore these datasets yourself on <a href="https://icharm.sdsu.edu/">iCHARM</a>.{repo}</p>
</footer>
</main>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-url", help="link to the GitHub repository, shown in the footer")
    args = ap.parse_args()

    missing = [s for i, (s, _, _) in enumerate(CURRENT, 1)
               if not (OUT / f"{i:02d}_{s.replace('.py', '.png')}").exists()]
    if missing:
        raise SystemExit(f"Run `python run_current.py` first; missing output for: {', '.join(missing)}")

    img_dir = DOCS / "img"
    if img_dir.exists():
        shutil.rmtree(img_dir)            # drop images of graphics that were retired
    img_dir.mkdir(parents=True)
    (DOCS / ".nojekyll").write_text("")   # serve files as-is, no Jekyll processing

    toc, figures = [], []
    for i, (script, _, caption) in enumerate(CURRENT, 1):
        stem = f"{i:02d}_{script.replace('.py', '')}"
        shutil.copy2(OUT / f"{stem}.png", img_dir / f"{stem}.png")
        alt_file = OUT / f"{stem}.alt.txt"
        alt = alt_file.read_text().strip() if alt_file.exists() else caption
        short = TITLES.get(script, script.replace(".py", ""))
        toc.append(f'  <li><a href="#g{i}">{html.escape(short)}</a></li>')
        figures.append(
            f'<figure id="g{i}"><a href="img/{stem}.png" target="_blank" rel="noopener">'
            f'<img src="img/{stem}.png" alt="{html.escape(alt)}" loading="{"eager" if i == 1 else "lazy"}"></a>'
            f"<figcaption><b>{i}. {html.escape(short)}.</b> {html.escape(caption)}</figcaption></figure>")

    lede = ("A strong El Niño is building in the Pacific in 2026. These graphics compare it with the biggest "
            "El Niños on record, at the surface and below it, and show what past El Niños have meant for "
            "rain and heat around the world.")
    repo = (f' Code and method: <a href="{html.escape(args.repo_url)}">GitHub repository</a>.'
            if args.repo_url else "")
    (DOCS / "index.html").write_text(PAGE.format(
        description=html.escape(lede), lede=html.escape(lede), updated=dt.date.today().strftime("%B %-d, %Y"),
        toc="\n".join(toc), figures="\n".join(figures), repo=repo))
    print(f"Wrote {DOCS / 'index.html'} with {len(CURRENT)} graphics")


if __name__ == "__main__":
    main()
