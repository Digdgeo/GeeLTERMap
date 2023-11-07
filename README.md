# GeeLTERMap

The GeeLTERMap python package has been created as a resource for scientists and site managers integrated into the eLTER network to evaluate the monitoring of long-term ecosystem variables. It was developed within the scope of the eLTER Plus and SUMHAL projects. 
The package offers a dynamic map that integrates with deimsPY to facilitate the selection of any site in the eLTER network. Users can access phenometrics, surface temperature, and flooding data through three tools integrated in the main map application (PhenoApp, FloodApp and LSTApp).

![Projects logos](https://i.imgur.com/mvnOXuo.png)

Geeltermap is based on the [Geemap](https://geemap.org/) package, a Python API that allows access to Google Earth Engine (GEE) datasets and algorithms and provides an interactive map interface. Additionally, we have access to all alphanumeric and spatial information from the Elter sites thanks to DEIMS and its Python API, DEIMSpy. Furthermore, by enabling access to all relevant site-related information, we can establish custom filters for sites on which we wish to perform specific procedures.

![GeeLTERMap](https://i.imgur.com/YzuOcl8.png)


Our application includes three buttons integrated into a Leaflet/Geemap map environment. Each button provides access to one of the three primary tools described in subsequent below. Additionally, a form has been included inside the map as another button. This form allows users to submit their own data for validating satellite products.


## PhenoApp

This application enables users to monitor the long-term LSP of various types of vegetation covers. The application features a dynamic map that permits site selection within the network to view phenological metrics for individual or grouped pixels. These metrics are generated using the Sentinel 2 image series with the Python libraries [Ndvi2Gif](https://pypi.org/project/ndvi2gif/) and [PhenoPY](https://github.com/JavierLopatin/PhenoPY). Additionally, the application integrates the MODIS phenology products (MCD12Q2.006) and the Copernicus Sentinel 2 High Resolution Vegetation Phenology Product (HR-VPP) for comparison purposes. The application also includes a tool for downloading the generated rasters as GeoTIFF files.  
While Sentinel 2 products are not currently available as GEE datasets, they are offered exclusively for some selected sites. MODIS phenology, however, is available for all eLTER sites. In any case, a new Python package, [pyvpp](https://pypi.org/project/pyvpp/), has been developed to facilitate the speedy and effortless download of HR-VPP products across all eLTER sites.

![PhenoApp](https://i.imgur.com/dmG3G36.jpg)

## FloodApp

FloodApp is a tool for obtaining the flooded surface of eTER sites. The tool design includes the complete Landsat series from Landsat 4-TM to Landsat 9-OLI, which provides data from 1984 until now, along with Sentinel 2, which provides data from 2017, as datasets. 
The tool also enables obtaining pixel-wise statistics if the selected study period covers multiple images. The statistics include the minimum, maximum, mean, median, and percentiles of 10th, 20th, 90th, and 95th for different water indices. Water indices availables are NDWI (McFeeters 1996), NDWI (Gao et al. 2015), MNDWI (Xu 2006) and AWEI (Feyisa et al. 2014). SWIR-2 band has also been added to the list of water indices since we have been detected and tested, and this band offers a very good quality water mask in marshland areas. The user can also set a threshold to identify the index cutoff value that closely corresponds to the actual flooded area. 
Scenes could be filtered based on cloud cover to exclude those with a high percent of cloud cover over the area.  Also note that two RGB compositions of the chosen period are added to the map along with the water index, though the display is disabled by default. This enables visual comparison of flooding mask with real conditions. A button for downloading the generated rasters as GeoTIFF files is also provided.

![FloodApp](https://i.imgur.com/JZu7lED.png)

## LSTApp

The Land Surface Temperature tool provides access MODIS (MOD11A1) and Landsat (TIRS) datasets (Landsat 8 and 9 merged in one collection). The tool provides users with options to select the desired site, collection, start and end dates, filter by scene cloud coverage for Landsat and quality band for MODIS, and choose the band and statistic for image reduction in the desired timeframe. Likewise for the PhenoApp and FloodApp a legend can be displayed if desired on the screen. Like the other two tools, users can download data obtained from the LSTApp. 
Available bands are: ST_B10 for Landsat and LST_Day_1km & LST_Night_1km for MODIS. Available statistics fro image collections reduction are: minimum, maximum, mean, median, and percentiles of 10th, 20th, 90th, and 95th.

![LSTApp](https://i.imgur.com/EsbThl5.jpg)




