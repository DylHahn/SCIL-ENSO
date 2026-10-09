"""
Figure 7 — "What are the odds for the coming seasons?"

One horizontal bar per 3-month season, split into NOAA's chance of La Niña,
neutral and El Niño. Read straight from the official CPC strength-probability
table (updated the second Thursday of each month), so the numbers are always
NOAA's published ones.

    python fig7_forecast_probabilities.py
    python fig7_forecast_probabilities.py --refresh     # after NOAA's monthly update
"""
import argparse

import matplotlib.pyplot as plt

from enso_common import (FIG_DIR, COLORS, add_source, add_title, apply_style, load_cpc_strengths, save,
                         season_label)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="light")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(FIG_DIR / "fig7_forecast_probabilities.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    st = load_cpc_strengths(args.refresh)
    probs = {
        "la_nina": st[["ln_vstrong", "ln_strong", "ln_moderate", "ln_weak"]].sum(axis=1),
        "neutral": st["neutral"],
        "el_nino": st[["en_weak", "en_moderate", "en_strong", "en_vstrong"]].sum(axis=1),
    }
    labels = [season_label(t) for t in st.index]
    n = len(st)

    h = 1.0 + 0.62 * n + 1.3
    fig, ax = plt.subplots(figsize=(12, h))
    fig.subplots_adjust(top=1 - 1.25 / h, bottom=0.12, left=0.19, right=0.97)

    parts = [("la_nina", "La Niña", COLORS["la_nina"], "white"),
             ("neutral", "Neutral", COLORS["neutral"], COLORS["text"]),
             ("el_nino", "El Niño", COLORS["el_nino"], "white")]
    y = list(range(n))[::-1]
    left = [0.0] * n
    for col, label, color, txt in parts:
        vals = probs[col].values
        ax.barh(y, vals, left=left, color=color, edgecolor=COLORS["surface"], linewidth=2,
                height=0.72, label=label)
        for yi, l, v in zip(y, left, vals):
            if v >= 8:
                ax.text(l + v / 2, yi, f"{v:.0f}%", ha="center", va="center", fontsize=12,
                        fontweight="bold", color=txt)
        left = [l + v for l, v in zip(left, vals)]

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.legend(loc="lower left", ncol=3, bbox_to_anchor=(0, 1.0))

    add_title(fig, "What are the odds for the coming seasons?",
              f"NOAA's chance of La Niña, neutral or El Niño for each 3-month season "
              f"(issued {st.attrs['issued']}).")
    add_source(fig, "Source: NOAA Climate Prediction Center, official ENSO strength probabilities (RONI).")
    save(fig, args.out,
         alt="Stacked bars of NOAA's El Niño, neutral and La Niña chances by season: " + "; ".join(
             f"{lab}: El Niño {e:.0f}%, neutral {nu:.0f}%, La Niña {la:.0f}%"
             for lab, e, nu, la in zip(labels, probs["el_nino"], probs["neutral"], probs["la_nina"])) + ".")


if __name__ == "__main__":
    main()
