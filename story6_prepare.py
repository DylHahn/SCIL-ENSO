"""
Story 6 — "How to prepare"

Six cards, one per El Niño hazard: where it is most likely (matching the map in
story 3) and three practical steps. Advice follows standard public guidance
(WHO, Red Cross, national weather and emergency services). Edit CARDS to
localise the wording or add phone numbers / links for your audience.

    python story6_prepare.py
    python story6_prepare.py --theme light
"""
import argparse
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from enso_common import FIG_DIR, COLORS, add_source, add_title, apply_style, save

# (title, accent (dark, light), where, three actions)
CARDS = [
    ("Extreme heat", ("#f07a3c", "#d9561f"),
     "Almost everywhere: El Niño adds heat to the whole planet",
     ["Learn the signs of heat illness: dizziness, nausea, confusion, hot dry skin.",
      "Check on older neighbours, young children and people who work outdoors.",
      "Find cool places nearby (libraries, cooling centres) before a heat wave hits."]),
    ("Drought & water shortages", ("#c98500", "#b07400"),
     "Southern Africa, Indonesia, Australia, India, Central & northern South America",
     ["Start saving water now and fix leaks before restrictions begin.",
      "Farmers: ask local agriculture services about drought-tolerant seeds and planting dates.",
      "Keep a few days of drinking water stored at home."]),
    ("Wildfire & smoke", ("#e66767", "#d64545"),
     "Indonesia, Australia, the Amazon and other dry regions",
     ["Clear dry brush and debris away from homes.",
      "Keep N95 masks on hand and set up one room with filtered air.",
      "Sign up for local emergency alerts and know your way out."]),
    ("Heavy rain & floods", ("#1fb5a0", "#128a79"),
     "Peru & Ecuador, the southern US, southeast South America, East Africa",
     ["Find out if your home is in a flood zone and plan your evacuation route.",
      "Clear gutters and drains before the rainy season.",
      "Never walk or drive through flood water: it is deeper and faster than it looks."]),
    ("Health", ("#9085e9", "#4a3aa7"),
     "Anywhere with floods or extreme heat",
     ["Empty standing water around your home: mosquitoes spread dengue and malaria.",
      "After floods, boil or treat drinking water if officials advise it.",
      "Keep a first-aid kit and a supply of your regular medicines."]),
    ("Food & household budgets", ("#c3c2b7", "#52514e"),
     "Worldwide, through markets: poor harvests in one place raise prices everywhere",
     ["Expect some food prices to rise in 2027 and budget for it.",
      "Support local food banks and community groups, which see demand rise.",
      "Farmers and businesses: use seasonal forecasts to plan the next season."]),
]


def draw_card(ax, x, y, w, h, title, accent, where, actions, unit):
    """`unit` = axes data units per inch, so text offsets follow the font sizes."""
    line = lambda pt, spacing=1.3: pt * spacing / 72 * unit       # height of one text line
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.018",
                                facecolor=COLORS["surface_2"], edgecolor="none"))
    ax.add_patch(FancyBboxPatch((x, y + h - 0.012), w, 0.012, boxstyle="round,pad=0,rounding_size=0.006",
                                facecolor=accent, edgecolor="none"))
    tx = x + 0.018
    ax.text(tx, y + h - 0.03, title, ha="left", va="top", fontsize=16, fontweight="bold", color=COLORS["text"])
    where = textwrap.fill(where, 44)
    ax.text(tx, y + h - 0.03 - line(16, 1.6), where, ha="left", va="top", fontsize=10.5,
            color=accent, linespacing=1.3, style="italic")
    yy = y + h - 0.03 - line(16, 1.6) - line(10.5) * (where.count("\n") + 1) - 0.014
    for a in actions:
        lines = textwrap.fill(a, 40)
        ax.text(tx, yy, "•", ha="left", va="top", fontsize=12, color=accent, fontweight="bold")
        ax.text(tx + 0.016, yy, lines, ha="left", va="top", fontsize=11.5, color=COLORS["text_2"],
                linespacing=1.3)
        yy -= line(11.5) * (lines.count("\n") + 1) + 0.008


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--out", default=str(FIG_DIR / "story" / "story6_prepare.png"))
    args = ap.parse_args()

    apply_style(args.theme)
    fig = plt.figure(figsize=(13, 9.4))
    rect = [0.03, 0.105, 0.94, 0.75]
    ax = fig.add_axes(rect)
    ymax = rect[3] * 9.4 / (rect[2] * 13)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, ymax)
    ax.axis("off")

    cols, gap = 3, 0.02
    w = (1 - gap * (cols - 1)) / cols
    h = (ymax - gap) / 2
    for i, (title, accents, where, actions) in enumerate(CARDS):
        r, c = divmod(i, cols)
        draw_card(ax, c * (w + gap), ymax - (r + 1) * h - r * gap, w, h, title,
                  accents[0 if args.theme == "dark" else 1], where, actions, unit=1 / (rect[2] * 13))

    fig.text(0.03, 0.055, "Your local forecast matters most: your national weather service publishes "
             "El Niño and seasonal outlooks for where you live.", fontsize=12.5, fontweight="bold",
             color=COLORS["text"], va="center")

    add_title(fig, "How to prepare",
              "We usually get months of warning before El Niño's biggest effects. "
              "Small steps taken now protect people later.")
    add_source(fig, "Guidance summarised from WHO, the Red Cross and national weather & emergency services. "
               "Regions match the typical El Niño patterns map.")
    save(fig, args.out,
         alt="Six preparation cards. " + " ".join(
             f"{t} ({where}): " + " ".join(a) for t, _, where, a in CARDS))


if __name__ == "__main__":
    main()
