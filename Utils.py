from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm, Normalize
import geopandas as gpd
import pandas as pd
import scipy

import openmeteo_requests
import requests_cache
from retry_requests import retry

from pyproj import Transformer
from shapely.geometry import Point, Polygon, box
from shapely.geometry import mapping
import numpy as np
import math
import os
import rasterio as rio
from rasterio.mask import mask
from rasterio.warp import reproject, Resampling, transform ,  calculate_default_transform
from rasterio.transform import from_bounds
#from mgrs import MGRS
from rasterio.windows import Window
from typing import Optional

import matplotlib.pyplot as plt
import  datetime as _dt
from datetime import datetime, timedelta
import Constants
import requests
#import inspect



try:
    import inspect
except:
    print("failed to import inspect")
    pass

import geopandas as gpd

# Load once at module level
#S2_GRID = gpd.read_file("Sentinel-2-tiling-grid.geojson")  # or .shp
S2_GRID = gpd.read_file("sentinel2_tiling_grid_wgs84.geojson") 



def show_raster_bounds(path):
    with rio.open(path) as ds:
        b = ds.bounds
        print(f"Raster CRS: {ds.crs}")
        print(f"Raster bounds: left={b.left}, bottom={b.bottom}, right={b.right}, top={b.top}")
        # centroid in lon/lat for sanity
        t = Transformer.from_crs(ds.crs, "EPSG:4326", always_xy=True)
        lon, lat = t.transform((b.left+b.right)/2, (b.bottom+b.top)/2)
        print(f"Raster centroid (lon,lat): {lon:.6f}, {lat:.6f}")
        return ds.crs, b


def get_pixel_from_latlon(bounds, lat, lon, shape):
    west, south, east, north = bounds
    height, width = shape
    if not (south <= lat <= north and west <= lon <= east):
        print("out of bounds")
        return None, None
    row = int((north - lat) / ((north - south) / height))
    col = int((lon - west) / ((east - west) / width))
    return row, col


def generate_date_range(start: str, end: str, fmt: str = "%Y-%m-%d", dateStep : int = 5) -> list:
    """
    Generate a list of consecutive date strings from start to end (inclusive).
    
    Args:
        start (str): Start date as 'YYYY-MM-DD'
        end (str): End date as 'YYYY-MM-DD'
        fmt (str): Date format for output (default: '%Y-%m-%d')
        
    Returns:
        List[str]: List of date strings
    """
    start_date = datetime.strptime(start, fmt)
    end_date = datetime.strptime(end, fmt)
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.strftime(fmt))
        current += timedelta(days=dateStep)
    return dates
    


# Deprecated. Tile is hard coded rather than dynamically computed from lat, lon. Also, does not cache downloaded data. Use download_band_dynamic instead
"""
def download_band(date, band):
    y, m, d = date.split("-")

    #base_url = f"https://roda.sentinel-hub.com/tiles/{Constants.tile['utm_zone']}/{Constants.tile['latitude_band']}/{Constants.tile['grid_square']}/{y}/{int(m)}/{int(d)}/0/{band}.jp2"
    base_url = f"https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/{Constants.tile['utm_zone']}/{Constants.tile['latitude_band']}/{Constants.tile['grid_square']}/{y}/{int(m)}/{int(d)}/0/{band}.jp2"
    #base_url = f"https://sentinel-s2-l1c.s3.amazonaws.com/tiles/{tile['utm_zone']}/{tile['latitude_band']}/{tile['grid_square']}/{y}/{int(m)}/{int(d)}/0/{band}.jp2"

    print("base_url = ",base_url )
    filename = f"s2_point_series/{date}_{band}.jp2"
    if not os.path.exists(filename):
        r = requests.get(base_url, stream=True)
        if r.status_code == 200:
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            return None
    return filename if os.path.exists(filename) else None

"""


# New method using Sentinel 2 tiling grid shapefile:
def latlon_to_s2_tile(lat, lon):
    """Return Sentinel-2 MGRS tile ID from official tiling grid."""
    pt = Point(lon, lat)  # shapely Point expects (x=lon, y=lat)
    match = S2_GRID[S2_GRID.contains(pt)]
    if match.empty:
        raise ValueError(f"No Sentinel-2 tile found for {lat},{lon}")
    print(f"[Line {inspect.currentframe().f_lineno}] ... Mapped latitude ", lat,", longitude ",lon," to mgrs_tile = ",match.iloc[0]["Name"])
    return match.iloc[0]["Name"]  # field is "Name" e.g. "14QQG"

def make_path_name(cache_dir, mgrs_tile,date,band,extension):
    # Local cache
    os.makedirs(cache_dir, exist_ok=True)
    print("band = >",band,"<")
    print("extension = >",extension,"<")
    return os.path.join(cache_dir, f"{mgrs_tile}_{date}_{band}.{extension}")

"""
def download_band_dynamic(date, band, lat, lon, cache_dir="s2_point_series"):
    # Parse date
    y, m, d = date.split("-")
    y = int(y)
    m = int(m)
    d = int(d)

    # Convert to MGRS tile
    # new way, using Sentinel 2 tiling grid shapefile:
    mgrs_tile = latlon_to_s2_tile(lat, lon)   # e.g. "14QQG"
    print(f"[Line {inspect.currentframe().f_lineno}] ... lat       = ",lat      )
    print(f"[Line {inspect.currentframe().f_lineno}] ... lon       = ",lon      )
    print(f"[Line {inspect.currentframe().f_lineno}] ... mgrs_tile = ",mgrs_tile)

    utm_zone = mgrs_tile[0:2]       # '14'
    latitude_band = mgrs_tile[2]    # 'Q'
    grid_square = mgrs_tile[3:5]    # 'KH'

    # Construct RODA URL
    base_url = (
    #https://sentinel-s2-l1c.s3.amazonaws.com/tiles
    #/14/Q/QG/2025/7/28/0/B11.jp2
        f"https://sentinel-s2-l1c.s3.amazonaws.com/tiles/"     
        f"{utm_zone}/{latitude_band}/{grid_square}/{y}/{m}/{d}/0/{band}.jp2"
        #f"https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/"
        #f"{utm_zone}/{latitude_band}/{grid_square}/{y}/{m}/{d}/0/{band}.jp2"
    )
    print("base_url = ", base_url)

    filename = make_path_name(cache_dir, mgrs_tile,date,band,"jp2"   ) # os.path.join(cache_dir, f"{mgrs_tile}_{date}_{band}.jp2")

    # Download if not cached
    if not os.path.exists(filename):
        print(f"[Line {inspect.currentframe().f_lineno}] ... Downloading, because did not find a cached file: ",filename)
        r = requests.get(base_url, stream=True)
        if r.status_code == 200:
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:  
            print(f"[Line {inspect.currentframe().f_lineno}] ...  ")
            print(f"Failed to download {band} on {date} from {mgrs_tile} (HTTP {r.status_code})")
            return None
    else:
        print(f"[Line {inspect.currentframe().f_lineno}] ... Using cached file: ",filename)
    return filename if os.path.exists(filename) else None
"""


# You already have this:
# from your_utils import latlon_to_s2_tile

def download_band_dynamic(date: str, band: str, lat: float, lon: float,
                          cache_dir: str = "s2_point_series",
                          level: Optional[str] = None) -> Optional[str]:
    """
    Download a Sentinel-2 asset for a given date/tile:
      - L1C bands (default): .../0/B11.jp2
      - L1C QA60:            .../0/QA60.jp2
      - L2A SCL (auto):      .../R20m/SCL_20m.jp2
      - L2A bands (if level='L2A'): .../R10m/B04_10m.jp2, .../R20m/B11_20m.jp2

    Args:
        date: 'YYYY-MM-DD'
        band: e.g. 'B08', 'B11', 'QA60', 'SCL' (or 'SCL_20m')
        lat, lon: point inside desired tile
        cache_dir: where to save
        level: 'L1C', 'L2A', or None to auto (SCL→L2A, QA60→L1C, others→L1C)

    Returns:
        Local filename, or None on failure.
    """
    # Parse date
    y, m, d = (int(x) for x in date.split("-"))

    # Tile lookup (e.g., '14QQG')
    mgrs_tile = latlon_to_s2_tile(lat, lon)
    utm_zone  = mgrs_tile[0:2]
    lat_band  = mgrs_tile[2]
    grid_sq   = mgrs_tile[3:5]

    band_u = band.upper()

    # Decide product level if not set
    if level is None:
        if band_u.startswith("SCL"):
            level = "L2A"
        elif band_u == "QA60":
            level = "L1C"
        else:
            level = "L1C"  # keep your original default
    level = level.upper()

    # Build URL path according to level/band
    urls_to_try = []
    if level == "L1C":
        bucket = "https://sentinel-s2-l1c.s3.amazonaws.com/tiles"
        # filenames are like B08.jp2, B11.jp2, QA60.jp2
        fname = f"{band_u}.jp2"
        for seq in (0, 1):
            url = f"{bucket}/{utm_zone}/{lat_band}/{grid_sq}/{y}/{m}/{d}/{seq}/{fname}"
            urls_to_try.append(url)

        band_tag = band_u  # for local filename

    elif level == "L2A":
        bucket = "https://sentinel-s2-l2a.s3.amazonaws.com/tiles"
        # resolution subfolder + filename differ by band
        print(f"[Line {inspect.currentframe().f_lineno}] ...       ")
        if band_u.startswith("SCL"):
            print(f"[Line {inspect.currentframe().f_lineno}] ...       ")
            sub = "R20m"
            fname = "SCL_20m.jp2"
            band_tag = "SCL_20m"
        else:
            # map band -> native resolution (10m/20m)
            res_map = {
                "B02":"10m","B03":"10m","B04":"10m","B08":"10m",
                "B05":"20m","B06":"20m","B07":"20m","B8A":"20m",
                "B11":"20m","B12":"20m"
            }
            if band_u not in res_map:
                raise ValueError(f"Unsupported L2A band: {band_u}")
            res = res_map[band_u]
            sub = f"R{res}"
            fname = f"{band_u}_{res}.jp2"
            band_tag = f"{band_u}_{res}"

        for seq in (0, 1):
            url = f"{bucket}/{utm_zone}/{lat_band}/{grid_sq}/{y}/{m}/{d}/{seq}/{sub}/{fname}"
            urls_to_try.append(url)
    else:
        raise ValueError(f"level must be 'L1C', 'L2A', or None; got {level!r}")

    # Local cache filename
    os.makedirs(cache_dir, exist_ok=True)
    filename = os.path.join(cache_dir, f"{mgrs_tile}_{date}_{band_tag}.jp2")

    if os.path.exists(filename):
        return filename

    # Try URLs (sequence 0 then 1)
    for url in urls_to_try:
        print (" trying url : ",url)
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filename
    if level == "L2A" and band_u.startswith("SCL"):
        print(f"[Line {inspect.currentframe().f_lineno}] ...       ")
        token = os.getenv("ACCESS_TOKEN") or os.getenv("CDSE_ACCESS_TOKEN")
        if token:
            ok = _download_scl_from_cdse(date, mgrs_tile, filename, token, scl_res="R20m")
            print(f"[Line {inspect.currentframe().f_lineno}] ...  date  =  ",date    )
            print(f"[Line {inspect.currentframe().f_lineno}] ...mgrs_tile  ",mgrs_tile)
            print(f"[Line {inspect.currentframe().f_lineno}] ...filename=  ",filename)
            print(f"[Line {inspect.currentframe().f_lineno}] ...token   =  ",token   )
            print(f"[Line {inspect.currentframe().f_lineno}] ...     ok =  ",ok)
            if ok:
                print(f"[Line {inspect.currentframe().f_lineno}] ...       ")
                return filename
        else :
            print(f"[Line {inspect.currentframe().f_lineno}] ...       ")
    # If we get here, all attempts failed
    print(f"[Line {inspect.currentframe().f_lineno}] ...       ")
    print(f"Failed to download {band_tag} on {date} for tile {mgrs_tile}. "
          f"Tried: {urls_to_try[0]} (and sequence fallback).")
    return None

# --- add imports if not already present ---

import os, io, re, shutil, zipfile, requests, datetime as _dt
from urllib.parse import quote as _q

_CDSE_CAT = "https://catalogue.dataspace.copernicus.eu/odata/v1"   # search + Nodes (+ $value; follows redirects)

def _nodes_list(j: dict):
    # CDSE may return arrays under "value" (often) or "result" (sometimes)
    return j.get("value") or j.get("result") or []

def _k(s: str) -> str:  # quote for Nodes('...') segments
    return f"%27{_q(s, safe='')}%27"

def _download_scl_from_cdse(date_str: str, mgrs_tile: str, out_path: str,
                            token: str, scl_res: str = "R20m") -> bool:
    """
    Robust SCL fetcher:
      - Node-listing via catalogue host (handles redirects)
      - Fallback: download whole SAFE ($value) and extract SCL_<res>.jp2
    Writes the SCL to out_path; returns True on success, else False.
    """
    # Build [start, end) window
    y, m, d = (int(x) for x in date_str.split("-"))
    start = f"{date_str}T00:00:00.000Z"
    end   = (_dt.date(y, m, d) + _dt.timedelta(days=1)).strftime("%Y-%m-%d") + "T00:00:00.000Z"

    tile = mgrs_tile if mgrs_tile.startswith("T") else ("T" + mgrs_tile)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # 1) Find candidate L2A products for this tile/day
    filt = (
        "Collection/Name eq 'SENTINEL-2' and "
        "Attributes/OData.CSC.StringAttribute/any("
        "att: att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'S2MSI2A') and "
        f"contains(Name,'{tile}') and "
        f"ContentDate/Start ge {start} and ContentDate/Start lt {end}"
    )
    params = {"$format": "json", "$select": "Id,Name,Online,ContentDate", "$orderby": "ContentDate/Start asc",
              "$top": "5", "$filter": filt}
    r = requests.get(f"{_CDSE_CAT}/Products", params=params, headers=headers, timeout=60)
    r.raise_for_status()
    items = r.json().get("value", [])
    if not items:
        return False

    scl_file = f"SCL_{scl_res[1:]}.jp2"  # R20m -> SCL_20m.jp2

    # 2) Try the light path first: list Nodes via catalogue host and download only SCL
    for prod in items:
        print(f"[Line {inspect.currentframe().f_lineno}] ...     prod =",prod)
        pid  = prod["Id"]
        print(f"[Line {inspect.currentframe().f_lineno}] ...     pid      =  ",pid     )
        safe = prod["Name"]  # we already know the SAFE name; no need to list root
        # new test
        print(f"[Line {inspect.currentframe().f_lineno}] ...      "     )
        test = requests.get(
            f"{_CDSE_CAT}/Products({pid})/$value",
            headers={"Authorization": headers["Authorization"]},
            stream=True, allow_redirects=True, timeout=300
        )
        print("archive $value:", test.status_code, test.headers.get("Content-Type"))

    # GRANULE list
    try:
        gran = requests.get(
            f"{_CDSE_CAT}/Products({pid})/Nodes({_k(safe)})/Nodes('GRANULE')/Nodes",
            params={"$format": "json"}, headers=headers, timeout=60
        )
        print(f"[Line {inspect.currentframe().f_lineno}] ... gran         ",gran     )
        if gran.status_code in (401, 403):
            print(f"[Line {inspect.currentframe().f_lineno}] ...          "     )
            raise PermissionError(f"granules auth {gran.status_code}")  # -> fallback
        if gran.status_code != 200:
            print(f"[Line {inspect.currentframe().f_lineno}] ...          "     )
            raise RuntimeError(f"granules status {gran.status_code}")
        granules = _nodes_list(gran.json())
    except Exception:
        print(f"[Line {inspect.currentframe().f_lineno}] ...          "     )
        granules = []  # this triggers the archive fallback later

        if granules:
            print(f"[Line {inspect.currentframe().f_lineno}] ...     granules =  ",granules)
            for g in (x["Name"] for x in granules):
                print(f"[Line {inspect.currentframe().f_lineno}] ...   ")
                # List IMG_DATA/<res> for SCL
                try:
                    print(f"[Line {inspect.currentframe().f_lineno}] ...   ")
                    lst = requests.get(
                        f"{_CDSE_CAT}/Products({pid})/Nodes({_k(safe)})/Nodes('GRANULE')/Nodes({_k(g)})"
                        f"/Nodes('IMG_DATA')/Nodes('{scl_res}')/Nodes",
                        params={"$format": "json"}, headers=headers, timeout=60
                    )
                    if lst.status_code != 200:
                        continue
                    names = {x["Name"] for x in _nodes_list(lst.json())}
                except Exception:
                    names = set()

                if scl_file in names:
                    url = (
                        f"{_CDSE_CAT}/Products({pid})/Nodes({_k(safe)})/Nodes('GRANULE')/Nodes({_k(g)})"
                        f"/Nodes('IMG_DATA')/Nodes('{scl_res}')/Nodes('{scl_file}')/$value"
                    )
                    with requests.get(url, headers=headers, stream=True, timeout=300, allow_redirects=True) as resp:
                        if resp.status_code != 200:
                            continue
                        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
                        with open(out_path, "wb") as f:
                            for chunk in resp.iter_content(8192):
                                if chunk:
                                    f.write(chunk)
                    return True
        # If we couldn’t list nodes or didn’t find SCL, try archive fallback next.

    # 3) Fallback: download whole SAFE as a ZIP and extract SCL_<res>.jp2
    for prod in items:
        pid  = prod["Id"]
        safe = prod["Name"]

        try:
            with requests.get(f"{_CDSE_CAT}/Products({pid})/$value",
                              headers={"Authorization": f"Bearer {token}"},
                              stream=True, timeout=900, allow_redirects=True) as rr:
                rr.raise_for_status()
                tmp_path = out_path + ".zip.part"
                os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
                with open(tmp_path, "wb") as f:
                    for chunk in rr.iter_content(1024 * 1024):
                        if chunk:
                            f.write(chunk)
            final_zip = out_path + ".zip"
            os.replace(tmp_path, final_zip)
        except Exception:
            # next candidate product
            continue

        try:
            if not zipfile.is_zipfile(final_zip):
                continue
            pattern = re.compile(
                r".+/GRANULE/([^/]+)/IMG_DATA/" + re.escape(scl_res) + r"/" + re.escape(scl_file) + r"$"
            )
            members = []
            with zipfile.ZipFile(final_zip) as z:
                # prefer granules whose name includes the tile code
                for nm in z.namelist():
                    if pattern.match(nm):
                        members.append(nm)
                # choose first; prefer match containing tile code
                pick = None
                for m in members:
                    if tile in m:
                        pick = m; break
                if not pick and members:
                    pick = members[0]
                if not pick:
                    continue
                with z.open(pick) as src, open(out_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            return True
        finally:
            # clean up the big ZIP to save space
            try: os.remove(final_zip)
            except OSError: pass

    return False

def grid_to_xy(c, r, x0, y0, dx, dy, rotation_deg):
    dx_i = c * dx
    dy_i = r * dy
    theta = math.radians(rotation_deg)
    cos_theta, sin_theta = math.cos(theta), math.sin(theta)
    x = x0 + dx_i * cos_theta - dy_i * sin_theta
    y = y0 + dx_i * sin_theta + dy_i * cos_theta
    return x, y

def draw_grid_box(lat0, lon0, dx, dy, n_cols, n_rows, rotation_deg,
                  col1, row1, col2, row2):
    """
    Draw a rotated rectangular box aligned to a tree grid.

    Args:
        lat0, lon0 (float): Origin of the grid (top-left corner).
        dx, dy (float): Spacing between columns and rows (in meters).
        n_cols, n_rows (int): Grid dimensions (not used directly here, for consistency).
        rotation_deg (float): Clockwise rotation from true north (degrees).
        col1, row1, col2, row2 (int): Grid indices defining opposite corners of the box.

    Returns:
        GeoDataFrame: A single Polygon geometry in EPSG:4326
    """
    # Convert origin to meters
    origin = Point(lon0, lat0)
    gdf_origin = gpd.GeoDataFrame(geometry=[origin], crs="EPSG:4326").to_crs(epsg=3857)
    x0, y0 = gdf_origin.geometry[0].x, gdf_origin.geometry[0].y
    print("x0 = ",x0)
    print("y0 = ",y0)

    theta = math.radians(rotation_deg)
    cos_theta, sin_theta = math.cos(theta), math.sin(theta)

    print("draw_grid_box : dx = ", dx)
    print("draw_grid_box : dy = ", dy)

    # Box corners in order (clockwise)
    x1, y1 = grid_to_xy(col1, row1, x0, y0, dx, dy, rotation_deg)
    x2, y2 = grid_to_xy(col2, row1, x0, y0, dx, dy, rotation_deg)
    x3, y3 = grid_to_xy(col2, row2, x0, y0, dx, dy, rotation_deg)
    x4, y4 = grid_to_xy(col1, row2, x0, y0, dx, dy, rotation_deg)
    #print ("x1,y1 etc")
    #print (x1,y1)
    #print (x2,y2)
    #print (x3,y3)
    #print (x4,y4)

    poly = Polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4), (x1, y1)])


    # Compute center in projected CRS
    center_proj = poly.centroid

    # Convert center to lat/lon
    gdf_center = gpd.GeoDataFrame(geometry=[center_proj], crs="EPSG:3857").to_crs("EPSG:4326")
    center_lon, center_lat = gdf_center.geometry[0].x, gdf_center.geometry[0].y
    print(f"📍 Center of box: ({center_lat:.6f}, {center_lon:.6f})")
    
    gdf_box = gpd.GeoDataFrame(geometry=[poly], crs="EPSG:3857").to_crs("EPSG:4326")
    return gdf_box





def generate_tree_circles(
    lat0, lon0, 
    n_cols, n_rows, 
    dx, dy, 
    rotation_deg, 
    radius=0.5,
    #return_crs="EPSG:4326" # Cartesian
    return_crs="EPSG:4326" # Cartesian
):
    """
    Generate a rotated grid of tree circles (polygons), each 1m in diameter by default.

    Args:
        lat0 (float): Latitude of the top-left tree.
        lon0 (float): Longitude of the top-left tree.
        n_cols (int): Number of columns of trees.
        n_rows (int): Number of rows of trees.
        dx (float): Distance between columns (meters).
        dy (float): Distance between rows (meters).
        rotation_deg (float): Clockwise rotation from true north (in degrees).
        radius (float): Circle radius in meters (default is 0.5 m → 1 m diameter).
        return_crs (str): CRS to return GeoDataFrame in (default: "EPSG:4326")

    Returns:
        GeoDataFrame: Circular tree geometries in specified CRS.
    """
    # Step 1: Convert origin to Web Mercator (meters)
    origin = Point(lon0, lat0)
    gdf_origin = gpd.GeoDataFrame(geometry=[origin], crs="EPSG:4326").to_crs(epsg=3857) # convert to Web Mercator. 
    x0, y0 = gdf_origin.geometry[0].x, gdf_origin.geometry[0].y

    # Step 2: Set up rotation
    theta = math.radians(rotation_deg)
    cos_theta, sin_theta = math.cos(theta), math.sin(theta)

    # Step 3: Generate circles
    circle_geoms = []
    for row in range(n_rows):
        for col in range(n_cols):
            dx_i = col * dx
            dy_i = row * dy

            x = x0 + dx_i * cos_theta - dy_i * sin_theta
            y = y0 + dx_i * sin_theta + dy_i * cos_theta

            circle = Point(x, y).buffer(radius)  # buffer in meters
            circle_geoms.append(circle)

    # Step 4: Return GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=circle_geoms, crs="EPSG:3857") # convert to Web Mercator. 
    return gdf.to_crs(return_crs)



# ndmi_path is the entire tile, which you prepared earlier in the program.
# plot_gdf is a GeoDataFrame.. contains the polygon to be used for cropping
# save_path is the filename to which the NDMI tif will be saved.
def crop_and_plot_ndmi(ndmi_path, plot_gdf, title="NDMI Cropped", show_plot=True, save_path=None):
    """
    Crop an NDMI raster to a polygon, plot it, and optionally save as GeoTIFF with georeferencing.
    """
    with rio.open(ndmi_path) as src:
        out_image, out_transform = mask(src, plot_gdf.geometry, crop=True)
        out_meta = src.meta.copy()

    ndmi_crop = out_image[0].astype("float32")
    ndmi_crop[ndmi_crop == src.nodata] = np.nan

    if show_plot:
        vmin = np.nanpercentile(ndmi_crop, 2)
        vmax = np.nanpercentile(ndmi_crop, 98)
        plt.figure(figsize=(6, 6))
        plt.imshow(ndmi_crop, cmap='BrBG', vmin=vmin, vmax=vmax)
        plt.colorbar(label="NDMI")
        plt.title(title)
        plt.axis('off')
        plt.tight_layout()
        plt.show()

    if save_path is not None:
        out_meta.update({
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "crs": src.crs,  # <-- This is the fix
            "driver": "GTiff",
            "dtype": "float32",
            "count": 1
        })
        print("Saving with CRS:", src.crs)

        with rio.open(save_path, "w", **out_meta) as dst:
            dst.write(ndmi_crop, 1)
    #show_tif_fit(save_path, scale=12, cmap="gray")
    return ndmi_crop, out_transform, out_meta



def reproject_UTM_to_3857(infile, outfile):
    with rio.open(infile) as src:
        dst_crs = "EPSG:3857"
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update({
            "crs": dst_crs,
            "transform": transform,
            "width": width,
            "height": height
        })

        with rio.open(outfile, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rio.band(src, i),
                    destination=rio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.bilinear
                )
    return outfile

def transform_from_jp2(jp2_file):
    """Return the Affine transform of the JP2 (use directly in transform=)."""
    with rio.open(jp2_file) as src:
        return src.transform  # Affine

def write_gndvi_geotiff(b08_path: str, b03_path: str, out_path: str) -> None: #b03 was b11
    """
    Create an GNDVI GeoTIFF from Sentinel-2 B08 (10 m) and B03.         
    - Resamples B11 onto B08's grid
    - Computes NDMI = (B08 - B11) / (B08 + B11)
    - Writes a single-band float32 GeoTIFF with B08's CRS/transform/bounds
    - Nodata is NaN
    """
    print(f"[Line {inspect.currentframe().f_lineno}] ... ")

    with rio.open(b08_path) as b8, rio.open(b03_path) as b3 :
        if b8.crs is None or b3.crs is None:
            raise ValueError("Input JP2 missing CRS")
        # Read reference band (B08)
        nir = b8.read(1).astype("float32")
        green=b3.read(1).astype("float32")

        # Convert to reflectance (S2 DN -> reflectance ~ /10000)
        nir  = nir  / 10000.0
        green= green/ 10000.0

        # Valid mask (ignore zeros/negatives)
        valid = (nir > 0) & (green> 0)

        # NDMI
        #ndmi = np.full_like(nir, np.nan, dtype="float32")
        gndvi= np.full_like(nir, np.nan, dtype="float32")
        denom = nir + green
        #ndmi[valid] = (nir[valid] - swir[valid]) / np.maximum(denom[valid], 1e-6)
        gndvi[valid]  = (nir[valid] - green[valid]) / (nir[valid] + green[valid])

        # Write GeoTIFF using B08 georeferencing
        profile = b8.profile.copy()
        profile.update(
            driver="GTiff",
            dtype="float32",
            count=1,
            nodata=np.float32(np.nan),
            compress="deflate",
            predictor=2,
            tiled=True,
            blockxsize=256,
            blockysize=256,
        )
        with rio.open(out_path, "w", **profile) as dst:
            dst.write(gndvi, 1)

def write_ndmi_geotiff(b08_path: str, b11_path: str, out_path: str) -> None:
    """
    Create an NDMI GeoTIFF from Sentinel-2 B08 (10 m) and B11 (20 m).
    - Resamples B11 onto B08's grid
    - Computes NDMI = (B08 - B11) / (B08 + B11)
    - Writes a single-band float32 GeoTIFF with B08's CRS/transform/bounds
    - Nodata is NaN
    """
    with rio.open(b08_path) as b8, rio.open(b11_path) as b11:
        if b8.crs is None or b11.crs is None:
            raise ValueError("Input JP2 missing CRS")
        # Read reference band (B08)
        nir = b8.read(1).astype("float32")

        # Resample SWIR (B11) to B08 grid
        swir_on_b8 = np.empty_like(nir, dtype="float32")

        reproject(
            source=b11.read(1).astype("float32"),
            destination=swir_on_b8,
            src_transform=b11.transform, src_crs=b11.crs,
            dst_transform=b8.transform,  dst_crs=b8.crs,   # <- REQUIRED
            dst_width=b8.width, dst_height=b8.height,      # <- recommended
            resampling=Resampling.bilinear,
)

        # Convert to reflectance (S2 DN -> reflectance ~ /10000)
        nir  = nir  / 10000.0
        swir = swir_on_b8 / 10000.0

        # Valid mask (ignore zeros/negatives)
        valid = (nir > 0) & (swir > 0)

        # NDMI
        ndmi = np.full_like(nir, np.nan, dtype="float32")
        denom = nir + swir
        ndmi[valid] = (nir[valid] - swir[valid]) / np.maximum(denom[valid], 1e-6)

        # Write GeoTIFF using B08 georeferencing
        profile = b8.profile.copy()
        profile.update(
            driver="GTiff",
            dtype="float32",
            count=1,
            nodata=np.float32(np.nan),
            compress="deflate",
            predictor=2,
            tiled=True,
            blockxsize=256,
            blockysize=256,
        )
        with rio.open(out_path, "w", **profile) as dst:
            dst.write(ndmi, 1)


import numpy as np

def write_rgb_geotiff_3857(b02_path: str, b03_path: str, b04_path: str, out_path: str, out_dtype:str ) -> None:
    """
    Create a true-color RGB GeoTIFF from Sentinel-2 B02 (Blue), B03 (Green), B04 (Red),
    reprojected to EPSG:3857 (Web Mercator) for Leafmap basemaps.

    - Reads DN, scales to reflectance (/10000)
    - Reprojects each band to EPSG:3857 using B04's extent as reference
    - Global 2–98% stretch across all channels + mild gamma (brightens)
    - Writes 3-band uint8 GeoTIFF (R,G,B) in EPSG:3857
    """
    print(f"[Line {inspect.currentframe().f_lineno}] ...       ")
    # Open bands
    with rio.open(b04_path) as r:
        red_src  = r.read(1).astype("float32") / 10000.0
        src_crs  = r.crs
        src_tr   = r.transform
        src_w, src_h = r.width, r.height
        src_bounds = r.bounds

    with rio.open(b03_path) as g:
        green_src = g.read(1).astype("float32") / 10000.0
        g_tr, g_crs = g.transform, g.crs

    with rio.open(b02_path) as b:
        blue_src  = b.read(1).astype("float32") / 10000.0
        b_tr, b_crs = b.transform, b.crs

    # Destination (Web Mercator)
    dst_crs = "EPSG:3857"
    # Compute target grid using B04's bounds
    transform, width, height = calculate_default_transform(
        src_crs, dst_crs, src_w, src_h, *src_bounds
    )

    # Allocate destination arrays (float32 for reprojection)
    red_3857   = np.empty((height, width), dtype="float32")
    green_3857 = np.empty_like(red_3857)
    blue_3857  = np.empty_like(red_3857)
    print(f"[Line {inspect.currentframe().f_lineno}] ...       ")

    # Reproject each band to 3857
    reproject(
        source=red_src, destination=red_3857,
        src_transform=src_tr, src_crs=src_crs,
        dst_transform=transform, dst_crs=dst_crs,
        resampling=Resampling.bilinear
    )
    reproject(
        source=green_src, destination=green_3857,
        src_transform=g_tr, src_crs=g_crs,
        dst_transform=transform, dst_crs=dst_crs,
        resampling=Resampling.bilinear
    )
    reproject(
        source=blue_src, destination=blue_3857,
        src_transform=b_tr, src_crs=b_crs,
        dst_transform=transform, dst_crs=dst_crs,
        resampling=Resampling.bilinear
    )
    print(f"[Line {inspect.currentframe().f_lineno}] ...       ")

    # Global 2–98% stretch across all channels (ignore zeros)
    stack = np.stack([red_3857, green_3857, blue_3857], axis=0)
    valid = np.all(stack > 0, axis=0)
    vals = stack[:, valid].ravel()
    if vals.size == 0:
        raise ValueError("No valid pixels found to compute stretch.")
    p2, p98 = np.percentile(vals, (2, 98))
    scale = max(p98 - p2, 1e-6)
    stretched = np.clip((stack - p2) / scale, 0, 1)

    # Mild gamma to brighten midtones
    gamma = 1 / 2.2
    rgb = np.power(stretched, gamma)

    """
    Encode an RGB stack (float array in [0,1]) to desired dtype.

    Parameters
    ----------
    rgb : np.ndarray
        Shape (3, H, W), float in [0,1] after your stretch/gamma.
    out_dtype : str or np.dtype
        "uint8", "uint16", or "float32".
    uint16_mode : {"display", "reflectance"}
        - "display": scale [0,1] -> [0,65535] for visually-oriented 16-bit.
        - "reflectance": scale [0,1] -> [0,reflectance_scale] (e.g., 0–10000).
    reflectance_scale : int
        Max value for reflectance-style scaling if uint16_mode="reflectance".

    Returns
    -------
    np.ndarray
        Encoded array with shape (3, H, W) and the requested dtype.
    """
    print(f"[Line {inspect.currentframe().f_lineno}] ...       ")
    uint16_mode = "display" # hard-code for now. Consider "reflectance" later, for analysis.
    dt = np.dtype(out_dtype)
    rgb = np.clip(rgb, 0.0, 1.0)
    if dt == np.uint8:
        print(f"[Line {inspect.currentframe().f_lineno}] ...       ")
        rgb =  (rgb * 255.0 + 0.5).astype(np.uint8)  # +0.5 for rounding
    elif dt == np.uint16:
        print(f"[Line {inspect.currentframe().f_lineno}] ...       ")
        if uint16_mode == "display":
            rgb = (rgb * 65535.0 + 0.5).astype(np.uint16)
        elif uint16_mode == "reflectance":
            rgb = (rgb * float(reflectance_scale) + 0.5).astype(np.uint16)
        else:
            raise ValueError(f"Unknown uint16_mode: {uint16_mode!r}")
    elif dt == np.float32:
        print(f"[Line {inspect.currentframe().f_lineno}] ...       ")
        rgb = rgb.astype(np.float32)
    else:
        print(f"[Line {inspect.currentframe().f_lineno}] ...       ")
        raise ValueError(f"Unsupported out_dtype: {out_dtype!r}")

    # Write RGB GeoTIFF in EPSG:3857
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 3,
        "dtype": dt.name,            
        #"dtype": out_dtype,
        #"dtype": "uint8",
        "crs": dst_crs,
        "transform": transform,
        "photometric": "RGB",
        "compress": "deflate",
        "predictor": 2,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    with rio.open(out_path, "w", **profile) as dst:
        print(f"[Line {inspect.currentframe().f_lineno}] ... About to write  >",out_path,"<")
        dst.write(rgb)
        #dst.write(rgb8)
    print(f"[Line {inspect.currentframe().f_lineno}] ... Exiting sub      ")
 


import numpy as np

def write_masked_geotiff(out_array, out_transform, src_meta, out_path,
                         dtype="float32", nodata=np.float32(np.nan)):
    """
    Save a masked/cropped raster (from rasterio.mask.mask) to GeoTIFF.
    out_array: np.ndarray of shape (count, H, W)
    out_transform: Affine from mask(...)
    src_meta: original src.meta (provides CRS, etc.)
    """
    count, height, width = out_array.shape
    meta = src_meta.copy()
    meta.update({
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": count,
        "transform": out_transform,
        "crs": src_meta["crs"],
        "dtype": dtype,
        "nodata": nodata,
        "compress": "deflate",
        "predictor": 2,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    })

    with rio.open(out_path, "w", **meta) as dst:
        dst.write(out_array.astype(dtype))

def _ndmi_stats_from_crop(band: np.ndarray, transform, nodata=-9999.0) -> dict:
    """Compute NDMI stats on a masked/cropped float32 band."""
    import numpy as np
    valid = np.isfinite(band) & (band != nodata) & (band >= -1.0) & (band <= 1.0)
    vals = band[valid]
    print(f"[Line {inspect.currentframe().f_lineno}] ... ")
    stats = {
        "count_valid": int(valid.sum()),
        "mean": float(np.nanmean(vals)) if vals.size else float("nan"),
        "median": float(np.nanmedian(vals)) if vals.size else float("nan"),
        "std": float(np.nanstd(vals)) if vals.size else float("nan"),
        "p10": float(np.nanpercentile(vals, 10)) if vals.size else float("nan"),
        "p90": float(np.nanpercentile(vals, 90)) if vals.size else float("nan"),
    }
    print(f"[Line {inspect.currentframe().f_lineno}] ... ")
    # approximate valid area (m²); works best when src.crs is in meters (e.g., UTM)
    px_area_m2 = abs(transform.a * transform.e)  # e.g., 10m * -10m
    stats["area_m2_valid"] = float(stats["count_valid"] * px_area_m2)
    stats["area_km2_valid"] = stats["area_m2_valid"] / 1e6
    return stats

def crop_ndmi_to_gdf(ndmi_path: str, gdf_box: gpd.GeoDataFrame, out_path: str) -> None:
    if not os.path.exists(ndmi_path):
        print(f"... The file {ndmi_path} does NOT exist. Skipping the rest of our function.")
        return {
            "status": "missing_file",
            "path": ndmi_path,
            "mean": np.nan, "median": np.nan, "std": np.nan,
            "p10": np.nan, "p90": np.nan,
            "count_valid": 0, "area_m2_valid": 0.0, "area_km2_valid": 0.0,
        }
    print(f"... The file {ndmi_path} exists. So onward with our function..")
    print(f"[Line {inspect.currentframe().f_lineno}] ... Checking raster bounds for ",ndmi_path," :  ")
    show_raster_bounds(ndmi_path)
    with rio.open(ndmi_path) as src:
        print(f"[Line {inspect.currentframe().f_lineno}] ... ")
        if src.crs is None:
            print(f"[Line {inspect.currentframe().f_lineno}] ... ")
            raise ValueError(f"{ndmi_path} has no CRS")

        # 1) Ensure AOI has CRS and reproject to raster CRS
        aoi = gdf_box.copy()
        if aoi.crs is None:
            print(f"[Line {inspect.currentframe().f_lineno}] ... ")
            aoi = aoi.set_crs("EPSG:4326")   # assign if your coords are lon/lat
        aoi = aoi.to_crs(src.crs)
        # Fix invalid geometries (rotations are fine; self-intersections aren’t)
        aoi["geometry"] = aoi.geometry.buffer(0)
        aoi = aoi[~aoi.geometry.is_empty & aoi.geometry.notna()]
        if aoi.empty:
            print(f"[Line {inspect.currentframe().f_lineno}] ... ")
            raise ValueError("AOI has no valid geometry after cleanup.")

        # 2) Optional: fast overlap sanity check
        if not any(box(*src.bounds).intersects(geom) for geom in aoi.geometry):
            print(f"[Line {inspect.currentframe().f_lineno}] ... ")
            raise ValueError("AOI does not overlap the raster (check CRS/location).")

        print(f"[Line {inspect.currentframe().f_lineno}] ... ")
        # 3) Mask/crop (use numeric nodata for max viewer compatibility)
        shapes = [geom.__geo_interface__ for geom in aoi.geometry]
        out, out_transform = mask(src, shapes, crop=True, filled=True, nodata=-9999.0)

        if out.size == 0 or out.shape[1] == 0 or out.shape[2] == 0:
            print(f"[Line {inspect.currentframe().f_lineno}] ... ")
            raise ValueError("Crop produced an empty array.")

        band = out[0].astype("float32")
        band[~np.isfinite(band)] = -9999.0  # replace NaNs
        print(f"[Line {inspect.currentframe().f_lineno}] ... ")

        # --- NEW: compute NDMI stats on the cropped AOI ---
        stats = _ndmi_stats_from_crop(band, out_transform, nodata=-9999.0)
        print(f"NDMI mean: {stats['mean']:.4f}  (n={stats['count_valid']}, "
              f"p10={stats['p10']:.3f}, p90={stats['p90']:.3f}, "
              f"area_valid={stats['area_km2_valid']:.4f} km²)")



        # 4) Write a minimal, super-compatible GeoTIFF
        profile = {
            "driver": "GTiff",
            "height": band.shape[0],
            "width":  band.shape[1],
            "count":  1,
            "dtype":  "float32",
            "crs":    src.crs,
            "transform": out_transform,
            "nodata": -9999.0,
            # no compression/tiling to avoid picky viewers
        }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    print(f"[Line {inspect.currentframe().f_lineno}] ... ")
    with rio.open(out_path, "w", **profile) as dst:
        dst.write(band, 1)

    # 5) Verify it opens
    with rio.open(out_path) as chk:
        _ = chk.read(1)
        # print("OK:", chk.crs, chk.bounds, chk.shape)
        print(f"[Line {inspect.currentframe().f_lineno}] ... ")
    # Optionally return stats to the caller (backwards-compatible if ignored)
    return stats

def crop_raster_to_gdf(raster_path, gdf_box, out_path):
    with rio.open(raster_path) as src:
        aoi = gdf_box.to_crs(src.crs).buffer(0)
        shapes = [geom.__geo_interface__ for geom in aoi.geometry]
        out, out_transform = mask(src, shapes, crop=True, filled=True, nodata=np.nan)
        
        profile = src.profile.copy()
        profile.update({
            "height": out.shape[1],
            "width": out.shape[2],
            "transform": out_transform,
        })
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with rio.open(out_path, "w", **profile) as dst:
            dst.write(out)
    return out_path



def ndmi_mean_and_cloudflag(
    ndmi_path: str,
    gdf_box: gpd.GeoDataFrame,
    out_path: str,
    scl_path: str = None,           # L2A SCL_20m.jp2 (preferred)
    qa60_path: str = None,          # L1C QA60.jp2 (fallback)
    threshold_frac: float = 0.05,   # flag if >=5% cloudy (on the classifier grid)
    min_cloud_pixels: int = 1,      # and at least this many pixels
    include_shadow: bool = True,    # count SCL=3 as cloud?
    all_touched: bool = False,
    nodata_value: float = -9999.0,
):
    # --- open NDMI and crop to AOI ---
    with rio.open(ndmi_path) as src:
        if src.crs is None:
            raise ValueError(f"{ndmi_path} has no CRS")

        aoi = gdf_box.copy()
        if aoi.crs is None:
            aoi = aoi.set_crs("EPSG:4326")        # assign if coords are lon/lat
        aoi = aoi.to_crs(src.crs)                 # AOI -> raster CRS
        aoi["geometry"] = aoi.geometry.buffer(0)  # fix invalid
        aoi = aoi[~aoi.geometry.is_empty & aoi.geometry.notna()]
        if aoi.empty:
            raise ValueError("AOI has no valid geometry after cleanup.")
        if not any(box(*src.bounds).intersects(geom) for geom in aoi.geometry):
            raise ValueError("AOI does not overlap raster (CRS/location).")

        shapes = [geom.__geo_interface__ for geom in aoi.geometry]
        out, out_transform = mask(
            src, shapes, crop=True, filled=True,
            nodata=nodata_value, all_touched=all_touched
        )
        ndmi = out[0].astype("float32")

        # prepare output profile
        profile = {
            "driver": "GTiff",
            "height": ndmi.shape[0],
            "width":  ndmi.shape[1],
            "count":  1,
            "dtype":  "float32",
            "crs":    src.crs,
            "transform": out_transform,
            "nodata": nodata_value,
        }

    # --- compute mean NDMI over valid pixels (don’t mask clouds here) ---
    valid = np.isfinite(ndmi) & (ndmi != nodata_value)
    mean_ndmi = float(np.nan) if valid.sum() == 0 else float(ndmi[valid].mean())

    # --- cloud flag (optional) ---
    cloud_flag = None  # None = unknown (no classifier provided)
    if scl_path is not None or qa60_path is not None:
        path = scl_path if scl_path is not None else qa60_path
        with rio.open(path) as cls:
            if cls.crs is None:
                raise ValueError(f"{path} has no CRS")
            aoi_cls = gdf_box.copy()
            if aoi_cls.crs is None:
                aoi_cls = aoi_cls.set_crs("EPSG:4326")
            aoi_cls = aoi_cls.to_crs(cls.crs)
            shapes_cls = [geom.__geo_interface__ for geom in aoi_cls.geometry if geom and not geom.is_empty]
            arr3, _ = mask(cls, shapes_cls, crop=True, filled=True, nodata=0, all_touched=all_touched)
            arr = arr3[0]

        if scl_path is not None:
            # SCL classes: 8=med cloud, 9=high cloud, 10=cirrus (+3=shadow if chosen)
            classes = {8, 9, 10} | ({3} if include_shadow else set())
            valid_c = arr > 0
            clouds = np.isin(arr, list(classes)) & valid_c
        else:
            # QA60 bits: 10=cloud, 11=cirrus
            qa = arr.astype("uint16")
            valid_c = qa >= 0
            clouds = ((qa & (1 << 10)) != 0) | ((qa & (1 << 11)) != 0)

        n_valid = int(valid_c.sum())
        n_cloud = int(clouds.sum())
        # fraction on the classifier grid
        frac = (n_cloud / n_valid) if n_valid > 0 else 0.0
        min_pix_threshold = max(min_cloud_pixels, int(np.ceil(threshold_frac * n_valid)))
        cloud_flag = bool(n_cloud >= min_pix_threshold)

    # --- write cropped NDMI GeoTIFF ---
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with rio.open(out_path, "w", **profile) as dst:
        dst.write(ndmi, 1)
        # store handy tags
        dst.update_tags(
            mean_ndmi=str(mean_ndmi),
            cloud_flag=str(cloud_flag),
            classifier=("SCL" if scl_path else ("QA60" if qa60_path else "")),
        )

    # validate open
    with rio.open(out_path) as _chk:
        _ = _.read(1)

    return mean_ndmi, cloud_flag, out_path

def show_tif_fit(path, scale=12, cmap="gray"):
    """
    Show a tiny raster large in the notebook.
    scale controls the figure size; no resampling of data unless you pick interpolation.
    """
    if os.path.exists(path):
        print(f"[Line {inspect.currentframe().f_lineno}] ... path ",path," exists. Onward with displaying.")
    else:
        print(f"[Line {inspect.currentframe().f_lineno}] ... path ",path," does NOT exist. Skipping this one.     ")
        return
    with rio.open(path) as ds:
        data = ds.read(1)
        extent = (ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top)

    plt.figure(figsize=(scale, scale))
    # interpolation='nearest' keeps crisp pixels (use 'bilinear' if you want smoothing)
    plt.imshow(data, extent=extent, origin="upper", interpolation="nearest", cmap=cmap)
    plt.gca().set_aspect("equal")
    plt.axis("off")
    plt.tight_layout()
    plt.show()



def show_ndmi_BrBG (path, scale=10, vmin=None, vmax=None, smooth=False):
    with rio.open(path) as src:
        ndmi = src.read(1, masked=True).astype("float32")  # respects src.nodata if set

        # If nodata wasn't set in the file, also treat 0-mask as nodata
        border_mask = (src.read_masks(1) == 0)  # True outside AOI
        ndmi = np.ma.array(ndmi, mask=np.ma.getmaskarray(ndmi) | border_mask)

        # Robust stretch on valid data only
        vals = ndmi.compressed()
        if vals.size == 0:
            raise ValueError("No valid pixels in NDMI.")
        lo, hi = np.percentile(vals, (2, 98))
        if lo == hi:  # extremely uniform AOI
            lo, hi = np.min(vals), np.max(vals)

        plt.imshow(ndmi, vmin=lo, vmax=hi, cmap="BrBG")
        plt.axis("off")
        plt.title("NDMI (masked border, robust stretch)")
        plt.show()


def show_ndmi_moist(path, scale=10, vmin=None, vmax=None, smooth=False):
    """
    Pretty NDMI preview:
      • dramatic dry→moist colors
      • auto-stretches to robust percentiles
      • scales to fill the cell (no postage stamp)
    """
    if os.path.exists(path):
        print(f"[Line {inspect.currentframe().f_lineno}] ... path ",path," exists. Onward with displaying.")
    else:
        print(f"[Line {inspect.currentframe().f_lineno}] ... path ",path," does NOT exist. Skipping this one.     ")
        return
    with rio.open(path) as ds:
        a = ds.read(1).astype("float32")
        nodata = ds.nodata
        extent = (ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top)

    mask = ~np.isfinite(a)
    if nodata is not None:
        mask |= (a == nodata)
    #data = np.ma.array(a, mask=mask)
    data = np.ma.masked_array(a, mask=mask)  # CHANGED

    # Robust stretch (clip to NDMI's [-1, 1])
    if vmin is None or vmax is None:
        #finite = a[~mask.filled(True)]
        finite = a[~mask]              # mask is a plain boolean array

        lo, hi = (np.nanpercentile(finite, [2, 98]) if finite.size else (-1.0, 1.0))
        vmin = -1.0 if vmin is None else max(-1.0, vmin)
        vmax =  1.0 if vmax is None else min( 1.0, vmax)
        vmin, vmax = max(vmin, float(lo)), min(vmax, float(hi))
        # CHANGED: guard against invalid ranges
        if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
            vmin, vmax = -1.0, 1.0
    # Dry→neutral→moist palette (brown→beige→teal→deep blue)
    colors = ["#8c510a", "#f6e8c3", "#ffffbf", "#c7eae5", "#2c7fb8", "#08306b"]
    cmap = LinearSegmentedColormap.from_list("moist", colors, N=256)
    cmap = cmap.copy(); cmap.set_bad((0, 0, 0, 0))  # nodata transparent

    plt.figure(figsize=(scale, scale))
    # CHANGED: only use TwoSlopeNorm when 0 is inside the range; else fall back to Normalize
    norm = TwoSlopeNorm(vmin=vmin, vcenter=0.0, vmax=vmax) if (vmin < 0 < vmax) else Normalize(vmin=vmin, vmax=vmax)
    im = plt.imshow(
        data, extent=extent, origin="upper",
        cmap=cmap, norm=norm,
        interpolation="bilinear" if smooth else "nearest"
    )
    cbar = plt.colorbar(im, shrink=0.8, pad=0.02)
    cbar.set_label("NDMI  (dry  →  moist)")
    plt.axis("off"); plt.tight_layout(); plt.show()

"""
def ratio_r_over_gb(rgb_path, gdf_box=None, eps=1e-6):
    import os, numpy as np, rasterio as rio
    from rasterio.mask import mask
    from shapely.geometry import box as shp_box

    if not os.path.exists(rgb_path):
        return np.array([np.nan], dtype="float32")

    with rio.open(rgb_path) as ds:
        if gdf_box is None:
            shapes = [shp_box(*ds.bounds).__geo_interface__]
        else:
            aoi = gdf_box.copy()
            if aoi.crs is None:
                aoi = aoi.set_crs("EPSG:4326")
            aoi = aoi.to_crs(ds.crs)
            shapes = [geom.__geo_interface__ for geom in aoi.geometry]

        arr_ma, _ = mask(ds, shapes=shapes, crop=True, filled=False, all_touched=True)
        arr = arr_ma.astype("float32", copy=False).filled(np.nan)

    R, G, B = arr[0], arr[1], arr[2]
    denom = G + B
    ratio = G #np.where(denom > eps, R / denom, np.nan).astype("float32")
    #ratio = np.where(denom > eps, R / denom, np.nan).astype("float32")
    return ratio
"""


def daily_precip_openmeteo(lat, lon, start_date, end_date, tz="UTC"):
    print(f"[Line {inspect.currentframe().f_lineno}] ...   ")
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = dict(latitude=lat, longitude=lon,
                  start_date=start_date, end_date=end_date,
                  daily="precipitation_sum", timezone=tz)
    print(f"[Line {inspect.currentframe().f_lineno}] ...   ")
    r = requests.get(url, params=params, timeout=30); r.raise_for_status()
    d = r.json()["daily"]
    print(f"[Line {inspect.currentframe().f_lineno}] ... pd.to_datetime(d[time])  ",pd.to_datetime(d["time"]))
    print(f"[Line {inspect.currentframe().f_lineno}] ... d[precipitation_sum]  ",d["precipitation_sum"])
    return pd.DataFrame({
        "date": pd.to_datetime(d["time"]),
        "precip_mm": d["precipitation_sum"]
    }).sort_values("date").reset_index(drop=True)

# --- basic Open-Meteo client (same style as precipitation)
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def daily_temp_openmeteo(lat, lon, start, end):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":  lat,
        "longitude": lon,
        "start_date": start,
        "end_date":   end,
        "daily": ["temperature_2m_max",
                  "temperature_2m_min",
                  "temperature_2m_mean"],
        "timezone": "UTC"
    }
    r = openmeteo.weather_api(url, params=params)[0]
    daily = r.Daily()
    times = pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )
    df = pd.DataFrame({
        "date": times.normalize(),
        "tmax": daily.Variables(0).ValuesAsNumpy(),
        "tmin": daily.Variables(1).ValuesAsNumpy(),
        "tavg": daily.Variables(2).ValuesAsNumpy(),
    })
    return df

# Example use (same as with precipitation):
#temp_df = daily_temp_openmeteo(Constants.lat0, Constants.lon0, startDate, endDate)

import urllib.request
import json

# Define the function to fetch weather data
def fetch_weather_data(api_key, location, start_date, end_date, unit_group):
    base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
    url = f"{base_url}{location}/{start_date}/{end_date}?unitGroup={unit_group}&contentType=json&include=days&key={api_key}"
    save_file_name = "visualcrossing."+location+start_date+end_date+unit_group+".json"
    weather_data = {}
    if os.path.exists(save_file_name):
        print(f"Cell [Line {inspect.currentframe().f_lineno}] ... Loading data from  ",save_file_name," ...")
        with open(save_file_name, 'r') as file:
            weather_data = json.load(file)
        #weather_data = pd.read_csv(save_file_name)
        #return pd.DataFrame(weather_data)
        return weather_data
    else:
        try:
            response = urllib.request.urlopen(url)
            data = response.read()
            weather_data = json.loads(data)
            #weather_data.to_csv(save_file_name, index=False) 
            with open(save_file_name, 'w') as f:
                json.dump(weather_data, f)
            return weather_data
            #return pd.DataFrame(weather_data)
        except urllib.error.URLError as e:
            if hasattr(e, 'reason'):
                print('Failed to reach a server. Reason: ', e.reason)
            elif hasattr(e, 'code'):
                print('The server couldn\'t fulfill the request. Error code: ', e.code)
            return None




def crop_and_sum_intensity(band_path, aoi_gdf, scale_factor=None, clip_to_aoi_bounds=True):
    """
    Crop a Sentinel-2 band to AOI and aggregate intensities.
    
    Parameters
    ----------
    band_path : str
        Path to JP2 band (e.g., '14QQG_2025-01-02_B02.jp2').
    aoi_gdf : GeoDataFrame
        GeoDataFrame containing AOI geometry. Will be reprojected to band CRS.
    scale_factor : float, optional
        e.g., 1/10000 for Sentinel-2 reflectance.
    clip_to_aoi_bounds : bool, default True
        If True, crop tightly to AOI. If False, mask only.
    """
    with rio.open(band_path) as src:
        aoi_in_crs = aoi_gdf.to_crs(src.crs)
        geoms = [mapping(geom) for geom in aoi_in_crs.geometry]

        data, out_transform = mask(src, geoms, crop=clip_to_aoi_bounds, nodata=src.nodata)
        arr = data[0].astype(np.float64)

        if src.nodata is not None:
            valid_mask = arr != src.nodata
        else:
            valid_mask = ~np.isnan(arr)

        arr_valid = arr[valid_mask]
        if scale_factor is not None:
            arr_valid = arr_valid * scale_factor

        return {
            "sum": float(np.sum(arr_valid)),
            "mean": float(np.mean(arr_valid)) if arr_valid.size else float("nan"),
            "valid_pixels": int(arr_valid.size),
            "pixel_size": src.res,
            "band_crs": src.crs.to_string()
        }


def get_stats_from_gdf (my_gdf_box, input_tif, my_name, date, my_cloudy):
    empty_stats = {
        "count_valid": 0,
        "mean": float("nan"),
        "median": float("nan"),
    }     
    return_stats = empty_stats
    if os.path.exists(input_tif):
        print(f"Cell [Line {inspect.currentframe().f_lineno}] ... Found file  ",input_tif,", continuing process...")
    else :
        print(f"Cell [Line {inspect.currentframe().f_lineno}] ... Could not find file  ",input_tif,", aborting process...")
        return empty_stats
    my_tif = make_path_name("s2_parcel_tifs", latlon_to_s2_tile(Constants.lat0, Constants.lon0),date, my_name,"tif")    
    print(f"Cell [Line {inspect.currentframe().f_lineno}] ... done working with ",my_tif)
    if not my_cloudy: 
        print("Avg NDMI over AOI ", my_name," = ",return_stats.get("mean", np.nan) )
        #print("Area = ",my_gdf_box.area)
        return_stats = crop_ndmi_to_gdf(input_tif, my_gdf_box, my_tif)  
        return return_stats
    else: 
        print(f"[Line {inspect.currentframe().f_lineno}] ... Too cloudy. Returning NaN. ")
        return empty_stats

def compute_season_stat_significance(my_start_date,my_end_date,my_df,plotName1,plotName2):
    # AVG
    plot1_avg = my_df.loc[(my_df["date"] >= my_start_date) & (my_df["date"] <= my_end_date), plotName1].mean()
    plot2_avg = my_df.loc[(my_df["date"] >= my_start_date) & (my_df["date"] <= my_end_date), plotName2].mean()
    # STD DEV
    plot1_std_dev = my_df.loc[(my_df["date"] >= my_start_date) & (my_df["date"] <= my_end_date), plotName1].std()
    plot2_std_dev = my_df.loc[(my_df["date"] >= my_start_date) & (my_df["date"] <= my_end_date), plotName2].std()
    print("****************************")
    print ("For quantities : ",plotName1, ", ",plotName2, " report of difference between ", my_start_date," and ",my_end_date)
    # Std dev of the sum:
    print("std dev for ",plotName1 ," = ",   plot1_std_dev)
    print("std dev for ",plotName2 ," = ",   plot2_std_dev)
    sum_std_dev = np.sqrt(plot1_std_dev * plot1_std_dev + plot2_std_dev * plot2_std_dev)
    difference = np.absolute(plot2_avg- plot1_avg)
    print("Mean value of ",plotName1 ," over date range = ", plot1_avg)
    print("Mean value of ",plotName2 ," over date range = ", plot2_avg)
    print("difference between ",plotName1," and ",plotName2," = ",difference)
    print("std dev for difference  = ",  sum_std_dev )
    zscore = difference/sum_std_dev
    print("Z = ",zscore)
    p_values = scipy.stats.norm.sf(abs(zscore)) #one-sided
    print ("p value = ", p_values)
    print("****************************")
    return p_values

# my_df should be a dataframe that contains columns: date, cloudy, red_green_blue_average 
# as well as plot-specific measurements including: gndvi_plots_4_5, gndvi_milpa1, ndmi_plots_4_5, ndmi_milpa1, etc.
# This compares the quantity indicated in plotName during the season season_start_month_day to season_end_month_day,
# for comparison_year, vs. the range baseline_start_year, baseline_end_year.
# season_start_month, season_start_day, etc. should be int's.

def compute_current_vs_past_seasons_single_plot_stat_significance(baseline_start_year, baseline_end_year, comparison_year, season_start_month, season_start_day, season_end_month, season_end_day, my_df, plotName):
    # AVG
    plot_baseline_avg = 0
    plot_baseline_std_dev = 0
    myYear = baseline_start_year
    my_start_date = pd.to_datetime("2011-11-11")
    my_end_date = pd.to_datetime("2011-11-11")
    my_end_date = pd.to_datetime("2011-11-11")
    plot_baseline_df = my_df
    plot_baseline_df = plot_baseline_df.iloc[:0]  # initialize 
    while (myYear <= baseline_end_year) :
        my_start_date = pd.to_datetime(str(myYear)+"-"+str(season_start_month)+"-"+str(season_start_day))
        my_end_date = pd.to_datetime(str(myYear)+"-"+str(season_end_month)+"-"+str(season_end_day))
        #print ("Appending season from ",my_start_date," to ",my_end_date)
        plot_baseline_df = pd.concat([ plot_baseline_df ,  my_df.loc[(my_df["date"] >= my_start_date) & (my_df["date"] <= my_end_date),: ] ])
        #print("New length of plot_baseline_df = ", len(plot_baseline_df))
        #print("New mean() for plot_baseline_df = ", (plot_baseline_df.loc[:,plotName]).mean())
        #print("New  std() for plot_baseline_df = ", (plot_baseline_df.loc[:,plotName]).std())
        myYear +=1
    plot_baseline_avg = (plot_baseline_df.loc[:,plotName]).mean()
    plot_baseline_std = (plot_baseline_df.loc[:,plotName]).std()
    #print("std dev for ",baseline_start_year," to " ,baseline_end_year, " = ", plot_baseline_std )
    #print("ave for "    ,baseline_start_year," to " ,baseline_end_year, " = ", plot_baseline_avg )

    comparison_start_date = pd.to_datetime(str(comparison_year)+"-"+str(season_start_month)+"-"+str(season_start_day)  )
    comparison_end_date = pd.to_datetime(str(comparison_year)+"-"+str(season_end_month)+"-"+str(season_end_day)  )

    comparison_avg = my_df.loc[(my_df["date"] >= comparison_start_date) & (my_df["date"] <= comparison_end_date), plotName].mean()
    comparison_std = my_df.loc[(my_df["date"] >= comparison_start_date) & (my_df["date"] <= comparison_end_date), plotName].std()

    # Send report to stdout:
    print("****************************")
    print("Comparison of ",plotName," for the range of years ",baseline_start_year, " to ", baseline_end_year, " vs.  year ",comparison_year)
    print("std dev for ",comparison_year ," = ", comparison_std )
    print("ave for      ",comparison_year ," = ", comparison_avg )

    sum_std_dev = np.sqrt(comparison_std * comparison_std + plot_baseline_std * plot_baseline_std)
    #print("comparing ",comparison_year, " vs. ",baseline_start_year," to " ,baseline_end_year," for quantity ",plotName)
    print("std dev for difference  = ",  sum_std_dev )
    difference = np.absolute(comparison_avg - plot_baseline_avg)
    print("difference = ",difference)
    zscore = difference/sum_std_dev
    print("Z = ",zscore)
    p_values = scipy.stats.norm.sf(abs(zscore)) #one-sided
    print ("p value = ", p_values)
    print("****************************")
    return p_values

