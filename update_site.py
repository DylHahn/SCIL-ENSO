"""
Rebuild the SDSU Climate Informatics Lab ENSO Visualizations website in one command: every figure, then every page in docs/.

    python update_site.py --refresh            # monthly update: re-download NOAA data, rebuild everything
    python update_site.py                      # rebuild from cached data
    python update_site.py --pages socal-heat   # rebuild one tab's figures (all pages are still written)
    python update_site.py --site-only          # rewrite the pages only, reusing existing figures
    python update_site.py --figures anim_3d.py # rebuild only the listed figure scripts

Each figure is also exported clean (no title, subtitle, source line or reading notes; animations also as
MP4 video) into figures_clean/<tab>/ and published at a fixed address, docs/downloads/<script name>.png and
.mp4, with download links under the figure; other websites can link to those addresses.

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
from export_figures import OUT as CLEAN_DIR, clean_name, export_one
from site_config import (AUTHOR, DATASETS, FIGURE_DATA, FIGURE_INFO, FIGURE_NOTES, FIGURE_VARIANTS, GLOSSARY, PAGES,
                         REPO_URL, SITE_URL)

DOCS = HERE / "docs"
DOWNLOADS = DOCS / "downloads"                     # clean figures at fixed addresses (no position prefix)
DOWNLOAD_INDEX = []                                # docs/downloads/figures.json: what is there, with current text
BUILD = HERE / "figures_public"
SITE = HERE / "site"


def figures_of(page):
    return [f for f in page["figures"] if f[0] not in ("section", "differences")]


def stem(i, script):
    return f"{i:02d}_{script.removesuffix('.py')}"


# interactive figures: the script writes a JSON data file; the template draws it in the browser
INTERACTIVE_TEMPLATES = {"interactive_data.py": "explorer.html", "interactive_3d_data.py": "ocean3d.html",
                         "interactive_sealevel_data.py": "sealevel3d.html"}


def is_interactive(script):
    return script.startswith("interactive")


def variant_slug(label):
    return re.sub(r"[^a-z0-9]+", "", label.lower())


def renumber(page):
    """Rename existing outputs in figures_public/<key>/ to the current figure order (NN_ prefixes) and
    remove outputs of figures no longer on the page, so reordering needs no rebuild."""
    out = BUILD / page["key"]
    out.mkdir(parents=True, exist_ok=True)
    order = {f[0].removesuffix(".py"): i for i, f in enumerate(figures_of(page), 1)}
    moves = []
    for f in out.iterdir():
        name, _, ext = f.name[3:].partition(".")
        base = name.split("__")[0]                         # NN_name__variant.ext belongs to its figure
        if f.is_file() and f.name[:2].isdigit() and base in order:
            moves.append((f, out / f"{order[base]:02d}_{name}.{ext}"))
        elif f.is_file():
            f.unlink()
    staged = [(src.rename(src.with_name("_tmp_" + src.name)), dst) for src, dst in moves]
    for tmp, dst in staged:
        tmp.rename(dst)


def build_figures(page, refresh, only=None):
    """Run each figure script for one tab (or only the scripts in `only`) into
    figures_public/<key>/NN_name.png. Returns failed scripts."""
    out = BUILD / page["key"]
    renumber(page)
    failed = []
    for i, (script, downloads, _, _) in enumerate(figures_of(page), 1):
        if only and script not in only:
            continue
        for old in out.glob(f"{stem(i, script)}.*"):
            old.unlink()
        ext = ".json" if is_interactive(script) else ".png"       # interactive charts: data file + template
        for v, (label, extra_args) in enumerate(FIGURE_VARIANTS.get(script, [("", [])])):
            name = stem(i, script) + (f"__{variant_slug(label)}" if v else "")
            cmd = [sys.executable, str(HERE / script), "--theme", "dark", "--out", str(out / f"{name}{ext}"), *extra_args]
            if refresh and downloads and v == 0:
                cmd.append("--refresh")
            print(f"\n>> [{page['key']}] {script} {label}".rstrip(), flush=True)
            if subprocess.call(cmd) != 0:
                failed.append(script)
            elif not is_interactive(script) and not export_one(page["slug"] or "el-nino", script, label, extra_args):
                failed.append(script)                              # clean copy for the download links
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


SEARCH = []                                                  # every figure and glossary term, for the search box


def slugify(text):
    import unicodedata
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def write_search_index():
    import json
    (DOCS / "search-index.json").write_text(json.dumps(SEARCH, ensure_ascii=False, separators=(",", ":")))
    print(f"Wrote {DOCS / 'search-index.json'} ({len(SEARCH)} entries)")


# pages that were renamed: the old address forwards to the new tab
REDIRECTS = {"compare": "surface/"}


def write_redirects():
    for old, new in REDIRECTS.items():
        d = DOCS / old
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        (d / "index.html").write_text(
            f'<!doctype html><meta charset="utf-8"><title>Moved</title>'
            f'<meta http-equiv="refresh" content="0; url=../{new}"><link rel="canonical" href="../{new}">'
            f'<p>This page has moved to <a href="../{new}">../{new}</a>.</p>')


def toc_html(groups):
    groups = [(h, items) for h, items in groups if items]
    if not groups:
        return ""
    parts = [(f'<div class="toc-group"><p>{html.escape(h)}</p>' if h else '<div class="toc-group">')
             + f'<ol>{"".join(items)}</ol></div>' for h, items in groups]
    return f'<nav class="toc" aria-label="Figures on this page">\n' + "\n".join(parts) + "\n</nav>"


def downloads_html(page, script, s, animated, up):
    """Copy the figure's clean exports to docs/downloads/ and return the download links: the figure as shown,
    the clean figure (no title or notes) and, for animations, the MP4 video, for each version (cm | inches)."""
    tab = page["slug"] or "el-nino"
    versions = FIGURE_VARIANTS.get(script, [("", [])])
    parts = [f'<a href="img/{s}.png" download>Figure as shown (PNG)</a>']
    files = {}
    for label, extra in versions:
        name = clean_name(script, label, extra)
        tag = f", {label}" if len(versions) > 1 else ""
        for ext, what in ((".png", "Clean figure, no title (PNG{})"), (".mp4", "Video (MP4{})")):
            f = CLEAN_DIR / tab / f"{name}{ext}"
            if f.exists() and (ext == ".png" or animated):
                DOWNLOADS.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, DOWNLOADS / f.name)
                mb = f.stat().st_size / 1e6
                size = f" · {mb:.0f} MB" if mb >= 1 else ""
                parts.append(f'<a href="{up}downloads/{f.name}" download>{what.format(tag)}{size}</a>')
                files[f"{label or 'default'}{ext}"] = SITE_URL + "downloads/" + f.name
    entry = next(e for e in page["figures"] if e[0] == script)
    alt = BUILD / page["key"] / f"{s}.alt.txt"
    DOWNLOAD_INDEX.append(dict(
        script=script, title=entry[2], tab=page["tab"], page=SITE_URL + (f"{page['slug']}/" if page["slug"] else ""),
        caption=entry[3], takeaway=FIGURE_NOTES.get(script, {}).get("takeaway", ""),
        how_to_read=FIGURE_NOTES.get(script, {}).get("how", ""), relation=FIGURE_INFO[script][0],
        data=FIGURE_INFO[script][1], description=alt.read_text().strip() if alt.exists() else "",
        animated=animated, files=files))
    return '<p class="figlinks downloads"><b>Download:</b> ' + " · ".join(parts) + "</p>"


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
    toc, body, n = [[None, []]], [], 0           # table of contents: [section heading, entries] groups
    for entry in page["figures"]:
        if entry[0] == "section":                  # ("section", heading[, short introduction])
            toc.append([entry[1], []])
            body.append(f'<h2 class="section">{html.escape(entry[1])}</h2>'
                        + (f'<p class="intro">{gloss(entry[2])}</p>' if len(entry) > 2 else ""))
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
        why, data_used = FIGURE_INFO[script]
        cap = (f'<b class="figtitle">Figure {n}. {html.escape(short)}</b>'
               f'<dl class="figinfo"><dt>What it shows</dt><dd>{gloss(caption)}</dd>'
               f'<dt>How it relates to El Niño</dt><dd>{gloss(why)}</dd>'
               f'<dt>Data</dt><dd>{html.escape(data_used)}</dd>'
               f'<dt>Get the data</dt><dd>' + " · ".join(
                   f'<a href="{html.escape(DATASETS[k][1])}" target="_blank" rel="noopener">{html.escape(DATASETS[k][0])}</a>'
                   for k in FIGURE_DATA[script]) + '</dd></dl>')
        toc[-1][1].append(f'<li value="{n}"><a href="#g{n}">{html.escape(short)}</a></li>')
        SEARCH.append(dict(t=f"Figure {n}. {short}", p=page["tab"], g=page.get("group") or "",
                           s=notes.get("takeaway") or caption,                # shown under the result
                           u=(f"{page['slug']}/" if page["slug"] else "") + f"#g{n}",
                           k=" ".join([notes.get("takeaway", ""), page["tab"], toc[-1][0] or ""]),
                           x=" ".join([caption, notes.get("how", ""), *FIGURE_INFO[script],
                                       *(DATASETS[d][0] for d in FIGURE_DATA[script])])))
        if is_interactive(script):
            if not (src / f"{s}.json").exists():
                raise SystemExit(f"Missing {s}.json: run update_site.py without --site-only first.")
            img_dir.mkdir(exist_ok=True)
            shutil.copy2(src / f"{s}.json", img_dir / f"{s}.json")
            body.append((SITE / INTERACTIVE_TEMPLATES[script]).read_text().replace("{{ID}}", f"g{n}")
                        .replace("{{DATA}}", f"img/{s}.json?v={dt.date.today():%Y%m%d}")
                        .replace("{{TAKEAWAY}}", takeaway).replace("{{CAPTION}}", cap + how))
            continue
        if not (src / f"{s}.png").exists():
            raise SystemExit(f"Missing figure {s}.png: run update_site.py without --site-only first.")
        img_dir.mkdir(exist_ok=True)
        shutil.copy2(src / f"{s}.png", img_dir / f"{s}.png")
        animated = (src / f"{s}.webp").exists()          # animations: animated WebP + PNG of the last frame
        if animated:
            shutil.copy2(src / f"{s}.webp", img_dir / f"{s}.webp")
        switch = ""
        if script in FIGURE_VARIANTS:                    # e.g. cm | inches: a button per version
            buttons = []
            for v, (label, _) in enumerate(FIGURE_VARIANTS[script]):
                vs = s + (f"__{variant_slug(label)}" if v else "")
                for e in (".png", ".webp"):
                    if (src / f"{vs}{e}").exists():
                        shutil.copy2(src / f"{vs}{e}", img_dir / f"{vs}{e}")
                buttons.append(f'<button type="button" data-png="img/{vs}.png" data-anim="img/{vs}.webp" '
                               f'aria-pressed="{str(v == 0).lower()}">{html.escape(label)}</button>')
            switch = (f'<div class="variant-switch" role="group" aria-label="Units"><span>Units:</span>'
                      + "".join(buttons) + "</div>")
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
            links = (f'<p class="figlinks"><a href="img/{s}.webp" target="_blank" rel="noopener">Open the animation in a '
                     f'new tab</a> · <a href="img/{s}.png" target="_blank" rel="noopener">still image of the final '
                     f'frame</a></p>')
        else:
            media = (f'<a href="img/{s}.png" target="_blank" rel="noopener"><img src="img/{s}.png" alt="{alt}" '
                     f'width="{w}" height="{h}" decoding="async"></a>')
            links = ""
        links += downloads_html(page, script, s, animated, up)
        body.append(f'<figure id="g{n}">{takeaway}{switch}{media}<figcaption>{cap}{links}{how}</figcaption></figure>')

    extra = page["extra"]
    if page["key"] == "methods":
        for t, d in GLOSSARY.items():
            if t != "anomalies":
                SEARCH.append(dict(t=t, p="Glossary", g="Methods & Data", u=f"methods/#term-{slugify(t)}", k=t, x=d, s=d))
        terms = "\n".join(f'  <dt id="term-{slugify(t)}">{html.escape(t)}</dt><dd>{html.escape(d)}</dd>'
                          for t, d in sorted(GLOSSARY.items(), key=lambda kv: kv[0].lower()) if t != "anomalies")
        extra = (SITE / "methods.html").read_text().format(repo=REPO_URL, site=SITE_URL, year=dt.date.today().year,
                                                           glossary=terms)
    tabs, groups = [], []
    for p in PAGES:                                         # tabs grouped under their topic
        if not groups or groups[-1][0] != p.get("group"):
            groups.append((p.get("group"), []))
        href = up + (f"{p['slug']}/" if p["slug"] else "")
        current = ' aria-current="page"' if p is page else ""
        groups[-1][1].append(f'<a href="{href or "./"}"{current}>{html.escape(p["tab"])}</a>')
    for g, links in groups:
        label = f'<span class="tablabel">{html.escape(g)}</span>' if g else ""
        tabs.append(f'  <div class="tabgroup">{label}{"".join(links)}</div>')
    data = ("  <p><b>Data</b> (all public, from NOAA):</p>\n  <ul>\n"
            + "\n".join(f"    <li>{html.escape(d)}</li>" for d in page["data"]) + "\n  </ul>") if page["data"] else ""

    page_html = Template((SITE / "page.html").read_text()).substitute(
        title=html.escape(page["title"]), description=html.escape(page["lede"]), home=up or "./", up=up,
        author=html.escape(AUTHOR), tabs="\n".join(tabs), today=f"{dt.date.today():%Y%m%d}", kicker=html.escape(page["kicker"]),
        h1=html.escape(page["h1"]), lede=lede, updated=dt.date.today().strftime("%B %-d, %Y"),
        fullres=" Select a figure to view it at full resolution." if n else "",
        summary=summary, explainer=(SITE / "explainer.html").read_text() if page.get("explainer") else "",
        toc=toc_html(toc),
        figures="\n".join(body), extra=extra, data=data, repo=REPO_URL)
    (page_dir / "index.html").write_text(page_html)
    print(f"Wrote {page_dir / 'index.html'} ({n} figures)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true", help="re-download NOAA data before rebuilding")
    ap.add_argument("--pages", nargs="+", choices=[p["key"] for p in PAGES], help="only rebuild these tabs' figures")
    ap.add_argument("--site-only", action="store_true", help="skip figures; just rewrite the pages")
    ap.add_argument("--figures", nargs="+", metavar="SCRIPT", help="only rebuild these figure scripts")
    args = ap.parse_args()

    failed = []
    for page in PAGES:
        if not figures_of(page):
            continue
        if args.site_only or (args.pages and page["key"] not in args.pages):
            renumber(page)                         # keep outputs in step with any reordering
        else:
            failed += build_figures(page, args.refresh, args.figures)
    DOCS.mkdir(exist_ok=True)
    (DOCS / ".nojekyll").write_text("")
    if DOWNLOADS.exists():                             # refilled from figures_clean/ as the pages are written
        shutil.rmtree(DOWNLOADS)              # serve files as-is (no Jekyll processing)
    for page in PAGES:
        write_page(page)
    write_search_index()
    if DOWNLOAD_INDEX:
        import json
        (DOWNLOADS / "figures.json").write_text(json.dumps(
            dict(updated=f"{dt.date.today():%Y-%m-%d}", site=SITE_URL, author=AUTHOR,
                 note="Clean figures (no title or notes) at fixed addresses, refreshed at every site update. "
                      "Text fields describe the current data.", figures=DOWNLOAD_INDEX),
            ensure_ascii=False, indent=1))
    write_redirects()
    print("\nDone." if not failed else f"\nFinished with errors in: {', '.join(failed)}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
