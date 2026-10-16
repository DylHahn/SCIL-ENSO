"""
What the website contains: its tabs, the figures on each tab (in order), their short titles and
captions, and the page text. `update_site.py` reads this file; edit here to add, remove or reorder
figures.

Each page's `figures` list holds a section heading, ("section", "Heading"[, "short introduction"]),
the computed "Why this El Niño stands out" list, ("differences",), or a figure,
(script, uses_downloads, short title, caption), where `uses_downloads` means the script accepts
--refresh to re-download its NOAA data.
"""

REPO_URL = "https://github.com/DylHahn/SCIL-ENSO"
SITE_URL = "https://dylhahn.github.io/SCIL-ENSO/"
AUTHOR = "Dylan Hahn"

PAGES = [
    dict(
        key="el-nino", slug="", tab="El Niño 2026",
        title="The 2026–27 El Niño in historical context", kicker="El Niño 2026–27",
        h1="The 2026–27 El Niño in historical context",
        lede="A strong El Niño is developing in the equatorial Pacific. This page summarises how it compares with "
             "the strongest events since 1950; the next two tabs look below the surface and at further "
             "comparisons. All figures use NOAA observations, reanalysis and official forecasts.",
        summary=True, explainer=True,
        figures=[
            ("section", 'Why this El Niño stands out',
             "The key findings, recomputed from the latest NOAA data at every update."),
            ("differences",),
            ("section", 'At the surface',
             "El Niño begins with warm water spreading east along the equator."),
            ('anim_sst.py', True, 'Animation: sea surface temperature, 2026 and past very strong events',
             "Animated month-by-month sea surface temperature across the tropical Pacific (NOAA OISST, 0.25°), "
             "January to the latest month, for 2026, 2015, 1997, 1982 and the 1991–2020 normal, with the Niño "
             "3.4 average for each."),
            ("section", 'Compared with every El Niño since 1950',
             "How this event has developed compared with all 22 El Niño events since 1950, measured at the "
             "same point in the year."),
            ('anim_timeseries.py', True, 'Animation: development compared with every El Niño since 1950',
             "Monthly Niño 3.4, Niño 1+2 and upper-ocean anomalies for every El Niño since 1950, aligned by "
             "onset year and drawn month by month; the box in each panel ranks the current event against all "
             "past events at the same stage."),
            ('interactive_data.py', True, 'Interactive: explore every El Niño since 1950',
             "Choose a measure, then move across the chart to compare all events month by month; the bars rank "
             "every event at the selected month. Select any gray line, or use the menu, to highlight another "
             "event."),
            ('event_ranking.py', True, 'Ranking of El Niño events since 1950',
             "El Niño events since 1950 ranked by peak strength, duration and accumulated intensity, with the "
             "current event completed by NOAA's median forecast."),
            ("section", 'What comes next',
             "NOAA's official forecast for the coming months and El Niño's influence on global temperature."),
            ('roni_vs_past_events.py', True, 'Event development vs. past very strong events',
             "Development of the 2026–27 event in NOAA's Relative Oceanic Niño Index alongside the four "
             "strongest El Niño events since 1950, with NOAA's official forecast."),
            ('global_temperature.py', True, 'Global temperature and El Niño',
             "Annual global mean surface temperature anomalies; recent record years have coincided with El Niño "
             "events."),
        ],
        extra="""<section class="note next">
  <h2>More on this El Niño</h2>
  <p><a href="ocean/">Below the surface</a>: the warm water stored in the upper ocean, in 3D, by temperature layer and
  as Kelvin waves. <a href="compare/">Detailed comparisons</a>: surface maps of each very strong El Niño, the Niño
  regions, and how NOAA's forecasts have performed.</p>
  <h2>What this means for Southern California</h2>
  <p>El Niño's effects reach California mainly through winter storms and coastal ocean temperatures. See
  <a href="socal/">Southern California Heat</a> for this year's summer and marine heat, and
  <a href="socal-precip/">Southern California Precipitation</a> for NOAA's winter outlook and what past strong El
  Niño winters brought.</p>
</section>""",
        data=["Relative Oceanic Niño Index (RONI), outlook and strength probabilities: NOAA Climate Prediction Center",
              "NCEP GODAS ocean reanalysis: NOAA NCEP, via NOAA PSL",
              "OISST v2.1 and ERSST v5 sea surface temperature: NOAA NCEI, via NOAA PSL",
              "NOAAGlobalTemp v6 and global temperature series: NOAA NCEI",
              "Daily satellite sea level (blended altimetry): NOAA NESDIS, via NOAA CoastWatch ERDDAP",
              "Monthly Niño region indices (OISST v2.1): NOAA Climate Prediction Center"],
    ),
    dict(
        key="ocean", slug="ocean", tab="Below the surface",
        title="The 2026–27 El Niño below the surface", kicker="El Niño 2026–27 · Below the surface",
        h1="Below the surface: the warm water behind the 2026–27 El Niño",
        lede="Most of an El Niño's heat is stored below the sea surface. These figures follow the warm water in the "
             "upper few hundred metres of the equatorial Pacific: in 3D, by temperature layer and as Kelvin waves, "
             "using NOAA's ocean reanalysis and daily satellite sea level.",
        figures=[
            ("section", 'The warm layer in 3D',
             "Rotatable and animated 3D views of the upper ocean, built from NOAA's ocean reanalysis."),
            ('anim_3d.py', False, 'Animation: the tropical Pacific in 3D',
             "Rotating 3D view of the tropical Pacific in a normal year and in 2026: the top surface is the "
             "temperature at 5 m and the lower surface the base of the warm layer (the 20 °C isotherm), from "
             "July of the year before onset to the latest month."),
            ('interactive_3d_data.py', False, 'Interactive 3D: warm layer, temperature layers and hottest water',
             "Rotate and zoom a 3D model of the tropical Pacific for 2026, 2015, 1997, 1982 or the 1991–2020 "
             "normal, month by month. Warm layer: the sea surface above the base of the warm layer (20 °C). "
             "Temperature layers: the depths of the 20, 24, 26 and 28 °C isotherms. Hottest water: the volume of "
             "water above 28 and 29 °C."),
            ("section", 'Warm water building up',
             "How much warm water is stored in the equatorial Pacific, and how much of it is the hottest "
             "water, above 28 °C."),
            ('anim_warm_water.py', False, 'Animation: warm water moving across the Pacific',
             "Animated maps of the depth of the 20 °C isotherm (the thickness of the warm upper layer) from July "
             "of the year before onset, for 2026, 2015, 1997, 1982 and the 1991–2020 normal, with the equatorial "
             "warm water volume (5°S–5°N) and its departure from normal."),
            ('anim_warm_layers.py', False, 'Animation: layers of warm water',
             "Equatorial sections coloured by temperature layer (20–24, 24–26, 26–28, 28–29 and above 29 °C) for "
             "2026, 2015, 1997, 1982 and the 1991–2020 normal, with the volume of water in each layer between "
             "5°S and 5°N, from July of the year before onset to the latest month."),
            ("section", 'Kelvin waves',
             "Pulses of warm water that cross the Pacific beneath the surface, followed in daily satellite sea "
             "level."),
            ('anim_kelvin.py', True, 'Animation: Kelvin waves',
             "Every Kelvin wave since July 2025 traced in daily satellite sea level along the equator: each "
             "pulse raises sea level by a few centimetres as it crosses the Pacific."),
            ('anim_sealevel_3d.py', True, 'Animation: sea level in 3D',
             "Daily satellite sea level across the tropical Pacific drawn as a 3D landscape, July 2025 to the "
             "latest day: Kelvin waves travel east along the equator as the eastern Pacific rises."),
            ("section", 'Along the equator',
             "Vertical slices through the ocean along the equator, from Asia to South America."),
            ('anim_upper_ocean.py', False, 'Animation: upper-ocean temperature, 2026 and past very strong events',
             "Animated equatorial upper-ocean temperature sections for 2026, 2015, 1997, 1982 and the 1991–2020 "
             "normal; during El Niño the warm layer deepens in the east and the 20 °C line flattens."),
            ('subsurface_comparison.py', True, 'Upper-ocean temperature by event',
             "Equatorial upper-ocean temperature at the same stage of each event; the current event holds "
             "substantially more subsurface heat."),
            ('hovmoller_upper_ocean.py', False, 'Upper-ocean heat content (Hovmöller)',
             "The same layout for the average temperature of the upper 200 m; warm water spreading east beneath "
             "the surface marks Kelvin waves."),
        ],
        extra="",
        data=["NCEP GODAS ocean reanalysis: NOAA NCEP, via NOAA PSL",
              "Daily satellite sea level (blended altimetry): NOAA NESDIS, via NOAA CoastWatch ERDDAP",
              "Relative Oceanic Niño Index (RONI): NOAA Climate Prediction Center"],
    ),
    dict(
        key="compare", slug="compare", tab="Detailed comparisons",
        title="The 2026–27 El Niño: detailed comparisons", kicker="El Niño 2026–27 · Detailed comparisons",
        h1="Detailed comparisons with past very strong El Niños",
        lede="Further comparisons of the 2026–27 El Niño with the very strong events of 2015, 1997 and 1982, and a "
             "record of how NOAA's forecasts for this event have performed.",
        figures=[
            ("section", 'At the same point in the year',
             "The surface of the tropical Pacific in 2026 and in the very strong El Niños of 2015, 1997 and "
             "1982."),
            ('surface_comparison.py', True, 'Sea surface temperature by event',
             "Tropical Pacific sea surface temperature in the same month of each very strong El Niño year, with "
             "Niño 3.4 and tropical-mean anomalies."),
            ('nino_regions.py', True, 'Warming across the Niño regions',
             "Location of the four Niño regions and their monthly anomalies, showing where along the equator the "
             "warming is concentrated."),
            ('hovmoller_sst.py', True, 'Equatorial SST evolution (Hovmöller)',
             "Sea surface temperature along the equator, month by month (rows, top to bottom) and from the "
             "western Pacific to South America (left to right), for four very strong events."),
            ("section", 'How well were the forecasts doing?'),
            ('forecast_verification.py', True, "Verification of NOAA's 2026 forecasts",
             "Each monthly NOAA strength forecast issued since April 2026 compared with the observed RONI, and "
             "how confidence in a very strong peak has evolved."),
        ],
        extra="",
        data=["OISST v2.1 and ERSST v5 sea surface temperature: NOAA NCEI, via NOAA PSL",
              "Monthly Niño region indices (OISST v2.1): NOAA Climate Prediction Center",
              "Relative Oceanic Niño Index (RONI), outlook and strength probabilities: NOAA Climate Prediction Center"],
    ),
    dict(
        key="socal-heat", slug="socal", tab="Southern California Heat",
        title="Southern California Heat", kicker="Southern California Heat",
        h1="Southern California heat",
        lede="How the summer of 2026 compared with past summers across Southern California, on land and in "
             "coastal waters, and how summer heat in the region has increased since 1895.",
        figures=[
            ('socal_summer_anomalies.py', True, 'Summer 2026 temperature anomalies',
             "June–September 2026 daytime-high and overnight-low anomalies across Southern California (NOAA "
             "nClimGrid, ~5 km), and the regional overnight-low anomaly for every summer since 1950."),
            ('socal_station_heat.py', True, 'Warm nights and hot days by station',
             "Station counts of warm nights (≥ 65 °F) and hot days (≥ 90 °F) each summer since 1950 at Los "
             "Angeles, San Diego, the Inland Empire and Santa Barbara."),
            ('socal_marine_heat.py', True, 'Marine heat in the Southern California Bight',
             "Daily sea surface temperature and marine heatwave days in the Southern California Bight since 1982 "
             "(NOAA OISST), with 2026 compared with 1997 and 2015."),
            ('socal_warming_since_1895.py', True, 'Long-term increase in summer heat',
             "Change in summer daytime highs and overnight lows since 1951–1980 across Southern California, and "
             "the regional summer temperature record since 1895 (NOAA nClimGrid)."),
        ],
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
  </ul>
</section>""",
        data=["Gridded monthly temperature (nClimGrid) and daily station records (GHCN-Daily): NOAA NCEI",
              "Daily sea surface temperature (OISST v2.1): NOAA NCEI, via NOAA CoastWatch ERDDAP",
              "Relative Oceanic Niño Index (RONI): NOAA Climate Prediction Center"],
    ),
    dict(
        key="socal-precip", slug="socal-precip", tab="Southern California Precipitation",
        title="Southern California Precipitation", kicker="Southern California Precipitation",
        h1="Southern California precipitation and El Niño",
        lede="NOAA's seasonal precipitation outlook for the coming winter, and the precipitation Southern "
             "California received during past strong El Niño winters, region-wide and at individual stations.",
        figures=[
            ("socal_precip_outlook.py", True, "NOAA seasonal precipitation outlook",
             "NOAA Climate Prediction Center probability of above-, near- or below-normal precipitation for "
             "Southern California, with season-by-season values for Los Angeles."),
            ("socal_precip_el_nino_winters.py", True, "Precipitation in strong El Niño winters",
             "November–March precipitation across Southern California during the strong El Niño winters since "
             "1951 (NOAA nClimGrid, ~5 km), and the regional total for every winter."),
            ("socal_station_precip.py", True, "Station precipitation by ENSO phase",
             "Water-year precipitation by ENSO phase at Los Angeles, San Diego, Lake Elsinore and Santa Barbara, "
             "1951 to present."),
        ],
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
    dict(
        key="methods", slug="methods", tab="Methods & data",
        title="Methods and data", kicker="Methods & data",
        h1="Methods and data",
        lede="Data sources, definitions and methods behind every figure on this site, with known limitations.",
        figures=[],
        extra="",            # filled from methods.html by update_site.py
        data=[],
    ),
]


# ---------------------------------------------------------------------------------------------
# Per-figure reading aids, keyed by script. `takeaway` is shown in bold above the caption and
# `how` in a collapsible "How to read this figure" note. Takeaways describe the current data:
# re-read them at each monthly update.
# ---------------------------------------------------------------------------------------------
FIGURE_NOTES = {
    "anim_timeseries.py": dict(
        takeaway="At the latest month, 2026 is warmer than every El Niño since 1950 at the same stage, both at the "
                 "surface and in the upper ocean.",
        how="Each line is one El Niño. The horizontal axis runs from January of the year the event began to June of "
            "the following year; the vertical axis shows how much warmer than normal the water was. A line above the "
            "others at a given month means that event was further developed at that point in the year."),
    "interactive_data.py": dict(
        takeaway="Pick a measure and a month to see where 2026 ranks among every El Niño since 1950."),
    "anim_sst.py": dict(
        takeaway="Water warmer than 28 °C, normally confined to the western Pacific, now reaches farther east along "
                 "the equator than in 2015, 1997 or 1982 at the same point in the year.",
        how="Each map shows the actual sea surface temperature for one month. Red and dark red are warmer than about "
            "28 °C (inside the black line), warm enough to fuel heavy tropical rainfall. Compare each year with the "
            "Normal panel at the bottom: during El Niño the warm area spreads east toward South America."),
    "anim_warm_layers.py": dict(
        takeaway="The hottest water has grown the most: the volume warmer than 28 °C is far above normal and above "
                 "2015, 1997 and 1982 at the same stage.",
        how="Each slice runs along the equator from Asia (left) to South America (right) and from 5 m down to 200 m. "
            "Colours mark temperature layers, from below 20 °C (dark blue) to above 29 °C (dark red). The dashed "
            "lines show where 20 °C and 28 °C normally lie; red reaching below or east of them means more warm water "
            "than usual. The bar beside each slice adds up the volume in each layer, warmest on the left."),
    "anim_kelvin.py": dict(
        takeaway="A series of Kelvin waves has carried warm water from the western Pacific to South America since "
                 "late 2025, each one adding to the warm layer in the east.",
        how="Top: total sea level along the equator on the day shown, rising in the east as warm water piles up. "
            "Bottom: the Kelvin-wave signal day by day, with time running down the page, so each "
            "wave is a red streak slanting down to the right. Yellow dashed lines trace each wave once it has "
            "crossed the Pacific."),
    "anim_sealevel_3d.py": dict(
        takeaway="Sea level along the equator in the eastern Pacific has risen by about 40 cm since mid-2025 as warm "
                 "water piled up, with Kelvin-wave ridges arriving one after another.",
        how="The landscape is the tropical Pacific seen from the south, with Asia to the left and South America to "
            "the right; its height and colour are the sea level anomaly. Watch the red ridge along the equator: "
            "bumps that move from left to right are Kelvin waves, and the ridge grows as warm water accumulates in "
            "the east."),
    "anim_upper_ocean.py": dict(
        takeaway="In 2026 the 20 °C line is nearly flat across the Pacific: the cold water that normally lies close "
                 "to the surface in the east has been pushed down.",
        how="Each panel is a vertical slice through the ocean along the equator, from Asia (left) to South America "
            "(right) and from the surface (top) to 200 m depth (bottom). Warm colours above the black line are the "
            "warm upper layer. Normally the line rises toward the east; during El Niño it flattens."),
    "anim_3d.py": dict(
        takeaway="In a normal year the warm layer is thin near South America; in 2026 it has thickened there, so "
                 "the cold water that normally cools the eastern Pacific stays far below the surface.",
        how="Each block is the tropical Pacific seen from the south-east, with Asia at the far left and South "
            "America at the right. The coloured lower surface is the base of the warm layer: red where it lies deep, "
            "blue where it is close to the surface. The thin top sheet is the sea surface temperature."),
    "interactive_3d_data.py": dict(
        takeaway="Switch to Hottest water and compare 2026 with Normal: the body of water above 28 °C is far larger "
                 "in 2026 and reaches much farther east.",
        how="Load the view, then drag to rotate and use + and − to zoom; the angle you choose is kept while the "
            "months play. Choose a view and a year above the model, and use the slider or play button to move "
            "through the months. The opacity sliders below fade or hide each layer, so you can look inside."),
    "anim_warm_water.py": dict(
        takeaway="More warm water is stored along the equator in 2026 than at the same stage of 2015, 1997 or 1982.",
        how="Each map shows how far below the surface the warm upper layer reaches (the depth of the 20 °C "
            "isotherm). Dark red means warm water extends deep; blue means the warm layer is thin. Watch the band "
            "between the dashed lines: during El Niño the red area spreads east along the equator."),
    "roni_vs_past_events.py": dict(
        takeaway="NOAA's official outlook places the peak of this event above the strongest El Niño since 1950."),
    "forecast_verification.py": dict(
        takeaway="NOAA's confidence in a very strong peak has risen with every forecast issued since April 2026."),
    "surface_comparison.py": dict(
        takeaway="In the same month, 2026 is warmer than past very strong events both in the Niño 3.4 region and "
                 "across the tropical Pacific as a whole."),
    "subsurface_comparison.py": dict(
        takeaway="The upper ocean holds far more extra heat in 2026 than in any past very strong event at the same "
                 "stage.",
        how="Each panel is a vertical slice along the equator, from Asia (left) to South America (right), down to "
            "200 m. Colours show how much warmer (red) or cooler (blue) than normal the water is."),
    "hovmoller_sst.py": dict(
        takeaway="Surface warming in the eastern Pacific is stronger in 2026 than at the same time in any past very "
                 "strong event.",
        how="Time runs down the page, one row per month; position runs left to right from the western Pacific to "
            "South America. Red marks warmer-than-normal water. Warmth that slants down and to the right is moving "
            "east over time."),
    "hovmoller_upper_ocean.py": dict(
        takeaway="Warm water spreading east beneath the surface has built a larger heat reservoir in 2026 than in "
                 "past very strong events.",
        how="Time runs down the page, one row per month; position runs left to right from the western Pacific to "
            "South America. Colours show the average temperature anomaly of the top 200 m. Diagonal streaks "
            "running down and to the right are Kelvin waves: pulses of warm water that cross the Pacific beneath "
            "the surface in about two months."),
    "nino_regions.py": dict(
        takeaway="Warming is strongest near South America and weakest in the western Pacific, a pattern closest to "
                 "1997–98.",
        how="The map shows the four standard boxes along the equator, from Niño 4 in the west to Niño 1+2 off South "
            "America. Each chart plots how much warmer than normal one box has been, month by month."),
    "event_ranking.py": dict(
        takeaway="If NOAA's median forecast is realised, 2026–27 would rank first by peak strength among El Niño "
                 "events since 1950."),
    "global_temperature.py": dict(
        takeaway="Many of the record-warm years since 1950 coincided with El Niño, which temporarily adds to the "
                 "long-term warming."),
    "socal_warming_since_1895.py": dict(
        takeaway="Summer nights across Southern California have warmed more than summer days since the mid-20th "
                 "century."),
    "socal_marine_heat.py": dict(
        takeaway="Coastal waters off Southern California have had more marine heatwave days in 2026 than in any "
                 "previous year by the same date.",
        how="A marine heatwave day is part of a spell of at least five days when the water is warmer than 90% of "
            "past values for that time of year. Each year is compared through the same calendar date."),
    "socal_summer_anomalies.py": dict(
        takeaway="Summer 2026 nights were among the warmest on record across the region; daytime highs were less "
                 "exceptional."),
    "socal_station_heat.py": dict(
        takeaway="Warm nights were far more frequent than usual in summer 2026 at every station, and Santa Barbara "
                 "set a record."),
    "socal_precip_outlook.py": dict(
        takeaway="NOAA's outlook favours a wetter-than-normal winter in Southern California, most strongly from "
                 "December onward."),
    "socal_precip_el_nino_winters.py": dict(
        takeaway="Most strong El Niño winters, though not all, have been wetter than normal across Southern "
                 "California."),
    "socal_station_precip.py": dict(
        takeaway="Strong El Niño seasons have usually been wet in Los Angeles and San Diego; the signal is weaker "
                 "inland and farther north."),
}

# Terms explained on hover (first use on each page) and listed on the Methods page.
GLOSSARY = {
    "El Niño": "A periodic warming of the central and eastern equatorial Pacific Ocean, with related changes in "
               "winds and rainfall, recurring every two to seven years.",
    "La Niña": "The cool counterpart of El Niño: below-normal ocean temperatures in the central and eastern "
               "equatorial Pacific.",
    "ENSO": "El Niño–Southern Oscillation: the cycle of El Niño, neutral and La Niña conditions and the related "
            "swing in air pressure across the tropical Pacific.",
    "anomaly": "The difference from normal (the 1991–2020 average) for the same time of year; +2 °C means 2 °C "
               "warmer than usual.",
    "anomalies": "Differences from normal (the 1991–2020 average) for the same time of year.",
    "Relative Oceanic Niño Index": "NOAA's official El Niño index (RONI): the Niño 3.4 anomaly measured relative to "
                                   "the average of the whole tropical ocean, so that general warming is not counted "
                                   "as El Niño. Three-month averages.",
    "RONI": "Relative Oceanic Niño Index, NOAA's official El Niño index: the Niño 3.4 anomaly measured relative to "
            "the average of the whole tropical ocean. Three-month averages.",
    "Niño 3.4": "A region of the central equatorial Pacific (5°S–5°N, 170°W–120°W) whose temperature is the main "
                "measure of El Niño.",
    "Niño 1+2": "The region off the coasts of Peru and Ecuador (10°S–0°, 90°W–80°W).",
    "Niño 3": "The eastern equatorial Pacific, 5°S–5°N, 150°W–90°W.",
    "Niño 4": "The western-central equatorial Pacific, 5°S–5°N, 160°E–150°W.",
    "thermocline": "The layer where temperature drops quickly with depth, separating warm surface water from cold "
                   "deep water; in the tropics it is marked by the 20 °C isotherm.",
    "20 °C isotherm": "The depth at which the ocean is 20 °C, used to mark the base of the warm upper layer.",
    "warm water volume": "The volume of water warmer than 20 °C near the equator (5°S–5°N, 120°E–80°W). It builds "
                         "up before an El Niño and is drained by it.",
    "warm pool": "The large area of very warm water (above about 28 °C) normally found in the western tropical "
                 "Pacific.",
    "upwelling": "The rise of cold, deep water toward the surface, normally strong along the equator and off "
                 "South America.",
    "trade winds": "Steady easterly winds over the tropical Pacific that push warm surface water toward the west.",
    "Kelvin waves": "Pulses of warm water that travel east along the equator beneath the surface, crossing the "
                    "Pacific in about two months.",
    "Hovmöller": "A diagram with position on one axis and time on the other, used to follow features as they move.",
    "reanalysis": "A best estimate of past ocean or weather conditions, made by combining observations with a "
                  "numerical model.",
    "GODAS": "NOAA's Global Ocean Data Assimilation System, an ocean reanalysis that estimates temperature below "
             "the surface.",
    "OISST": "NOAA's Optimum Interpolation Sea Surface Temperature: a daily 0.25° analysis of satellite, ship and "
             "buoy data since 1981.",
    "ERSST": "NOAA's Extended Reconstructed Sea Surface Temperature: a monthly 2° record since 1854.",
    "nClimGrid": "NOAA's gridded (about 5 km) monthly temperature and precipitation for the United States since "
                 "1895.",
    "GHCN-Daily": "NOAA's Global Historical Climatology Network of daily weather-station records.",
    "marine heatwave": "A spell of at least five days when sea surface temperature is above the 90th percentile for "
                       "the time of year (Hobday et al., 2016).",
    "water year": "October to September, labelled by the year in which it ends.",
    "Santa Ana": "Dry, often strong offshore winds that blow from the interior toward the Southern California "
                 "coast, mainly in autumn and winter.",
}
