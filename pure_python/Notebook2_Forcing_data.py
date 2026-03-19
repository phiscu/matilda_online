# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Climate forcing data

# %% [markdown]
# Now that we have all the **static catchment data**, we can turn to the **climate forcing** needed for MATILDA.
#
# In this notebook we will...
#
# 1. request the **reference elevation** of the forcing data,
# 2. request **ERA5-Land temperature and precipitation** for the catchment,
# 3. inspect the returned time series,
# 4. and store the results for the next workflow steps.
#
# 🌦️ The aim is not only to obtain the data, but also to make each step easy to follow. Even when code cells are hidden in the final Jupyter Book, the printed outputs and figures should still show a clear workflow.

# %% [markdown]
# To get started, we read the settings from the `config.ini` file again.
#
# We will need:
#
# - paths for **input**, **output**, and **figures**,
# - the name of the output **GeoPackage** from Notebook 1,
# - whether **projections** are enabled,
# - whether a refreshed **ZIP archive** should be created,
# - and the **MATILDA-Webservice URL** plus **API key** for the requests.

# %%
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import ast
import configparser
import os

config = configparser.ConfigParser()
config.read("config.ini")

dir_input = config["FILE_SETTINGS"]["DIR_INPUT"]
dir_output = config["FILE_SETTINGS"]["DIR_OUTPUT"]
dir_figures = config["FILE_SETTINGS"]["DIR_FIGURES"]
output_gpkg = dir_output + config["FILE_SETTINGS"]["GPKG_NAME"]
scenarios = config.getboolean("CONFIG", "PROJECTIONS")
show_map = config.getboolean("CONFIG", "SHOW_MAP")
zip_output = config.getboolean("CONFIG", "ZIP_OUTPUT")

plt_style = ast.literal_eval(config["CONFIG"]["PLOT_STYLE"])

print(f"Output GeoPackage: {output_gpkg}")
print(f"Figure directory:  {dir_figures}")

# %% [markdown]
# If you have decided to back up your output files, you can now load them.

# %%
import zipfile

if zip_output:
    with zipfile.ZipFile("output_download.zip", "r") as z:
        z.extractall(dir_output)

    print(f'Extracted "output_download.zip" to "{dir_output}".')

# %% [markdown]
# Next, we load the **catchment geometry** from Notebook 1.
#
# This geometry is the spatial reference for all following requests:
#
# - the **reference elevation** is calculated for this catchment,
# - and the **ERA5-Land time series** are aggregated to exactly this area.

# %%
import geopandas as gpd
import json
import matplotlib.pyplot as plt

catchment_new = gpd.read_file(output_gpkg, layer="catchment_new")
catchment_geojson = json.loads(catchment_new.to_json())

print(f"Loaded catchment layer with {len(catchment_new)} feature(s).")
print(f"Catchment CRS: {catchment_new.crs}")
display(catchment_new.head(1))

# %% [markdown]
# ## ERA5-Land reference elevation

# %% [markdown]
# ERA5-Land provides the atmospheric forcing variables we need, but for a lumped hydrological model we also need one representative **reference elevation** of the forcing data. 
#
# This elevation is derived from the **surface geopotential**:
#
# > The geopotential height can be calculated by dividing the geopotential by the Earth's gravitational acceleration,
# > \(g = 9.80665\; m\; s^{-2}\).
#
# In practical terms, this gives us a representative elevation for the catchment-wide forcing data — similar in spirit to the elevation of a weather station.
#
# ✨ In the notebook, we simply request this value from the MATILDA-Webservice and inspect the result.

# %%
from tools.geetools import get_geopotential_webservice

geopot_data = get_geopotential_webservice(catchment_new)
mean_val = geopot_data["geopotential_mean"]
ele_dat = geopot_data["elevation_m"]

# %% [markdown]
# ***

# %% [markdown]
# ## ERA5-Land temperature and precipitation data

# %% [markdown]
# ### Select the date range
# The selected time period depends on whether the workflow should prepare **only past forcing data** or also support later **scenario processing**.
#
# - If `PROJECTIONS=False`, the date range is taken directly from the `config.ini`.
# - If `PROJECTIONS=True`, the workflow requests the historical period from **1979 onward** to provide a broader baseline for later bias adjustment.

# %%
if scenarios is True:
    date_range = ["1979-01-01", "2026-01-01"]
else:
    date_range = ast.literal_eval(config["CONFIG"]["DATE_RANGE"])

print(f"The selected date range is {date_range[0]} to {date_range[1]}")

# %% [markdown]
# ### Download ERA5-Land data
# For the MATILDA model, the key meteorological inputs are:
#
# - **air temperature**
# - **precipitation**
#
# We request both as **catchment-aggregated daily time series** for the selected period.
#
# The returned values are then converted into a compact `pandas.DataFrame`:
#
# - temperature from **Kelvin** to **°C**,
# - precipitation from **meters** to **millimeters**.
#
# > 💡 **How are the ERA5-Land data aggregated?**  
# > The ERA5-Land data has an approximate spatial resolution of 9 km. Depending on the size of your catchment area, the data may cover many or just a few grid cells. The web service calculates one area-weighted, catchment-wide average for each day. This means each cell is weighted according to its overlap with the catchment area.

# %%
from tools.geetools import get_climate_data_webservice

df = get_climate_data_webservice(catchment_new, date_range)
display(df.head())

# %% [markdown]
# The first rows already show the structure of the forcing data:
#
# - a timestamp,
# - the original temperature,
# - the original precipitation in m per day,
# - a readable date,
# - the converted temperature in °C,
# - and precipitation converted to mm per day.

# %%
import pandas as pd

summary_df = pd.DataFrame(
    {
        "variable": ["Temperature", "Precipitation"],
        "minimum": [df["temp_c"].min(), df["prec"].min()],
        "mean": [df["temp_c"].mean(), df["prec"].mean()],
        "maximum": [df["temp_c"].max(), df["prec"].max()],
        "unit": ["°C", "mm d-1"],
    }
)
print("Quick summary statistics of the forcing data:")
display(summary_df)

# %% [markdown]
# A time series plot provides a first impression of the seasonal signal and the variability of both variables.

# %%
import matplotlib.dates as mdates
import scienceplots

plt.style.use(plt_style)

axes = df[["dt", "temp_c", "prec"]].plot.line(
    x="dt",
    subplots=True,
    legend=False,
    figsize=(10, 5),
    title="ERA5-Land data for target catchment",
    color={"temp_c": "#A24600", "prec": "#005A9C"},
)

axes[0].set_ylabel("Temperature [$^\circ$C]")
axes[1].set_ylabel("Precipitation [mm]")
axes[1].set_xlabel("Date")
axes[1].xaxis.set_minor_locator(mdates.YearLocator())
plt.xlim(date_range)
plt.tight_layout()
plt.savefig(dir_figures + "NB2_ERA5_Temp_Prec.png")
plt.show()
print(f'Saved overview plot to "{dir_figures}NB2_ERA5_Temp_Prec.png".')

# %% [markdown]
# For long time series, a short close-up can be useful as well 🔎

# %%
from tools.plots import plot_mean_annual_cycle

fig, ax1, ax2, clim = plot_mean_annual_cycle(df)
fig.savefig(dir_figures + "NB2_ERA5_Temp_Prec_clim.png")

print(f'Saved climatology plot to "{dir_figures}NB2_ERA5_Temp_Prec_clim.png".')

# %% [markdown]
# ## Store data for next steps

# %% [markdown]
# To continue in the workflow, we store two outputs:
#
# - the **ERA5-Land forcing time series** as `ERA5L.csv`,
# - and the **reference elevation** in `settings.yml` as `ele_dat`.

# %%
era5l_path = dir_output + "ERA5L.csv"
df.to_csv(era5l_path, header=True, index=False)
print(f'ERA5-Land forcing data written to "{era5l_path}".')

# %%
from tools.helpers import update_yaml

update_yaml(dir_output + "settings.yml", {"ele_dat": float(ele_dat)})
print(f'Updated "{dir_output}settings.yml" with ele_dat = {float(ele_dat):.2f}.')

# %% [markdown]
# Finally, if requested in the `config.ini`, we refresh `output_download.zip` so that all newly generated output files can be downloaded together.

# %%
import shutil

if zip_output:
    shutil.make_archive("output_download", "zip", "output")
    print('Output folder refreshed and available as "output_download.zip".')
else:
    print("ZIP output disabled in config.ini")

# %% [markdown]
# ✅ Notebook 2 is complete. You can now continue with [Notebook 3](Notebook3_CMIP6.ipynb).
