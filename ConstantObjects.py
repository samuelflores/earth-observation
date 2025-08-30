import importlib

import Constants
importlib.reload(Constants)
import geopandas as gpd
from shapely.geometry import Polygon
import Utils


#print("n_cols in ConstantObjects:", Constants.n_cols)
import inspect
print(f"[Line {inspect.currentframe().f_lineno}] n_cols in ConstantObjects: {Constants.n_cols}")

print(f"[Line {inspect.currentframe().f_lineno}] n_cols: {Constants.n_cols}, n_rows: {Constants.n_rows}")

gdf_tree_circles = Utils.generate_tree_circles(
    Constants.lat0, 
    Constants.lon0,
    Constants.n_cols,
    Constants.n_rows,
    Constants.dx,
    Constants.dy,
    Constants.rotation_deg
)
print(f"[Line {inspect.currentframe().f_lineno}] n_cols in ConstantObjects: {Constants.n_cols}")

print(f"[Line {inspect.currentframe().f_lineno}] gdf_tree_circles.shape: {gdf_tree_circles.shape}")


gdf_box_plots_4_5 = Utils.draw_grid_box( # was gdf_box
    Constants.lat0, 
    Constants.lon0,
    Constants.dx,Constants.dy,
    Constants.n_cols,Constants.n_rows,
    Constants.rotation_deg,
    col1=8+3, row1=0,
    col2=13+3, row2=4,
    #col1=11, row1=0,
    #col2=16, :row2=4
    
)

gdf_box_plots_2_3_1A_1B = Utils.draw_grid_box(
    Constants.lat0, 
    Constants.lon0,
    Constants.dx,Constants.dy,
    Constants.n_cols,Constants.n_rows,
    Constants.rotation_deg,
    col1=2+3, row1=0,
    col2=7+3  , row2=12,
    #col1=5, row1=0,

)
print ("Constants.n_cols = ", Constants.n_cols)
print ("Constants.n_rows = ", Constants.n_rows)

gdf_box_river        = Utils.draw_grid_box(
    #Constants.lat0,
    Constants.lat0-.0032,
    Constants.lon0,
    #Constants.lon0-.007,
    Constants.dx,Constants.dy,
    Constants.n_cols,Constants.n_rows,
    0.0, # rotation angle                    
    col1=0, row1=0,
    col2=Constants.n_cols*12,row2=Constants.n_rows*12
)

gdf_box_terreno_casa = Utils.draw_grid_box(
    Constants.lat0, 
    Constants.lon0,
    Constants.dx,Constants.dy,
    Constants.n_cols,Constants.n_rows,
    Constants.rotation_deg,
    col1=0, row1=0,
    col2=Constants.n_cols-1, row2=Constants.n_rows-1
)

gdf_box_casa_y_vecino = Utils.draw_grid_box(
    Constants.lat0+.0013,
    Constants.lon0+.0005,
    Constants.dx,Constants.dy,
    40    ,200   , # cols, rows
    Constants.rotation_deg,
    col1=0, row1=0,
    col2=(40-1), row2= (60-1)           
)
gdf_box_milpa_vecino = Utils.draw_grid_box(
    Constants.lat0+.0013,
    Constants.lon0+.0005,
    Constants.dx,Constants.dy,
    40    ,200   , # cols, rows
    Constants.rotation_deg,
    col1=7, row1=5,
    col2=(14  ), row2= (56  )           
)

gdf_box_pueblo =  Utils.draw_grid_box(
    19.771852, #Constants.lat0,
    -96.868030, #Constants.lon0,
    Constants.dx,Constants.dy,
    Constants.n_cols,Constants.n_rows,
    0. , # rotation angle #Constants.rotation_deg,
    col1=0, row1=0,
    col2=34      , row2=50      
    #19.771852, -96.868030
)

gdf_box_xalapa_norte =  Utils.draw_grid_box(
    19.563464, #Constants.lat0,
    -96.914547, #Constants.lon0,
    Constants.dx,Constants.dy,
    Constants.n_cols,Constants.n_rows,
    0. , # rotation angle #Constants.rotation_deg,
    col1=0, row1=0,
    col2=30      , row2=60      
)

gdf_box_jilotepec_rural =  Utils.draw_grid_box(
    19.588953, #Constants.lat0,
    -96.887248, #Constants.lon0,
    Constants.dx,Constants.dy,
    Constants.n_cols,Constants.n_rows,
    0. , # rotation angle #Constants.rotation_deg,
    col1=0, row1=0,
    col2=30      , row2=60
)

#19.588953, -96.887248



# Your coordinates (longitude, latitude pairs)

coordsMilpa1 = [
    (-96.870102, 19.777411),
    (-96.870583, 19.777035),
    (-96.871361, 19.776827),
    (-96.871643, 19.776731),
    (-96.871582, 19.777145),
    (-96.871429, 19.777185),
    (-96.871193, 19.777403),
    (-96.870384, 19.777546),
    (-96.870102, 19.777411)  # Close the polygon
]

coordsMilpa2 = [
    (-96.870804, 19.777090),
    (-96.871132, 19.776869),
    (-96.871063, 19.776474),
    (-96.870583, 19.776627)
]

coords14QNG = [
    (-99.234,19.879),
    (-97.998,19.888),
    (-97.999,18.988),
    (-99.236,18.980),
    (-99.234,19.879) # Close polygon
]

coords14QKH = [
    (-96.870405, 19.888153),  # NW
    (-95.634522, 19.888207),  # NE
    (-95.634399, 18.988241),  # SE
    (-96.870107, 18.988191),  # SW
    (-96.870405, 19.888153)   # Close polygon
]

coords14QKG = [
    (-98.106640, 19.888200),  # NW
    (-96.870405, 19.888153),  # NE (shared with 14QKH)
    (-96.870107, 18.988191),  # SE (shared with 14QKH)
    (-98.106355, 18.988238),  # SW
    (-98.106640, 19.888200)   # Close polygon
]

# Create the polygon
polygonMilpa1 = Polygon(coordsMilpa1)
gdf_plotMilpa1 = gpd.GeoDataFrame(geometry=[polygonMilpa1], crs="EPSG:4326")

polygonMilpa2= Polygon(coordsMilpa2)
gdf_plotMilpa2 = gpd.GeoDataFrame(geometry=[polygonMilpa2], crs="EPSG:4326")

polygon14QNG = Polygon(coords14QNG )
gdf_plot14QNG  = gpd.GeoDataFrame(geometry=[polygon14QNG ], crs="EPSG:4326")

polygon14QKH = Polygon(coords14QKH )
gdf_plot14QKH  = gpd.GeoDataFrame(geometry=[polygon14QKH ], crs="EPSG:4326")


polygon14QKG = Polygon(coords14QKG )
gdf_plot14QKG  = gpd.GeoDataFrame(geometry=[polygon14QKG ], crs="EPSG:4326")

