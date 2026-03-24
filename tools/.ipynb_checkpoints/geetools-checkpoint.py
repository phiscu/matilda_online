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
import io
import time
import threading
import getpass

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
    fallback_to_local=False,
    fallback_dem_asset_id="MERIT/DEM/v1_0_3",
    fallback_dem_filename="dem_gee.tif",
    fallback_buffer_m=40000,
    fallback_bbox=None,
    dem_config_path=None,
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
    fallback_to_local : bool, optional
        If True, fall back to local pysheds delineation when the MG Hydro
        request fails. Default is False.
    dem_asset_id : str, optional
        Earth Engine asset ID of the DEM used for local fallback delineation.
    dem_filename : str or Path, optional
        DEM filename used for local fallback delineation.
    fallback_buffer_m : int or float, optional
        Default buffer radius in meters for local fallback delineation.
    fallback_bbox : list or tuple, optional
        Optional custom bounding box [xmin, ymin, xmax, ymax] for local
        fallback delineation. If None, the user is prompted for a bbox.
    dem_config_path : str or Path, optional
        Optional path to webservices.ini for local DEM download.

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
    from pathlib import Path
    import json
    import requests
    import geopandas as gpd
    import matplotlib.pyplot as plt

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

    try:
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

    except Exception as e:
        if not fallback_to_local:
            raise

        if fallback_dem_asset_id is None or fallback_dem_filename is None:
            raise RuntimeError(
                "MG Hydro delineation failed and local fallback is not fully configured. "
                "Please provide fallback_dem_asset_id and dem_filename."
            ) from e

        print("MG Hydro delineation failed.")
        print(f"Reason: {e}")
        print("Falling back to local delineation with pysheds...")

        bbox_to_use = fallback_bbox

        if bbox_to_use is None:
            print(
                "Please provide a custom DEM bounding box in geographic coordinates:\n"
                "bbox = [xmin, ymin, xmax, ymax]"
            )
            bbox_str = input("Enter bbox as xmin,ymin,xmax,ymax: ").strip()

            try:
                bbox_to_use = [float(x) for x in bbox_str.split(",")]
            except Exception as parse_err:
                raise RuntimeError(
                    "Could not parse bbox input. Expected format: xmin,ymin,xmax,ymax"
                ) from parse_err

            if len(bbox_to_use) != 4:
                raise RuntimeError(
                    "Invalid bbox input. Expected exactly 4 values: xmin,ymin,xmax,ymax"
                )

            xmin, ymin, xmax, ymax = bbox_to_use
            if not (xmin < xmax and ymin < ymax):
                raise RuntimeError(
                    "Invalid bbox input. Expected xmin < xmax and ymin < ymax."
                )

        watershed_gdf, info = delineate_catchment_local(
            lat=lat,
            lon=lon,
            dem_filename=fallback_dem_filename,
            catchment_filename=watershed_output_path,
            asset_id=fallback_dem_asset_id,
            buffer_m=fallback_buffer_m,
            bbox=bbox_to_use,
            config_path=dem_config_path,
        )

        rivers_gdf = gpd.GeoDataFrame(geometry=[], crs=watershed_gdf.crs)
        if rivers_output_path is not None:
            Path(rivers_output_path).parent.mkdir(parents=True, exist_ok=True)
            rivers_gdf.to_file(rivers_output_path, driver="GeoJSON")

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
    

def _prompt_for_api_key(prompt_text="API key not found in config or environment. Please paste your MATILDA-Online API key: "):
    """Prompt interactively for an API key without echoing it to the screen."""
    try:
        return getpass.getpass(prompt_text).strip()
    except Exception:
        return input(prompt_text).strip()



def resolve_api_key(config=None, env_var="MATILDA_API_KEY", prompt_if_missing=True):
    """
    Resolve the MATILDA webservice API key.

    Priority
    --------
    1. MATILDA_API_KEY environment variable
    2. PUBLIC_API_KEY from webservices.ini
    3. Interactive prompt (optional)
    """
    env_key = os.environ.get(env_var, "").strip()
    if env_key:
        return env_key

    if config is not None:
        cfg_key = str(config.get("PUBLIC_API_KEY", "")).strip()
        if cfg_key:
            return cfg_key

    if not prompt_if_missing:
        raise ValueError(
            "No MATILDA webservice API key found. Provide MATILDA_API_KEY as an "
            "environment variable, add PUBLIC_API_KEY to webservices.ini, or enter it "
            "interactively."
        )

    api_key = _prompt_for_api_key()
    if not api_key:
        raise ValueError("No API key provided.")
    return api_key



def load_webservice_config(config_path=None, section="GOOGLE", prompt_for_api_key=True):
    """
    Load settings from webservices.ini.

    Parameters
    ----------
    config_path : str or Path, optional
        Path to webservices.ini. If None, defaults to repo_root/webservices.ini
        assuming this file lives in repo_root.
    section : str, optional
    prompt_for_api_key : bool, optional
        If True and section is [GOOGLE], prompt interactively for an API key when
        neither MATILDA_API_KEY nor PUBLIC_API_KEY is available.

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
    "GOOGLE": ["PUBLIC_CLOUD_PROJECT", "BASE_URL"],
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
        config["PUBLIC_API_KEY"] = resolve_api_key(
            config=config,
            prompt_if_missing=prompt_for_api_key,
        )

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


def download_dem_webservice(
    output_path,
    asset_id,
    lat=None,
    lon=None,
    buffer_m=None,
    geometry=None,
    config_path=None,
):
    """
    Download a DEM GeoTIFF from the MATILDA webservice and save it locally.

    Parameters
    ----------
    output_path : str or Path
        Local output path for the downloaded GeoTIFF.
    asset_id : str
        Earth Engine asset ID of the DEM.
    lat : float, optional
        Latitude of the pour point. Must be used together with lon.
    lon : float, optional
        Longitude of the pour point. Must be used together with lat.
    buffer_m : int or float, optional
        Buffer radius in meters used to create the request box when using
        lat/lon input.
    geometry : dict or geopandas.GeoDataFrame or shapely geometry, optional
        Polygon geometry to send directly to the webservice. This is the
        preferred option when a catchment outline is already available.
    config_path : str or Path, optional
        Optional path to webservices.ini.

    Returns
    -------
    Path
        Path to the saved GeoTIFF file.

    Raises
    ------
    ValueError
        If neither a valid point+buffer nor a valid geometry is provided.
    RuntimeError
        If the webservice request fails or returns unexpected content.
    """

    try:
        from IPython.display import clear_output
        in_notebook = True
    except Exception:
        in_notebook = False

    cfg = load_webservice_config(config_path=config_path, section="GOOGLE")
    service_url = f"{cfg['BASE_URL'].rstrip('/')}/download-dem"

    payload = {
        "asset_id": asset_id,
    }

    if geometry is not None:
        # GeoDataFrame -> first geometry
        if hasattr(geometry, "geometry"):
            if len(geometry) == 0:
                raise ValueError("Provided GeoDataFrame is empty.")
            geometry = geometry.geometry.iloc[0]

        # shapely geometry -> GeoJSON-like dict
        if hasattr(geometry, "__geo_interface__"):
            geometry = geometry.__geo_interface__

        if not isinstance(geometry, dict):
            raise ValueError(
                "geometry must be a GeoJSON-like dict, a GeoDataFrame, or a shapely geometry."
            )

        geom_type = geometry.get("type")
        coords = geometry.get("coordinates")

        if geom_type not in {"Polygon", "MultiPolygon"} or coords is None:
            raise ValueError(
                "geometry must be a Polygon or MultiPolygon with coordinates."
            )

        payload["geometry"] = {
            "type": geom_type,
            "coordinates": coords,
        }

    else:
        if lat is None or lon is None or buffer_m is None:
            raise ValueError(
                "Provide either geometry, or lat/lon together with buffer_m."
            )

        payload["lat"] = float(lat)
        payload["lon"] = float(lon)
        payload["buffer_m"] = float(buffer_m)

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": cfg["PUBLIC_API_KEY"],
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    try:
        response = requests.post(
            service_url,
            json=payload,
            headers=headers,
            timeout=cfg["TIMEOUT"],
            stream=True,
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

    total_size = int(response.headers.get("Content-Length", 0))
    downloaded = 0
    chunk_size = 1024 * 1024  # 1 MB

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if not chunk:
                continue
            f.write(chunk)
            downloaded += len(chunk)

            elapsed = time.time() - start_time
            if in_notebook:
                clear_output(wait=True)

            print("⏳ Downloading DEM from the MATILDA web service...")
            if total_size > 0:
                progress_pct = downloaded / total_size * 100
                print(
                    f"Downloaded: {downloaded / 1024**2:,.1f} / {total_size / 1024**2:,.1f} MB "
                    f"({progress_pct:.1f}%)"
                )
            else:
                print(f"Downloaded: {downloaded / 1024**2:,.1f} MB")
            print(f"Elapsed time: {elapsed:,.1f} s")

    elapsed_total = time.time() - start_time

    if in_notebook:
        clear_output(wait=True)

    print("✅ DEM successfully downloaded from the MATILDA web service.")
    print(f"Saved to: {output_path}")
    print(f"File size: {downloaded / 1024**2:,.1f} MB")
    print(f"Elapsed time: {elapsed_total:,.1f} s")
    return


def download_dem_for_bbox(
    bbox,
    output_path,
    asset_id,
    config_path=None,
):
    """
    Download a DEM for a custom geographic bounding box.

    Parameters
    ----------
    bbox : list or tuple
        Bounding box as [xmin, ymin, xmax, ymax] in lon/lat coordinates.
    output_path : str or Path
        Local output path for the downloaded GeoTIFF.
    asset_id : str
        Earth Engine asset ID of the DEM.
    config_path : str or Path, optional
        Optional path to webservices.ini.

    Returns
    -------
    Path
        Path to the saved GeoTIFF file.

    Raises
    ------
    ValueError
        If bbox is invalid.
    """
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise ValueError("bbox must be a list or tuple: [xmin, ymin, xmax, ymax]")

    xmin, ymin, xmax, ymax = map(float, bbox)
    if not (xmin < xmax and ymin < ymax):
        raise ValueError("bbox must satisfy xmin < xmax and ymin < ymax")

    geometry = {
        "type": "Polygon",
        "coordinates": [[
            [xmin, ymin],
            [xmax, ymin],
            [xmax, ymax],
            [xmin, ymax],
            [xmin, ymin],
        ]]
    }

    return download_dem_webservice(
        output_path=output_path,
        asset_id=asset_id,
        geometry=geometry,
        config_path=config_path,
    )


def delineate_catchment_local(
    lat,
    lon,
    dem_filename,
    catchment_filename,
    asset_id,
    buffer_m=40000,
    bbox=None,
    snap_acc_threshold=1000,
    config_path=None,
):
    """
    Delineate a catchment locally with pysheds after downloading a DEM.

    The function uses the MATILDA DEM webservice to download a DEM either for
    a default square around the outlet point or for a custom bounding box.
    It then performs local delineation with pysheds.

    If the resulting catchment touches the DEM boundary, the DEM extent is
    likely too small and the function raises an error asking the user to
    provide a custom lat/lon bounding box.

    Parameters
    ----------
    lat : float
        Latitude of the outlet / pour point.
    lon : float
        Longitude of the outlet / pour point.
    dem_filename : str or Path
        Output path for the downloaded DEM GeoTIFF.
    catchment_filename : str or Path
        Output path for the delineated catchment GeoJSON.
    asset_id : str
        Earth Engine asset ID of the DEM to download.
    buffer_m : int or float, optional
        Buffer radius in meters for the default DEM download box.
        Ignored when bbox is provided.
    bbox : list or tuple, optional
        Custom bounding box in geographic coordinates:
        [xmin, ymin, xmax, ymax].
    snap_acc_threshold : int or float, optional
        Accumulation threshold used to snap the outlet point to the channel
        network. Default is 1000.
    config_path : str or Path, optional
        Optional path to webservices.ini.

    Returns
    -------
    tuple
        (catchment_gdf, info)

        catchment_gdf : geopandas.GeoDataFrame
            Delineated catchment polygon.
        info : dict
            Dictionary with useful diagnostics:
            - dem_filename
            - catchment_filename
            - snapped_lon
            - snapped_lat
            - bbox_used
            - edge_touched

    Raises
    ------
    RuntimeError
        If delineation fails or if the DEM extent appears too small.
    ValueError
        If bbox is invalid.
    """
    from pathlib import Path

    import numpy as np
    import geopandas as gpd
    from shapely.geometry import shape
    from rasterio.features import shapes
    from pysheds.grid import Grid

    dem_filename = Path(dem_filename)
    catchment_filename = Path(catchment_filename)
    dem_filename.parent.mkdir(parents=True, exist_ok=True)
    catchment_filename.parent.mkdir(parents=True, exist_ok=True)

    if bbox is not None:
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise ValueError("bbox must be a list or tuple: [xmin, ymin, xmax, ymax]")

        xmin, ymin, xmax, ymax = map(float, bbox)
        if not (xmin < xmax and ymin < ymax):
            raise ValueError("bbox must satisfy xmin < xmax and ymin < ymax")

        bbox_used = [xmin, ymin, xmax, ymax]

        if dem_filename.exists():
            print(f"Using existing DEM: {dem_filename}")
        else:
            print("Downloading DEM for custom bounding box...")
            download_dem_for_bbox(
                bbox=bbox_used,
                output_path=dem_filename,
                asset_id=asset_id,
                config_path=config_path,
            )
    else:
        bbox_used = None
        if dem_filename.exists():
            print(f"Using existing DEM: {dem_filename}")
        else:
            print(f"Downloading DEM for default {buffer_m} m box around outlet point...")
            download_dem_webservice(
                output_path=dem_filename,
                asset_id=asset_id,
                lat=lat,
                lon=lon,
                buffer_m=buffer_m,
                config_path=config_path,
            )

    print("Loading DEM into pysheds...")
    grid = Grid.from_raster(str(dem_filename))
    dem = grid.read_raster(str(dem_filename))

    print("Filling depressions...")
    flooded_dem = grid.fill_depressions(dem)

    print("Resolving flats...")
    inflated_dem = grid.resolve_flats(flooded_dem)

    dirmap = (64, 128, 1, 2, 4, 8, 16, 32)

    print("Computing flow directions...")
    fdir = grid.flowdir(inflated_dem, dirmap=dirmap)

    print("Computing flow accumulation...")
    acc = grid.accumulation(fdir, dirmap=dirmap)

    print("Snapping outlet point to channel network...")
    x_snap, y_snap = grid.snap_to_mask(acc > snap_acc_threshold, (lon, lat))

    print("Delineating catchment...")
    catch = grid.catchment(
        x=x_snap,
        y=y_snap,
        fdir=fdir,
        dirmap=dirmap,
        xytype="coordinate",
    )

    catch_view = np.asarray(grid.view(catch), dtype=np.uint8)

    edge_touched = bool(
        catch_view[0, :].any()
        or catch_view[-1, :].any()
        or catch_view[:, 0].any()
        or catch_view[:, -1].any()
    )

    if edge_touched:
        raise RuntimeError(
            "Local delineation touches the DEM boundary. "
            "The DEM extent is likely too small. "
            "Please provide a larger custom lat/lon bounding box "
            "as bbox=[xmin, ymin, xmax, ymax]."
        )

    print("Converting delineated catchment raster to polygon...")
    polygons = []
    for geom, value in shapes(
        catch_view,
        mask=catch_view.astype(bool),
        transform=grid.affine,
    ):
        if value == 1:
            polygons.append(shape(geom))

    if not polygons:
        raise RuntimeError("No catchment polygon could be created from the delineation result.")

    catchment_gdf = gpd.GeoDataFrame(
        geometry=polygons,
        crs=grid.crs,
    )

    catchment_gdf = catchment_gdf.dissolve().explode(index_parts=False).reset_index(drop=True)

    if len(catchment_gdf) > 1:
        areas = catchment_gdf.to_crs(catchment_gdf.estimate_utm_crs()).area
        catchment_gdf = catchment_gdf.loc[[areas.idxmax()]].reset_index(drop=True)

    catchment_gdf.to_file(catchment_filename, driver="GeoJSON")
    print(f"Local catchment delineation saved to: {catchment_filename}")

    info = {
        "dem_filename": str(dem_filename),
        "catchment_filename": str(catchment_filename),
        "snapped_lon": float(x_snap),
        "snapped_lat": float(y_snap),
        "bbox_used": bbox_used,
        "edge_touched": edge_touched,
    }

    return catchment_gdf, info
    

def get_geopotential_webservice(
    catchment,
    config_path=None,
    asset_id=None,
    band=None,
    show_progress=True,
):
    """
    Request catchment-mean geopotential and reference elevation from the
    MATILDA webservice.

    Parameters
    ----------
    catchment : dict or geopandas.GeoDataFrame or shapely geometry
        Catchment geometry as a GeoJSON FeatureCollection, GeoDataFrame,
        or shapely geometry. If a GeoDataFrame or shapely geometry is
        provided, it will be converted to a FeatureCollection payload.
    config_path : str or Path, optional
        Optional path to webservices.ini.
    asset_id : str, optional
        Optional override of the geopotential Earth Engine asset.
    band : str, optional
        Optional override of the band name.
    show_progress : bool, optional
        If True, show a simple live status message while the request runs.

    Returns
    -------
    dict
        Dictionary with keys:
        - "geopotential_mean"
        - "elevation_m"

    Raises
    ------
    RuntimeError
        If the webservice request fails or returns malformed output.
    """

    try:
        from IPython.display import clear_output
        in_notebook = True
    except Exception:
        in_notebook = False

    cfg = load_webservice_config(config_path=config_path, section="GOOGLE")
    service_url = f"{cfg['BASE_URL'].rstrip('/')}/geopotential"

    if hasattr(catchment, "to_json"):
        catchment = json.loads(catchment.to_json())
    elif hasattr(catchment, "__geo_interface__") and not isinstance(catchment, dict):
        catchment = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": catchment.__geo_interface__,
                }
            ],
        }

    if not isinstance(catchment, dict):
        raise ValueError(
            "catchment must be a GeoJSON dict, a GeoDataFrame, or a shapely geometry."
        )

    payload = {"catchment": catchment}

    if asset_id is not None:
        payload["asset_id"] = asset_id
    if band is not None:
        payload["band"] = band

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": cfg["PUBLIC_API_KEY"],
    }

    stop_flag = False
    start_time = time.time()

    def progress_worker():
        symbols = ["⏳", "⌛"]
        i = 0
        while not stop_flag:
            elapsed = time.time() - start_time
            msg1 = f"{symbols[i % 2]} Requesting reference elevation from the MATILDA web service..."
            msg2 = f"Elapsed time: {elapsed:,.1f} s"

            if in_notebook:
                clear_output(wait=True)
                print(msg1)
                print(msg2)
            else:
                print(msg1, msg2)

            time.sleep(1)
            i += 1

    thread = None
    if show_progress:
        thread = threading.Thread(target=progress_worker, daemon=True)
        thread.start()

    try:
        response = requests.post(
            service_url,
            json=payload,
            headers=headers,
            timeout=cfg["TIMEOUT"],
        )
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to reach geopotential webservice: {e}") from e
    finally:
        stop_flag = True
        if thread is not None:
            thread.join()

    elapsed_total = time.time() - start_time

    if not response.ok:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(
            f"Geopotential webservice request failed with status {response.status_code}: {detail}"
        )

    try:
        data = response.json()
    except Exception as e:
        raise RuntimeError(f"Geopotential webservice did not return valid JSON: {e}") from e

    required = {"geopotential_mean", "elevation_m"}
    missing = required.difference(data.keys())
    if missing:
        raise RuntimeError(
            f"Geopotential webservice response is missing keys: {sorted(missing)}"
        )

    if in_notebook and show_progress:
        clear_output(wait=True)

    print("✅ Reference elevation successfully retrieved.")
    print(f"Geopotential mean:\t{data['geopotential_mean']:.2f} m2 s-2")
    print(f"Reference elevation:\t{data['elevation_m']:.2f} m a.s.l.")
    print(f"Elapsed time:\t\t{elapsed_total:,.1f} s")

    return data


def get_climate_data_webservice(
    catchment,
    date_range,
    config_path=None,
    show_progress=True,
    max_concurrent=6,
):
    """
    Request spatially aggregated ERA5-Land forcing data from the MATILDA
    webservice and return them as a pandas DataFrame.

    The webservice streams one JSON record per year (NDJSON).
    """
    import json
    import time
    import pandas as pd
    import requests

    try:
        from IPython.display import clear_output
        in_notebook = True
    except Exception:
        in_notebook = False

    cfg = load_webservice_config(config_path=config_path, section="GOOGLE")
    service_url = f"{cfg['BASE_URL'].rstrip('/')}/climate-data"

    if hasattr(catchment, "to_json"):
        catchment = json.loads(catchment.to_json())
    elif hasattr(catchment, "__geo_interface__") and not isinstance(catchment, dict):
        catchment = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": catchment.__geo_interface__,
                }
            ],
        }

    if not isinstance(catchment, dict):
        raise ValueError(
            "catchment must be a GeoJSON dict, a GeoDataFrame, or a shapely geometry."
        )

    if not isinstance(date_range, (list, tuple)) or len(date_range) != 2:
        raise ValueError("date_range must be a list or tuple: [start_date, end_date]")

    start_year = int(str(date_range[0])[:4])
    end_year = int(str(date_range[1])[:4])
    total_years = end_year - start_year + 1

    payload = {
        "catchment": catchment,
        "date_range": [str(date_range[0]), str(date_range[1])],
        "max_concurrent": int(max_concurrent),
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": cfg["PUBLIC_API_KEY"],
    }

    start_time = time.time()
    year_results = []
    finished = 0

    try:
        response = requests.post(
            service_url,
            json=payload,
            headers=headers,
            timeout=cfg["TIMEOUT"],
            stream=True,
        )
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to reach climate-data webservice: {e}") from e

    if not response.ok:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(
            f"Climate-data webservice request failed with status {response.status_code}: {detail}"
        )

    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue

        try:
            item = json.loads(line)
        except Exception as e:
            raise RuntimeError(f"Could not parse streamed climate-data response: {e}") from e

        if "error" in item:
            raise RuntimeError(
                f"Climate-data webservice failed for year {item.get('year')}: {item['error']}"
            )

        year_results.append(item)
        finished += 1

        if show_progress:
            elapsed = time.time() - start_time
            if in_notebook:
                clear_output(wait=True)
            print("⏳ Requesting ERA5-Land forcing data from the MATILDA web service...")
            print(f"Years completed: {finished}/{total_years}")
            print(f"Latest year received: {item.get('year')}")
            print(f"Elapsed time: {elapsed:,.1f} s")

    if not year_results:
        raise RuntimeError("Climate-data webservice returned no data.")

    year_results = sorted(year_results, key=lambda x: x["year"])

    timestamps = []
    temp = []
    prec = []

    for item in year_results:
        timestamps.extend(item["timestamps"])
        temp.extend(item["temp"])
        prec.extend(item["prec"])

    df = pd.DataFrame({
        "ts": timestamps,
        "temp": temp,
        "prec": prec,
    })

    df = df.drop_duplicates(subset="ts").sort_values("ts").reset_index(drop=True)
    df["dt"] = pd.to_datetime(df["ts"], unit="ms")
    df["temp_c"] = df["temp"] - 273.15
    df["prec"] = df["prec"] * 1000

    elapsed_total = time.time() - start_time

    if in_notebook and show_progress:
        clear_output(wait=True)

    print("✅ ERA5-Land forcing data successfully retrieved.")
    print(f"Date range: {df['dt'].min().date()} to {df['dt'].max().date()}")
    print(f"Number of daily records: {len(df)}")
    print(f"Elapsed time: {elapsed_total:,.1f} s")

    return df[["dt", "temp", "temp_c", "prec"]]

    
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


class CMIPDownloaderWebservice:
    """
    Download spatially averaged CMIP6 yearly CSV files from the MATILDA webservice.

    This class mirrors the output of the local CMIPDownloader, but uses the
    /cmip6-data endpoint. It is designed as a low-disruption bridge so that
    CMIPProcessor can remain unchanged.

    Parameters
    ----------
    starty : int
        First year to request.
    endy : int
        Last year to request.
    catchment : dict or geopandas.GeoDataFrame or shapely geometry
        Catchment geometry to send to the webservice.
    variables : list of str, optional
        Variables to request. Default is ["tas", "pr"].
    dir : str, optional
        Output directory for yearly CSV files.
    max_concurrent : int, optional
        Concurrency passed to the webservice endpoint.
    block_size_years : int or None, optional
        If given, split each variable request into year blocks of this size.
        If None, request each variable over the full time period.
    config_path : str or Path, optional
        Optional path to webservices.ini.
    show_progress : bool, optional
        Whether to print progress information.
    """

    def __init__(
        self,
        starty,
        endy,
        catchment,
        variables=None,
        dir="./",
        max_concurrent=6,
        block_size_years=None,
        config_path=None,
        show_progress=True,
    ):
        self.starty = int(starty)
        self.endy = int(endy)
        self.catchment = catchment
        self.variables = variables or ["tas", "pr"]
        self.directory = dir
        self.max_concurrent = int(max_concurrent)
        self.block_size_years = block_size_years
        self.config_path = config_path
        self.show_progress = show_progress

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

    def _normalize_catchment(self):
        catchment = self.catchment

        if hasattr(catchment, "to_json"):
            catchment = json.loads(catchment.to_json())
        elif hasattr(catchment, "__geo_interface__") and not isinstance(catchment, dict):
            catchment = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": catchment.__geo_interface__,
                    }
                ],
            }

        if not isinstance(catchment, dict):
            raise ValueError(
                "catchment must be a GeoJSON dict, a GeoDataFrame, or a shapely geometry."
            )

        return catchment

    def _iter_blocks(self):
        if self.block_size_years is None:
            yield self.starty, self.endy
            return

        y = self.starty
        while y <= self.endy:
            block_end = min(y + self.block_size_years - 1, self.endy)
            yield y, block_end
            y = block_end + 1

    def _request_block(self, variable, block_start, block_end, pbar=None):
        cfg = load_webservice_config(config_path=self.config_path, section="GOOGLE")
        service_url = f"{cfg['BASE_URL'].rstrip('/')}/cmip6-data"

        payload = {
            "catchment": self._normalize_catchment(),
            "date_range": [f"{block_start}-01-01", f"{block_end}-12-31"],
            "variables": [variable],
            "max_concurrent": self.max_concurrent,
        }

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": cfg["PUBLIC_API_KEY"],
        }

        try:
            response = requests.post(
                service_url,
                json=payload,
                headers=headers,
                timeout=cfg["TIMEOUT"],
                stream=True,
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to reach cmip6-data webservice: {e}") from e

        if not response.ok:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise RuntimeError(
                f"cmip6-data webservice request failed with status {response.status_code}: {detail}"
            )

        received_years = []

        for raw_line in response.iter_lines(decode_unicode=False):
            if not raw_line:
                continue

            if isinstance(raw_line, bytes):
                line = raw_line.decode("utf-8", errors="replace")
            else:
                line = raw_line

            if not line.strip():
                continue

            try:
                item = json.loads(line)
            except Exception as e:
                raise RuntimeError(f"Could not parse streamed cmip6-data response: {e}") from e

            if "error" in item:
                raise RuntimeError(
                    f"cmip6-data webservice failed for var={item.get('var')} year={item.get('year')}: {item['error']}"
                )

            year = int(item["year"])
            var = item["var"]
            filename = item.get("filename", f"cmip6_{var}_{year}.csv")
            csv_text = item["csv"]

            out_path = os.path.join(self.directory, filename)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(csv_text)

            received_years.append(year)

            if pbar is not None:
                pbar.update(1)
                pbar.set_postfix_str(f"variable={var}, year={year}")

        return sorted(received_years)

    def download(self):
        """
        Download all requested variables and save yearly CSV files locally.

        Returns
        -------
        dict
            Summary of downloaded years by variable.
        """
        summary = {}
        t0 = time.time()

        total_expected = (self.endy - self.starty + 1) * len(self.variables)

        pbar = tqdm(
            total=total_expected,
            desc="Downloading CMIP6 yearly files",
            unit="file",
            disable=not self.show_progress,
        )

        try:
            for variable in self.variables:
                if self.show_progress:
                    pbar.set_postfix_str(f"variable={variable}")

                variable_years = []

                for block_start, block_end in self._iter_blocks():
                    years = self._request_block(variable, block_start, block_end, pbar=pbar)
                    variable_years.extend(years)

                variable_years = sorted(set(variable_years))
                summary[variable] = variable_years

                expected = list(range(self.starty, self.endy + 1))
                missing = sorted(set(expected) - set(variable_years))

                if self.show_progress and missing:
                    print(f"Missing years for {variable}: {missing[:10]}{' ...' if len(missing) > 10 else ''}")

        finally:
            pbar.close()

        elapsed = time.time() - t0

        if self.show_progress:
            print(f"CMIP6 webservice download complete in {elapsed:,.1f} s.")

        return


class CMIPDownloaderManifest:
    """
    Fast CMIP6 downloader using the /cmip6-manifest endpoint.

    The MATILDA webservice generates signed Earth Engine download URLs.
    This helper downloads those files directly in parallel and saves them
    with the same filenames expected by CMIPProcessor.
    """

    def __init__(
        self,
        starty,
        endy,
        catchment,
        variables=None,
        dir="./",
        manifest_concurrent=6,
        download_workers=10,
        block_size_years=None,
        config_path=None,
        show_progress=True,
    ):
        self.starty = int(starty)
        self.endy = int(endy)
        self.catchment = catchment
        self.variables = variables or ["tas", "pr"]
        self.directory = dir
        self.manifest_concurrent = int(manifest_concurrent)
        self.download_workers = int(download_workers)
        self.block_size_years = block_size_years
        self.config_path = config_path
        self.show_progress = show_progress

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

    def _normalize_catchment(self):
        catchment = self.catchment

        if hasattr(catchment, "to_json"):
            catchment = json.loads(catchment.to_json())
        elif hasattr(catchment, "__geo_interface__") and not isinstance(catchment, dict):
            catchment = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": catchment.__geo_interface__,
                    }
                ],
            }

        if not isinstance(catchment, dict):
            raise ValueError(
                "catchment must be a GeoJSON dict, a GeoDataFrame, or a shapely geometry."
            )

        return catchment

    def _iter_blocks(self):
        if self.block_size_years is None:
            yield self.starty, self.endy
            return

        y = self.starty
        while y <= self.endy:
            block_end = min(y + self.block_size_years - 1, self.endy)
            yield y, block_end
            y = block_end + 1

    def _fetch_manifest_block(self, variable, block_start, block_end):
        cfg = load_webservice_config(config_path=self.config_path, section="GOOGLE")
        service_url = f"{cfg['BASE_URL'].rstrip('/')}/cmip6-manifest"

        payload = {
            "catchment": self._normalize_catchment(),
            "date_range": [f"{block_start}-01-01", f"{block_end}-12-31"],
            "variables": [variable],
            "max_concurrent": self.manifest_concurrent,
        }

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": cfg["PUBLIC_API_KEY"],
        }

        try:
            response = requests.post(
                service_url,
                json=payload,
                headers=headers,
                timeout=cfg["TIMEOUT"],
                stream=True,
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to reach cmip6-manifest webservice: {e}") from e

        if not response.ok:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise RuntimeError(
                f"cmip6-manifest request failed with status {response.status_code}: {detail}"
            )

        entries = []
        for raw_line in response.iter_lines(decode_unicode=False):
            if not raw_line:
                continue

            line = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else raw_line
            if not line.strip():
                continue

            try:
                item = json.loads(line)
            except Exception as e:
                raise RuntimeError(f"Could not parse streamed cmip6-manifest response: {e}") from e

            if "error" in item:
                raise RuntimeError(
                    f"cmip6-manifest failed for var={item.get('var')} year={item.get('year')}: {item['error']}"
                )

            entries.append(item)

        return entries

    def _download_one(self, item):
        filename = item["filename"]
        url = item["download_url"]
        out_path = os.path.join(self.directory, filename)

        response = requests.get(url, timeout=300)
        response.raise_for_status()

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        return {
            "filename": filename,
            "year": int(item["year"]),
            "var": item["var"],
            "path": out_path,
        }

    def download(self):
        summary = {}
        t0 = time.time()

        manifest_entries = []
        for variable in self.variables:
            if self.show_progress:
                print(f"Fetching manifest for '{variable}'...")

            variable_entries = []
            for block_start, block_end in self._iter_blocks():
                variable_entries.extend(
                    self._fetch_manifest_block(variable, block_start, block_end)
                )

            manifest_entries.extend(variable_entries)

        if self.show_progress:
            print(f"Received {len(manifest_entries)} manifest entries.")

        total_expected = (self.endy - self.starty + 1) * len(self.variables)
        pbar = tqdm(
            total=total_expected,
            desc="Downloading CMIP6 yearly files",
            unit="file",
            disable=not self.show_progress,
        )

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.download_workers) as executor:
                futures = [executor.submit(self._download_one, item) for item in manifest_entries]

                downloaded = []
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    downloaded.append(result)
                    pbar.update(1)
                    pbar.set_postfix_str(f"variable={result['var']}, year={result['year']}")

        finally:
            pbar.close()

        for variable in self.variables:
            years = sorted(
                {item["year"] for item in downloaded if item["var"] == variable}
            )
            summary[variable] = years

            expected = list(range(self.starty, self.endy + 1))
            missing = sorted(set(expected) - set(years))

            if self.show_progress and missing:
                print(f"Missing years for {variable}: {missing[:10]}{' ...' if len(missing) > 10 else ''}")

        elapsed = time.time() - t0
        if self.show_progress:
            print(f"CMIP6 manifest download complete in {elapsed:,.1f} s.")

        return summary


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

