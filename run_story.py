"""
Build the "Super El Niño, explained" series for icharm.sdsu.edu in one go.

    python run_story.py                  # dark theme (matches iCHARM)
    python run_story.py --refresh        # after NOAA's monthly update (2nd Thursday)
    python run_story.py --theme light

Writes figures_public/story/: one PNG per step, a .alt.txt next to each (use it
as the image's alt text on the website) and index.html, a preview of the whole
sequence with captions that web developers can copy from.
"""
import argparse
import html
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures_public" / "story"

# (script, takes --refresh, caption shown under the image on the web page)
STORY = [
    ("story1_super_el_nino.py", True,
     "El Niño is measured by how much warmer the central Pacific is than normal. This year's event has "
     "climbed fast, and NOAA expects it to rival or beat the strongest on record."),
    ("story2_how_it_works.py", True,
     "Why it grows: winds and ocean reinforce each other in a loop, until the stored warm water runs out."),
    ("story3_global_impacts.py", False,
     "El Niño reshuffles rain around the world: droughts in some places, floods in others."),
    ("story4_global_heat.py", True,
     "The extra heat from the Pacific spreads into the atmosphere and pushes global temperatures to new records."),
    ("story5_timeline.py", True,
     "The biggest effects arrive over the next few months, which leaves time to prepare."),
    ("story6_prepare.py", False,
     "Practical steps for each kind of El Niño risk."),
]


def write_index(series, out, page_title, theme):
    """Preview page: every image in order with its alt text and caption."""
    bg, fg = ("#0d0d0e", "#f4f4f1") if theme == "dark" else ("#fcfcfb", "#0b0b0b")
    items = []
    for script, _, caption in series:
        png = script.replace(".py", ".png")
        alt_file = out / script.replace(".py", ".alt.txt")
        alt = alt_file.read_text().strip() if alt_file.exists() else ""
        items.append(f'<figure><img src="{png}" alt="{html.escape(alt)}">'
                     f"<figcaption>{html.escape(caption)}</figcaption></figure>")
    (out / "index.html").write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(page_title)}</title>
<style>
  body {{ margin: 0; background: {bg}; color: {fg}; font: 17px/1.5 system-ui, sans-serif; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 32px 16px 64px; }}
  figure {{ margin: 0 0 56px; }}
  img {{ width: 100%; height: auto; display: block; border-radius: 8px; }}
  figcaption {{ margin-top: 12px; opacity: .8; }}
</style></head>
<body><main><h1>{html.escape(page_title)}</h1>
{chr(10).join(items)}
</main></body></html>
""")
    print(f"Saved {out / 'index.html'}")


def run_series(series, out, page_title, description):
    """Command-line entry shared by run_story.py and run_stats.py."""
    ap = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--refresh", action="store_true", help="re-download NOAA data first")
    args = ap.parse_args()

    failed = []
    for script, refreshable, _ in series:
        cmd = [sys.executable, str(HERE / script), "--theme", args.theme]
        if args.refresh and refreshable:
            cmd.append("--refresh")
        print("\n>>", " ".join(cmd[1:]))
        if subprocess.call(cmd) != 0:
            failed.append(script)
    write_index(series, out, page_title, args.theme)
    print("\nDone." if not failed else f"\nFinished with errors in: {', '.join(failed)}")


if __name__ == "__main__":
    run_series(STORY, OUT, "Super El Niño, explained", __doc__)
