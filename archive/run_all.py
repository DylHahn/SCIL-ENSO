"""
Make every public ENSO graphic in one go.

    python run_all.py --data-dir data        # real data (NOAA downloads + your GODAS files)

Figures go to figures_public/. A failure in one figure doesn't stop the others.
"""
import argparse
import subprocess
import sys
from pathlib import Path

from enso_common import GODAS_DIR

HERE = Path(__file__).resolve().parent

SCRIPTS = [
    ("fig1_nino_regions_map.py", ["--all-regions"]),
    ("fig2_roni_timeline.py", []),
    ("fig3_oni_vs_roni.py", []),
    ("fig4_wwv_vs_nino34.py", ["DATA"]),
    ("fig5_walker_circulation.py", []),
    ("fig6_equatorial_cross_section.py", ["DATA"]),
    ("fig7_forecast_probabilities.py", []),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(GODAS_DIR))
    args = ap.parse_args()

    failed = []
    for script, extra in SCRIPTS:
        cmd = [sys.executable, str(HERE / script)]
        for e in extra:
            cmd += ["--data-dir", args.data_dir] if e == "DATA" else [e]
        print("\n>>", " ".join(cmd[1:]))
        if subprocess.call(cmd) != 0:
            failed.append(script)

    print("\nDone." if not failed else f"\nFinished with errors in: {', '.join(failed)}")


if __name__ == "__main__":
    main()
