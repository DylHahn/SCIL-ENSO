"""
Export clean copies of the website's figures for slides, papers and posters: no title, subtitle,
source line or "How to read" box, cropped to the content, at 200 dpi. Animations are written as
an MP4 video and an animated WebP, with a PNG of the final frame. Interactive figures (which live
only in the browser) are skipped.

Output goes to figures_clean/<tab>/; the website (docs/) is not touched. Credit the data sources
listed on the site's Methods page when using these figures.

    python export_figures.py                          # every figure
    python export_figures.py --figures anim_sst.py    # selected figures
    python export_figures.py --theme light            # light background (for print)
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from site_config import FIGURE_VARIANTS, PAGES

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures_clean"
EXTRA = [("socal", "anim_marine_heatwaves.py")]          # figures not (yet) on a page


def figures():
    out = []
    for page in PAGES:
        for f in page["figures"]:
            if f[0] not in ("section", "differences") and not f[0].startswith("interactive"):
                out.append((page["slug"] or "el-nino", f[0]))
    return out + [e for e in EXTRA if e[1] not in {s for _, s in out}]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--figures", nargs="+", metavar="SCRIPT", help="only these figure scripts")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    args = ap.parse_args()

    env = dict(os.environ, ENSO_CLEAN="1")
    failed = []
    for tab, script in figures():
        if args.figures and script not in args.figures:
            continue
        for label, extra in FIGURE_VARIANTS.get(script, [("", [])]):
            name = Path(script).stem + (f"_{label}" if extra else "")
            out = OUT / tab / f"{name}{'_light' if args.theme == 'light' else ''}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            print(f">> {tab}/{out.name}", flush=True)
            t = time.time()
            r = subprocess.run([sys.executable, script, "--theme", args.theme, "--out", str(out), *extra], cwd=HERE,
                               env=env, capture_output=True, text=True)
            if r.returncode:
                failed.append(script)
                print(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "failed", flush=True)
            else:
                print(f"   done in {time.time() - t:.0f} s", flush=True)
    print(f"\nFigures in {OUT}" + (f"; failed: {', '.join(failed)}" if failed else ""))


if __name__ == "__main__":
    main()
