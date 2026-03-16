from configparser import ConfigParser
from pathlib import Path
import pandas as pd
import concurrent.futures
import os
import sys
import requests
from retry import retry
from tqdm import tqdm
import ee
import json
import geopandas as gpd
import matplotlib.pyplot as plt

from configparser import ConfigParser
from pathlib import Path


def delineate_catchment_mghydro(
    lat,
    lon,
    watershed_output_path,
    rivers_output_path=None,
    precision="high",
    plot=False,
    timeout=120,
):
    """
    Delineate a catchment and fetch upstream rivers from the MG Hydro /
    Global Watersheds API.

    This helper uses the public API of the Global Watersheds web app:
    https://mghydro.com/watersheds/

    API/help documentation:
    https://mghydro.com/watersheds/help.html

    Python demo notebook by the author:
    https://mghydro.com/demo-use-the-global-watersheds-api-and-python-to-automatically-delineate-watersheds/

    Related GitHub materials:
    https://gist.github.com/mheberger/c05f10de225fbee8f572c5dfbb38d0b5
    https://github.com/mheberger/delineator

    Author / maintainer:
    Matthew Heberger (mheberger)
    https://github.com/mheberger
    https://mghydro.com/author/mheberger/

    Notes
    -----
    The Global Watersheds app and API are based on global hydrographic datasets
    including MERIT-Hydro / MERIT-Basins and provide fast watershed delineation
    and upstream river extraction. The service is very useful for rapid
    catchment screening, but results should always be checked visually before
    further use in analysis workflows.

    Parameters
    ----------
    lat : float
        Latitude of the outlet / pour point.
    lon : float
        Longitude of the outlet / pour point.
    watershed_output_path : str or Path
        Output path for the watershed GeoJSON.
    rivers_output_path : str or Path, optional
        Output path for the upstream rivers GeoJSON.
        If None, a filename based on watershed_output_path is created.
    precision : str, optional
        Delineation precision, either 'low' or 'high'. Default is 'high'.
        For very large basins, the service may automatically fall back to
        lower precision.
    plot : bool, optional
        If True, create a quick visual check plot with catchment boundary,
        river network, and outlet point.
    timeout : int, optional
        Timeout in seconds for each API request.

    Returns
    -------
    tuple
        (watershed_gdf, rivers_gdf)

    Raises
    ------
    ValueError
        If precision is invalid.
    RuntimeError
        If the API request fails or returns invalid data.
    """
    
    precision = str(precision).strip().lower()
    if precision not in {"low", "high"}:
        raise ValueError("precision must be 'low' or 'high'")

    watershed_output_path = Path(watershed_output_path)
    watershed_output_path.parent.mkdir(parents=True, exist_ok=True)

    if rivers_output_path is None:
        rivers_output_path = watershed_output_path.with_name(
            watershed_output_path.stem + "_rivers.geojson"
        )
    else:
        rivers_output_path = Path(rivers_output_path)
        rivers_output_path.parent.mkdir(parents=True, exist_ok=True)

    base_url = "https://mghydro.com/app"
    params = {
        "lat": float(lat),
        "lng": float(lon),
        "precision": precision,
    }

    endpoints = {
        "watershed": f"{base_url}/watershed_api",
        "rivers": f"{base_url}/upstream_rivers_api",
    }

    def _fetch_geojson(url, label):
        try:
            response = requests.get(url, params=params, timeout=timeout)
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to reach MG Hydro {label} API: {e}") from e

        if response.status_code == 400:
            raise RuntimeError(
                f"MG Hydro {label} request was rejected (400 Bad Request). "
                f"Check coordinates and parameters. Response: {response.text}"
            )
        elif response.status_code == 404:
            raise RuntimeError(
                f"MG Hydro {label} could not create a result (404 Not Found). "
                f"This can happen for unsuitable outlet points, e.g. over the ocean. "
                f"Response: {response.text}"
            )
        elif response.status_code == 500:
            raise RuntimeError(
                f"MG Hydro {label} returned 500 Internal Server Error. "
                f"Response: {response.text}"
            )
        elif response.status_code != 200:
            raise RuntimeError(
                f"MG Hydro {label} request failed with status {response.status_code}. "
                f"Response: {response.text}"
            )

        content_type = response.headers.get("Content-Type", "")
        if "json" not in content_type and "geojson" not in content_type and response.text[:1] not in "{[":
            raise RuntimeError(
                f"MG Hydro {label} returned unexpected content type '{content_type}'."
            )

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise RuntimeError(f"MG Hydro {label} returned invalid JSON") from e

        if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
            raise RuntimeError(
                f"MG Hydro {label} did not return a GeoJSON FeatureCollection."
            )

        return data

    watershed_data = _fetch_geojson(endpoints["watershed"], "watershed")
    rivers_data = _fetch_geojson(endpoints["rivers"], "rivers")

    watershed_output_path.write_text(json.dumps(watershed_data), encoding="utf-8")
    rivers_output_path.write_text(json.dumps(rivers_data), encoding="utf-8")

    watershed_gdf = gpd.read_file(watershed_output_path)
    rivers_gdf = gpd.read_file(rivers_output_path)

    if watershed_gdf.empty:
        raise RuntimeError("MG Hydro watershed result is empty.")
    if rivers_gdf.empty:
        print("Warning: MG Hydro returned an empty upstream rivers layer.")

    if plot:
        fig, ax = plt.subplots(figsize=(8, 8))

        if not rivers_gdf.empty:
            rivers_gdf.plot(ax=ax, linewidth=0.8, label="Rivers")

        watershed_gdf.boundary.plot(ax=ax, linewidth=1.5, label="Catchment boundary")

        ax.scatter(lon, lat, marker="o", s=40, label="Outlet point")
        ax.set_title(f"Catchment delineation (MG Hydro, precision={precision})")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_aspect("equal")
        ax.legend()

        plt.show()

    return watershed_gdf, rivers_gdf


def load_webservice_config(config_path=None, section="GOOGLE"):
    """
    Load settings from webservices.ini.

    Parameters
    ----------
    config_path : str or Path, optional
        Path to webservices.ini. If None, defaults to repo_root/webservices.ini
        assuming this file lives in tools/.
    section : str, optional

    Returns
    -------
    dict
        Dictionary with keys and values from the requested section.

    Raises
    ------
    FileNotFoundError
        If the config file does not exist.
    KeyError
        If the requested section is missing.
    ValueError
        If required keys for the section are missing.
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "webservices.ini"
    else:
        config_path = Path(config_path).resolve()

    if not config_path.exists():
        raise FileNotFoundError(f"Webservice config file not found: {config_path}")

    parser = ConfigParser()
    parser.optionxform = str
    parser.read(config_path)

    if section not in parser:
        raise KeyError(f"Section [{section}] not found in {config_path}")

    config = dict(parser[section])

    required_keys_by_section = {
    "GOOGLE": ["PUBLIC_CLOUD_PROJECT", "PUBLIC_API_KEY", "BASE_URL"],
    "HU": ["MEDIA_API_URL", "MEDIA_PRIVATE_KEY", "MEDIA_USER"],
    }

    required_keys = required_keys_by_section.get(section, [])
    missing = [key for key in required_keys if key not in config or not config[key].strip()]
    if missing:
        raise ValueError(
            f"Missing required keys in [{section}] of {config_path}: {missing}"
        )

    if section == "GOOGLE":
        config["TIMEOUT"] = int(config.get("TIMEOUT", 120))

    return config
    
    
def authenticate_and_initialize_ee(cloud_project):
    """
    Robustly authenticates and initializes Earth Engine for local/notebook environments.

    It attempts to initialize Earth Engine:
    1. Using existing credentials if available and valid for the project.
    2. If a permission error occurs, it forces a new interactive browser-based
       authentication suitable for notebooks.

    Args:
        cloud_project (str): The Google Cloud Project ID to use for Earth Engine.

    Raises:
        RuntimeError: If Earth Engine initialization ultimately fails after retries.
    """
    print(f"--- Attempting Earth Engine Setup for project: {cloud_project} ---")

    # --- First Attempt: Try to initialize with any existing, valid credentials ---
    try:
        print("1. Trying to initialize with existing credentials...")
        ee.Initialize(project=cloud_project)
        # Verify with a simple API call to ensure permissions are correct
        _ = ee.Image("CGIAR/SRTM90_V4").getInfo()
        print(f"✅ Earth Engine successfully initialized with existing credentials for project: {cloud_project}")
        return # Success, exit function

    except ee.EEException as e:
        msg = str(e)
        if "Caller does not have required permission" in msg:
            print(f"Initial attempt failed due to permission error: {e}")
            print("This likely means existing credentials are for the wrong account/project, or lack permissions.")
            print("Proceeding to force a new interactive authentication.")
        else:
            # Handle other EE exceptions (e.g., project not found, invalid API key etc.)
            print(f"Initial attempt failed with an unexpected Earth Engine error: {e}")
            print("Proceeding to force a new interactive authentication, as this might resolve it.")
    except Exception as e:
        print(f"Initial attempt failed with an unexpected general error: {e}")
        print("Proceeding to force a new interactive authentication, as this might resolve it.")


    # --- Second Attempt: Force a new interactive browser-based authentication ---
    print("\n--- Forcing New Earth Engine Authentication ---")
    print("A browser window should open (or instructions to copy/paste a URL).")
    print("Please select the Google Account that has access to your Earth Engine project.")
    print("-----------------------------------")
    
    try:
        # Clear in-memory credentials just in case
        ee.Reset() 
        
        # Explicitly use 'notebook' auth_mode for Jupyter environments or 'paste' as a fallback
        try:
            print("Attempting authentication with auth_mode='notebook'...")
            ee.Authenticate(force=True, auth_mode='notebook') 
        except Exception as notebook_auth_error:
            print(f"Auth_mode='notebook' failed or didn't prompt: {notebook_auth_error}")
            print("Falling back to auth_mode='paste' (you may need to copy/paste a URL).")
            ee.Authenticate(force=True, auth_mode='paste') # This will provide a URL if it can't open a browser

        print("\nAuthentication flow completed. Attempting re-initialization...")
        ee.Initialize(project=cloud_project)

        # Verify with a simple API call again
        _ = ee.Image("CGIAR/SRTM90_V4").getInfo()
        print(f"✅ Earth Engine successfully initialized with new credentials for project: {cloud_project}")
        return # Success, exit function

    except ee.EEException as e:
        msg = str(e)
        print(f"\n❌ Earth Engine setup FAILED even after forced authentication for project: {cloud_project}")
        print(f"Final Error: {e}")
        if "Caller does not have required permission" in msg:
            raise RuntimeError(
                f"Earth Engine permission error for project '{cloud_project}' after forced authentication. "
                "Please ensure: \n"
                "  1. Earth Engine is ENABLED for this project (check Google Cloud Console).\n"
                "  2. The Google Account you selected during authentication has the 'Earth Engine User' IAM role for this project.\n"
                "  3. You selected the CORRECT Google Account during the browser login."
            ) from e
        else:
            raise RuntimeError(
                f"Earth Engine initialization failed with an unexpected error after forced authentication for project '{cloud_project}'."
            ) from e

    except Exception as e:
        raise RuntimeError(
            f"An unexpected error occurred during Earth Engine setup after forced authentication: {e}"
        ) from e


def download_dem_webservice(lat, lon, buffer_m, asset_id, output_path, config_path=None):
    """
    Download a DEM GeoTIFF from the MATILDA webservice and save it locally.

    Parameters
    ----------
    lat : float
        Latitude of the pour point.
    lon : float
        Longitude of the pour point.
    buffer_m : int or float
        Buffer radius in meters used to create the request box.
    asset_id : str
        Earth Engine asset ID of the DEM.
    output_path : str or Path
        Local output path for the downloaded GeoTIFF.
    config_path : str or Path, optional
        Optional path to webservices.ini.

    Returns
    -------
    Path
        Path to the saved GeoTIFF file.

    Raises
    ------
    RuntimeError
        If the webservice request fails or returns unexpected content.
    """
    cfg = load_webservice_config(config_path=config_path, section="GOOGLE")

    service_url = f"{cfg['BASE_URL'].rstrip('/')}/download-dem"

    payload = {
        "lat": float(lat),
        "lon": float(lon),
        "buffer_m": float(buffer_m),
        "asset_id": asset_id,
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": cfg["PUBLIC_API_KEY"],
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.post(
            service_url,
            json=payload,
            headers=headers,
            timeout=cfg["TIMEOUT"],
        )
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to reach DEM webservice: {e}") from e

    if not response.ok:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(
            f"DEM webservice request failed with status {response.status_code}: {detail}"
        )

    content_type = response.headers.get("Content-Type", "")
    if "image/tiff" not in content_type:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(
            f"DEM webservice returned unexpected content type '{content_type}': {detail}"
        )

    output_path.write_bytes(response.content)
    return output_path


class CMIPDownloader:
    """Class to download spatially averaged CMIP6 data for a given period, variable, and spatial subset."""

    def __init__(self, var, starty, endy, shape, processes=10, dir='./'):
        self.var = var
        self.starty = starty
        self.endy = endy
        self.shape = shape
        self.processes = processes
        self.directory = dir

        # create the download directory if it doesn't exist
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

    def download(self):
        """Runs a subset routine for CMIP6 data on GEE servers to create ee.FeatureCollections for all years in
        the requested period. Downloads individual years in parallel processes to increase the download time."""
        
        print('Initiating download request for NEX-GDDP-CMIP6 data from ' +
              str(self.starty) + ' to ' + str(self.endy) + '.')

        def getRequests(starty, endy):
            """Generates a list of years to be downloaded. [Client side]"""

            return [i for i in range(starty, endy+1)]

        @retry(tries=10, delay=1, backoff=2)
        def getResult(index, year):
            """Handle the HTTP requests to download one year of CMIP6 data. [Server side]"""

            start = str(year) + '-01-01'
            end = str(year + 1) + '-01-01'
            startDate = ee.Date(start)
            endDate = ee.Date(end)
            n = endDate.difference(startDate, 'day').subtract(1)

            def getImageCollection(var):
                """Create and image collection of CMIP6 data for the requested variable, period, and region.
                [Server side]"""
                collection = ee.ImageCollection('NASA/GDDP-CMIP6') \
                    .select(var) \
                    .filterDate(startDate, endDate) \
                    .filterBounds(self.shape) \
                    .filter(ee.Filter.neq('model', 'NorESM2-LM'))  # Exclude model (missing year 2096)

                return collection

            def renameBandName(b):
                """Edit variable names for better readability. [Server side]"""

                split = ee.String(b).split('_')
                return ee.String(split.splice(split.length().subtract(2), 1).join("_"))

            def buildFeature(i):
                """Create an area weighted average of the defined region for every day in the given year.
                [Server side]"""

                t1 = startDate.advance(i, 'day')
                t2 = t1.advance(1, 'day')
                # feature = ee.Feature(point)
                dailyColl = collection.filterDate(t1, t2)
                dailyImg = dailyColl.toBands()
                # renaming and handling names
                bands = dailyImg.bandNames()
                renamed = bands.map(renameBandName)
                # Daily extraction and adding time information
                dict = dailyImg.rename(renamed).reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=self.shape,
                ).combine(
                    ee.Dictionary({'system:time_start': t1.millis(), 'isodate': t1.format('YYYY-MM-dd')})
                )
                return ee.Feature(None, dict)

            # Create features for all days in the respective year. [Server side]
            collection = getImageCollection(self.var)
            year_feature = ee.FeatureCollection(ee.List.sequence(0, n).map(buildFeature))

            # Create a download URL for a CSV containing the feature collection. [Server side]
            url = year_feature.getDownloadURL()

            # Handle downloading the actual csv for one year. [Client side]
            r = requests.get(url, stream=True)
            if r.status_code != 200:
                r.raise_for_status()
            filename = os.path.join(self.directory, 'cmip6_' + self.var + '_' + str(year) + '.csv')
            with open(filename, 'w') as f:
                f.write(r.text)

            return index

        # Create a list of years to be downloaded. [Client side]
        items = getRequests(self.starty, self.endy)

        # Launch download requests in parallel processes and display a status bar. [Client side]
        with tqdm(total=len(items), desc="Downloading CMIP6 data for variable '" + self.var + "'") as pbar:
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.processes) as executor:
                for i, year in enumerate(items):
                    results.append(executor.submit(getResult, i, year))
                for future in concurrent.futures.as_completed(results):
                    index = future.result()
                    pbar.update(1)

        print("All downloads complete.")


class CMIPProcessor:
    """Class to read and pre-process CSV files downloaded by the CMIPDownloader class."""
    def __init__(self, var, file_dir='.'):
        self.file_dir = file_dir
        self.var = var
        self.df_hist = self.append_df(self.var, self.file_dir, hist=True)
        self.df_ssp = self.append_df(self.var, self.file_dir, hist=False)
        self.ssp2_common, self.ssp5_common, self.hist_common,\
            self.common_models, self.dropped_models = self.process_dataframes()
        self.ssp2, self.ssp5 = self.get_results()

    def read_cmip(self, filename):
        """Reads CMIP6 CSV files and drops redundant columns."""

        df = pd.read_csv(filename, index_col='isodate', parse_dates=['isodate'])
        df = df.drop(['system:index', '.geo', 'system:time_start'], axis=1)
        return df

    def append_df(self, var, file_dir='.', hist=True):
        """Reads CMIP6 CSV files of individual years and concatenates them into dataframes for the full downloaded
        period. Historical and scenario datasets are treated separately. Converts precipitation unit to mm."""

        df_list = []
        if hist:
            starty = 1979
            endy = 2014
        else:
            starty = 2015
            endy = 2100
        for i in range(starty, endy + 1):
            filename = file_dir + 'cmip6_' + var + '_' + str(i) + '.csv'
            df_list.append(self.read_cmip(filename))
        if hist:
            hist_df = pd.concat(df_list)
            if var == 'pr':
                hist_df = hist_df * 86400       # from kg/(m^2*s) to mm/day
            return hist_df
        else:
            ssp_df = pd.concat(df_list)
            if var == 'pr':
                ssp_df = ssp_df * 86400       # from kg/(m^2*s) to mm/day
            return ssp_df

    def process_dataframes(self):
        """Separates the two scenarios and drops models not available for both scenarios and the historical period."""

        ssp2 = self.df_ssp.loc[:, self.df_ssp.columns.str.startswith('ssp245')]
        ssp5 = self.df_ssp.loc[:, self.df_ssp.columns.str.startswith('ssp585')]
        hist = self.df_hist.loc[:, self.df_hist.columns.str.startswith('historical')]

        ssp2.columns = ssp2.columns.str.lstrip('ssp245_').str.rstrip('_' + self.var)
        ssp5.columns = ssp5.columns.str.lstrip('ssp585_').str.rstrip('_' + self.var)
        hist.columns = hist.columns.str.lstrip('historical_').str.rstrip('_' + self.var)

        # Get all the models the three datasets have in common
        common_models = set(ssp2.columns).intersection(ssp5.columns).intersection(hist.columns)

        # Get the model names that contain NaN values
        nan_models_list = [df.columns[df.isna().any()].tolist() for df in [ssp2, ssp5, hist]]
        # flatten the list
        nan_models = [col for sublist in nan_models_list for col in sublist]
        # remove duplicates
        nan_models = list(set(nan_models))

        # Remove models with NaN values from the list of common models
        common_models = [x for x in common_models if x not in nan_models]

        ssp2_common = ssp2.loc[:, common_models]
        ssp5_common = ssp5.loc[:, common_models]
        hist_common = hist.loc[:, common_models]

        dropped_models = list(set([mod for mod in ssp2.columns if mod not in common_models] +
                                  [mod for mod in ssp5.columns if mod not in common_models] +
                                  [mod for mod in hist.columns if mod not in common_models]))

        return ssp2_common, ssp5_common, hist_common, common_models, dropped_models

    def get_results(self):
        """Concatenates historical and scenario data to combined dataframes of the full downloaded period.
        Arranges the models in alphabetical order."""

        ssp2_full = pd.concat([self.hist_common, self.ssp2_common])
        ssp2_full.index.names = ['TIMESTAMP']
        ssp5_full = pd.concat([self.hist_common, self.ssp5_common])
        ssp5_full.index.names = ['TIMESTAMP']

        ssp2_full = ssp2_full.reindex(sorted(ssp2_full.columns), axis=1)
        ssp5_full = ssp5_full.reindex(sorted(ssp5_full.columns), axis=1)


        return ssp2_full, ssp5_full

