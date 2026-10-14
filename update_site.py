"""
Rebuild the SCIL ENSO website in one command: every figure, then every page in docs/.

    python update_site.py --refresh            # monthly update: re-download NOAA data, rebuild everything
    python update_site.py                      # rebuild from cached data
    python update_site.py --pages socal-heat   # rebuild one tab's figures (all pages are still written)
    python update_site.py --site-only          # rewrite the pages only, reusing existing figures

Then publish:
    git add docs && git commit -m "Update for <month>" && git push

Tabs, figures, titles and captions are defined in site_config.py; the page layout is site/page.html
and the Methods tab text is site/methods.html. Figures are written to figures_public/<tab>/ (not
committed) and copied into docs/ (published by GitHub Pages).
"""
import argparse
import datetime as dt
import html
import re
import shutil
import subprocess
import sys
from string import Template

from PIL import Image

from enso_common import HERE
from site_config import AUTHOR, FIGURE_NOTES, GLOSSARY, PAGES, REPO_URL, SITE_URL

DOCS = HERE / "docs"
BUILD = HERE / "figures_public"
SITE = HERE / "site"


def figures_of(page):
    return [f for f in page["figures"] if f[0] not in ("section", "differences")]


def stem(i, script):
    return f"{i:02d}_{script.removesuffix('.py')}"


def is_interactive(script):
    return script.startswith("interactive")


def build_figures(page, refresh):
    """Run each figure script for one tab into figures_public/<key>/NN_name.png. Returns failed scripts."""
    out = BUILD / page["key"]
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*"):                    # start clean so retired figures don't linger
        old.unlink()
    failed = []
    for i, (script, downloads, _, _) in enumerate(figures_of(page), 1):
        ext = ".json" if is_interactive(script) else ".png"       # interactive charts: data file + site/explorer.html
        cmd = [sys.executable, str(HERE / script), "--theme", "dark", "--out", str(out / f"{stem(i, script)}{ext}")]
        if refresh and downloads:
            cmd.append("--refresh")
        print(f"\n>> [{page['key']}] {script}", flush=True)
        if subprocess.call(cmd) != 0:
            failed.append(script)
    return failed


class Glosser:
    """Escapes plain text for HTML and wraps the first use of each glossary term on a page in a
    focusable span whose definition appears on hover or tap (see the script in site/page.html)."""
    SAME = [{"anomaly", "anomalies"}, {"RONI", "Relative Oceanic Niño Index"}]

    def __init__(self):
        self.seen = set()
        terms = sorted(GLOSSARY, key=len, reverse=True)
        alt = "|".join(f"(?i:{re.escape(t)})" if t.islower() else re.escape(t) for t in terms)
        self.rx = re.compile(rf"(?<![\w-])({alt})(?![\w-])")
        self.lookup = {t.lower(): t for t in terms}

    def __call__(self, text):
        def wrap(m):
            term = self.lookup[m.group(1).lower()]
            if term in self.seen:
                return m.group(1)
            self.seen |= next((g for g in self.SAME if term in g), {term})
            d = html.escape(GLOSSARY[term])
            return (f'<span class="term" tabindex="0" data-def="{d}">{m.group(1)}'
                    f'<span class="vh"> ({d})</span></span>')
        return self.rx.sub(wrap, html.escape(text))


def summary_html(gloss):
    from summary import current_summary
    items = current_summary()
    if not items:
        return ""
    rows = "\n".join(f"    <dt>{html.escape(k)}</dt><dd>{gloss(v)}</dd>" for k, v in items)
    return (f'<section class="summary" aria-label="Summary">\n  <h2>What\'s happening now</h2>\n  <dl>\n{rows}\n  </dl>\n'
            f'  <p class="asof">Computed from the latest NOAA data when this page was built '
            f'({dt.date.today():%B %-d, %Y}).</p>\n</section>')


def differences_html(gloss):
    from summary import differences
    try:
        items = differences()
    except Exception as exc:                       # never let the text block break the build
        print(f"'Why this El Niño is different' skipped: {exc}")
        return ""
    rows = "\n".join(f"  <li><b>{html.escape(h)}</b> {gloss(t)}</li>" for h, t in items)
    return f'<ol class="diffs">\n{rows}\n</ol>' if items else ""


def write_page(page):
    src = BUILD / page["key"]
    page_dir = DOCS / page["slug"] if page["slug"] else DOCS
    img_dir = page_dir / "img"
    if img_dir.exists():
        shutil.rmtree(img_dir)
    page_dir.mkdir(parents=True, exist_ok=True)
    up = "../" if page["slug"] else ""

    gloss = Glosser()
    lede = gloss(page["lede"])
    summary = summary_html(gloss) if page.get("summary") else ""
    toc, body, n = [], [], 0
    for entry in page["figures"]:
        if entry[0] == "section":
            body.append(f'<h2 class="section">{html.escape(entry[1])}</h2>')
            continue
        if entry[0] == "differences":
            body.append(differences_html(gloss))
            continue
        script, _, short, caption = entry
        n += 1
        s = stem(n, script)
        notes = FIGURE_NOTES.get(script, {})
        takeaway = f'<p class="takeaway">{gloss(notes["takeaway"])}</p>' if notes.get("takeaway") else ""
        how = (f'<details class="how"><summary>How to read this figure</summary><p>{gloss(notes["how"])}</p>'
               f'</details>') if notes.get("how") else ""
        cap = f"<b>Figure {n}. {html.escape(short)}.</b> {gloss(caption)}"
        toc.append(f'  <li><a href="#g{n}">{html.escape(short)}</a></li>')
        if is_interactive(script):
            if not (src / f"{s}.json").exists():
                raise SystemExit(f"Missing {s}.json: run update_site.py without --site-only first.")
            img_dir.mkdir(exist_ok=True)
            shutil.copy2(src / f"{s}.json", img_dir / f"{s}.json")
            body.append((SITE / "explorer.html").read_text().replace("{{ID}}", f"g{n}")
                        .replace("{{DATA}}", f"img/{s}.json")
                        .replace("{{TAKEAWAY}}", takeaway).replace("{{CAPTION}}", cap + how))
            continue
        if not (src / f"{s}.png").exists():
            raise SystemExit(f"Missing figure {s}.png: run update_site.py without --site-only first.")
        img_dir.mkdir(exist_ok=True)
        shutil.copy2(src / f"{s}.png", img_dir / f"{s}.png")
        animated = (src / f"{s}.webp").exists()          # animations: animated WebP + PNG of the last frame
        if animated:
            shutil.copy2(src / f"{s}.webp", img_dir / f"{s}.webp")
        alt_file = src / f"{s}.alt.txt"
        alt = html.escape(alt_file.read_text().strip() if alt_file.exists() else caption)
        with Image.open(img_dir / f"{s}.png") as im:
            w, h = im.size                      # width/height reserve the space before the image loads
        if animated:
            # click to play: the still (last frame) is shown first; the animation loads only when asked for
            mb = (img_dir / f"{s}.webp").stat().st_size / 1e6
            media = (f'<div class="player"><img src="img/{s}.png" data-anim="img/{s}.webp" alt="{alt}" '
                     f'width="{w}" height="{h}" decoding="async">'
                     f'<button type="button" class="play"><span aria-hidden="true">▶</span> Play animation '
                     f'<span class="size">({mb:.0f} MB)</span></button></div>')
            links = (f' <a href="img/{s}.webp" target="_blank" rel="noopener">Open the animation in a new tab</a> · '
                     f'<a href="img/{s}.png" target="_blank" rel="noopener">still image of the final frame</a>.')
        else:
            media = (f'<a href="img/{s}.png" target="_blank" rel="noopener"><img src="img/{s}.png" alt="{alt}" '
                     f'width="{w}" height="{h}" decoding="async"></a>')
            links = ""
        body.append(f'<figure id="g{n}">{takeaway}{media}<figcaption>{cap}{links}{how}</figcaption></figure>')

    extra = page["extra"]
    if page["key"] == "methods":
        terms = "\n".join(f"  <dt>{html.escape(t)}</dt><dd>{html.escape(d)}</dd>"
                          for t, d in sorted(GLOSSARY.items(), key=lambda kv: kv[0].lower()) if t != "anomalies")
        extra = (SITE / "methods.html").read_text().format(repo=REPO_URL, site=SITE_URL, year=dt.date.today().year,
                                                           glossary=terms)
    tabs = []
    for p in PAGES:
        href = up + (f"{p['slug']}/" if p["slug"] else "")
        current = ' aria-current="page"' if p is page else ""
        tabs.append(f'  <a href="{href or "./"}"{current}>{html.escape(p["tab"])}</a>')
    data = ("  <p><b>Data</b> (all public, from NOAA):</p>\n  <ul>\n"
            + "\n".join(f"    <li>{html.escape(d)}</li>" for d in page["data"]) + "\n  </ul>") if page["data"] else ""

    page_html = Template((SITE / "page.html").read_text()).substitute(
        title=html.escape(page["title"]), description=html.escape(page["lede"]), home=up or "./", up=up,
        author=html.escape(AUTHOR), tabs="\n".join(tabs), kicker=html.escape(page["kicker"]),
        h1=html.escape(page["h1"]), lede=lede, updated=dt.date.today().strftime("%B %-d, %Y"),
        fullres=" Select a figure to view it at full resolution." if n else "",
        summary=summary, explainer=(SITE / "explainer.html").read_text() if page.get("explainer") else "",
        toc=f'<nav class="toc" aria-label="Figures on this page"><ol>\n{chr(10).join(toc)}\n</ol></nav>' if toc else "",
        figures="\n".join(body), extra=extra, data=data, repo=REPO_URL)
    (page_dir / "index.html").write_text(page_html)
    print(f"Wrote {page_dir / 'index.html'} ({n} figures)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true", help="re-download NOAA data before rebuilding")
    ap.add_argument("--pages", nargs="+", choices=[p["key"] for p in PAGES], help="only rebuild these tabs' figures")
    ap.add_argument("--site-only", action="store_true", help="skip figures; just rewrite the pages")
    args = ap.parse_args()

    failed = []
    if not args.site_only:
        for page in PAGES:
            if figures_of(page) and (not args.pages or page["key"] in args.pages):
                failed += build_figures(page, args.refresh)
    DOCS.mkdir(exist_ok=True)
    (DOCS / ".nojekyll").write_text("")              # serve files as-is (no Jekyll processing)
    for page in PAGES:
        write_page(page)
    print("\nDone." if not failed else f"\nFinished with errors in: {', '.join(failed)}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
