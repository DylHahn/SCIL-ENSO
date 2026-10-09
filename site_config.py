"""
What the website contains: its tabs, the figures on each tab (in order), their short titles and
captions, and the page text. `update_site.py` reads this file; edit here to add, remove or reorder
figures.

Each page's `figures` list holds either a section heading, ("section", "Heading"), or a figure,
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
        lede="A strong El Niño is developing in the equatorial Pacific. These figures compare its surface and "
             "subsurface evolution with the strongest events since 1950, using NOAA observations, reanalysis "
             "and official forecasts.",
        summary=True,
        figures=[
            ("section", "Current state"),
            ("anim_sst.py", True, "Animation: sea surface temperature",
             "Animated month-by-month sea surface temperature across the tropical Pacific (NOAA OISST, 0.25°), "
             "January to the latest month, for 2026, 1997 and the 1991–2020 normal."),
            ("roni_vs_past_events.py", True, "Event development vs. past very strong events",
             "Development of the 2026–27 event in NOAA's Relative Oceanic Niño Index alongside the four strongest "
             "El Niño events since 1950, with NOAA's official forecast."),
            ("event_timeseries.py", True, "Anomaly time series across events",
             "Monthly anomaly time series for every El Niño since 1950, aligned by onset year: Niño 3.4 and Niño "
             "1+2 sea surface temperature and equatorial upper-ocean temperature."),
            ("section", "Compared with past very strong events"),
            ("surface_comparison.py", True, "Sea surface temperature by event",
             "Tropical Pacific sea surface temperature in the same month of each very strong El Niño year, with "
             "Niño 3.4 and tropical-mean anomalies."),
            ("subsurface_comparison.py", True, "Upper-ocean temperature by event",
             "Equatorial upper-ocean temperature at the same stage of each event; the current event holds "
             "substantially more subsurface heat."),
            ("anim_upper_ocean.py", False, "Animation: upper-ocean temperature",
             "Animated equatorial upper-ocean temperature sections for 2026, 1997 and the 1991–2020 normal; during "
             "El Niño the warm layer deepens in the east and the 20 °C line flattens."),
            ("hovmoller_sst.py", True, "Equatorial SST evolution (Hovmöller)",
             "Sea surface temperature along the equator, month by month (rows, top to bottom) and from the western "
             "Pacific to South America (left to right), for four very strong events."),
            ("hovmoller_upper_ocean.py", False, "Upper-ocean heat content (Hovmöller)",
             "The same layout for the average temperature of the upper 200 m; warm water spreading east beneath "
             "the surface marks Kelvin waves."),
            ("nino_regions.py", True, "Warming across the Niño regions",
             "Location of the four Niño regions and their monthly anomalies, showing where along the equator the "
             "warming is concentrated."),
            ("event_ranking.py", True, "Ranking of El Niño events since 1950",
             "El Niño events since 1950 ranked by peak strength, duration and accumulated intensity, with the "
             "current event completed by NOAA's median forecast."),
            ("section", "Forecasts and global context"),
            ("forecast_verification.py", True, "Verification of NOAA's 2026 forecasts",
             "Each monthly NOAA strength forecast issued since April 2026 compared with the observed RONI, and how "
             "confidence in a very strong peak has evolved."),
            ("global_temperature.py", True, "Global temperature and El Niño",
             "Annual global mean surface temperature anomalies; recent record years have coincided with El Niño "
             "events."),
        ],
        extra="",
        data=["Relative Oceanic Niño Index (RONI), outlook and strength probabilities: NOAA Climate Prediction Center",
              "NCEP GODAS ocean reanalysis: NOAA NCEP, via NOAA PSL",
              "OISST v2.1 and ERSST v5 sea surface temperature: NOAA NCEI, via NOAA PSL",
              "NOAAGlobalTemp v6 and global temperature series: NOAA NCEI",
              "Monthly Niño region indices (OISST v2.1): NOAA Climate Prediction Center"],
    ),
    dict(
        key="socal-heat", slug="socal", tab="Southern California Heat",
        title="Southern California Heat", kicker="Southern California Heat",
        h1="Southern California heat",
        lede="How summer heat across Southern California has increased since 1895, how the summer of 2026 "
             "compares, and how warm nights and hot days have changed at individual stations.",
        figures=[
            ("socal_warming_since_1895.py", True, "Long-term increase in summer heat",
             "Change in summer daytime highs and overnight lows since 1951–1980 across Southern California, and the "
             "regional summer temperature record since 1895 (NOAA nClimGrid)."),
            ("socal_marine_heat.py", True, "Marine heat in the Southern California Bight",
             "Daily sea surface temperature and marine heatwave days in the Southern California Bight since 1982 "
             "(NOAA OISST), with 2026 compared with 1997 and 2015."),
            ("socal_summer_anomalies.py", True, "Summer 2026 temperature anomalies",
             "June–September 2026 daytime-high and overnight-low anomalies across Southern California (NOAA "
             "nClimGrid, ~5 km), and the regional overnight-low anomaly for every summer since 1950."),
            ("socal_station_heat.py", True, "Warm nights and hot days by station",
             "Station counts of warm nights (≥ 65 °F) and hot days (≥ 90 °F) each summer since 1950 at Los "
             "Angeles, San Diego, the Inland Empire and Santa Barbara."),
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
