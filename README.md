
You will need to install a few libs. I do:
conda install -c conda-forge jupyterlab
conda create -n earth-observation -c conda-forge   python=3.12    jupyterlab   ipykernel   numpy   matplotlib   rasterio   geopandas  boto3 rasterstats matplotlib rasterio inspect importlib  pyproj shapely  libgdal-jp2openjpeg
conda activate earth-observation  
#conda install -c conda-forge numpy 
python -m pip install retry-requests

To reproduce the soil aggregate size histogram, use the r code and data in the soil-aggregate-sizes directory.

For the historic precipitation and temperature plot using openmeteo, 
In Constants.py, adjust lat0 and lon0 to your desired location
You can first have to create-NDMI-rgb-tile-geotiffs.ipynb, in order to get the cloud cover. See the instructions further down. Note that you do not have to do this, we also provide the NDMI and gNDVI data for 2022-2026 in .csv.           
issue:
python3 -m notebook openmeteo-weather.ipynb
In openmeteo-weather.ipynb, adjust startDate, endDate. Run all cells.


For the earth obseration data:

You will first have to run create-NDMI-rgb-tile-geotiffs.ipynb . On the command line, that is something like 
python3 -m notebook create-NDMI-rgb-tile-geotiffs.ipynb
You will need to set the "dates" range. At the latitude of Veracruz Sentinel2 only flies overhead every five days. For now it's just trial and error to pick a date that actually has images. If you see nothing but failed downloads, shift by a day and try again.

Make sure the dates(..) function is being called with the correct start and end dates. It is your responsibility to ensure that Sentinel2 was overhead on the start date. At this location it flies overhead every 5 days. You can do this by trial and error if need be. Once you have run this, the s2_point_series directory will be populated with one .jp2 image for every band and every flyover date (both the band and the date are in the file name).

The NDMI and GNDVI over the dry seasons plot is generated with NDMI-gNDVI-precip-temp-vs-time.ipynb . It assumes earth observation .tif files have been generated. Those are too heavy to put on github. Please generate them using the other mentioned script. 

Use NDMI-cumulative-image.ipynb to create the graphical abstract. The resulting image shows the ndmi averaged over the entire dry season. One can see the difference in moisture between the bare-soil plot and the A. pintoi cover cropped plots.
