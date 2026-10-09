"""
Build the "What El Niño has done before" statistics graphics in one go.

    python run_stats.py                  # dark theme (matches iCHARM)
    python run_stats.py --refresh        # re-download NOAA data (gridded files are ~100 MB)
    python run_stats.py --theme light

Writes figures_public/stats/: one PNG per graphic, a .alt.txt next to each and
index.html, a captioned preview. The first run downloads GPCP rainfall and
NOAAGlobalTemp into data/gridded/.
"""
from run_story import HERE, run_series

OUT = HERE / "figures_public" / "stats"

# (script, takes --refresh, caption shown under the image on the web page)
STATS = [
    ("stats1_rain_change.py", True,
     "Measured, not sketched: average rainfall during the 8 moderate-or-stronger El Niños since 1979."),
    ("stats2_rain_odds.py", False,          # same rainfall file stats1 just refreshed
     "How reliable is the pattern? The number of past El Niños that brought a drier or wetter season."),
    ("stats3_temperature.py", True,
     "El Niño's own temperature fingerprint, with the long-term warming trend taken out."),
    ("event_ranking.py", True,
     "Every big El Niño since 1950 by peak, length and total warmth, with this year's event finished by "
     "NOAA's forecast."),
    ("stats5_how_often.py", True,
     "El Niño has no fixed schedule, but it keeps coming back every few years."),
]

if __name__ == "__main__":
    run_series(STATS, OUT, "What El Niño has done before", __doc__)
