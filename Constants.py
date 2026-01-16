import pandas as pd
from rasterio.transform import from_bounds



# Point of interest (Veracruz)
#lat, lon = 19.777411, -96.870102

# Sentinel-2 tile metadata
tile = {
    "utm_zone": "14",
    "latitude_band": "Q",
    "grid_square": "NG"
}

# Bounding box for tile T14QNG in lat/lon (WGS84)
#bounds_wgs84 = (-96.98, 19.53, -96.38, 20.03) # magic number!!!
tile_width, tile_height = 10980, 10980  # 10m resolution

#transform_override = from_bounds(*bounds_wgs84, tile_width, tile_height)
crs_override = "EPSG:4326"

# This will be used to define the season of interest for earlier years as well.
#reference:
#Alonso-Dı´az MA, Castillo-Gallegos E, Basurto-Camberos H,Jarillo-Rodrı´guez J, Valles-de la Mora B (2007) Respuesta
#productiva de una pastura de gramas nativas bajo pastoreo rotacional intensivo en clima ca´lido hu´medo. Avances en Investigacio´n Agropecuaria 11:35–55

warmDryStart2025 = pd.to_datetime("2025-03-01")
warmDryEnd2025   = pd.to_datetime("2025-06-30") 
# This will cause all stat significance to disappear:
#warmDryStart2025 = pd.to_datetime("2025-01-01")
#warmDryEnd2025   = pd.to_datetime("2025-07-30") 

# Dates you want to sample NDMI from (you can extend this list)
dates = [
    "2025-05-02",
    "2025-05-04",
    "2025-05-05",
    "2025-05-07",
    "2025-05-10",
    "2025-05-12"
]


# Tree grid parameters
lat0 = 19.7782 #location of tree at col 0 row 0. Note there is no actual tree at this location, it is on the driveway.
lon0 = -96.86942
#honolulu coordinates, for testing:
#lat0=21.3099
#lon0= -157.8581
# port Isabel, TX :
#lat0=26.0734
#lon0= -97.2086
# Borana University, Ethiopia. 1st October 2021 to the 30th of June 2022.
lat0=4.908058823095451
lon0= 38.15135412942004

# These were the lime tree locations:
n_cols=21
n_rows=18
dx=5
dy=4
rotation_deg=-155
