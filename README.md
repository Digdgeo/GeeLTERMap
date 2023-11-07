# GeeLTERMap

The GeeLTERMap python package has been created as a resource for scientists and site managers integrated into the eLTER network to evaluate the monitoring of long-term ecosystem variables. It was developed within the scope of the eLTER Plus and SUMHAL projects. 
The package offers a dynamic map that integrates with deimsPY to facilitate the selection of any site in the eLTER network. Users can access phenometrics, surface temperature, and flooding data through three tools integrated in the main map application (PhenoApp, FloodApp and LSTApp).

![Projects logos](https://i.imgur.com/mvnOXuo.png)

Geeltermap is based on the geemap package, a Python API that allows access to Google Earth Engine (GEE) datasets and algorithms and provides an interactive map interface. Additionally, we have access to all alphanumeric and spatial information from the Elter sites thanks to DEIMS and its Python API, DEIMSpy. Furthermore, by enabling access to all relevant site-related information, we can establish custom filters for sites on which we wish to perform specific procedures.

![GeeLTERMap](https://i.imgur.com/YzuOcl8.png)


Our application includes three buttons integrated into a Leaflet/Geemap map environment. Each button provides access to one of the three primary tools described in subsequent below. Additionally, a form has been included inside the map as another button. This form allows users to submit their own data for validating satellite products.


## PhenoApp

This application enables users to monitor the long-term LSP of various types of vegetation covers. The application features a dynamic map that permits site selection within the network to view phenological metrics for individual or grouped pixels. These metrics are generated using the Sentinel 2 image series with the Python libraries [Ndvi2Gif](https://pypi.org/project/ndvi2gif/) and [PhenoPY](https://github.com/JavierLopatin/PhenoPY). Additionally, the application integrates the MODIS phenology products (MCD12Q2.006) and the Copernicus Sentinel 2 High Resolution Vegetation Phenology Product (HR-VPP) for comparison purposes. The application also includes a tool for downloading the generated rasters as GeoTIFF files.  

While Sentinel 2 products are not currently available as GEE datasets, they are offered exclusively for some selected sites. MODIS phenology, however, is available for all eLTER sites. In any case, a new Python package, [pyvpp](https://pypi.org/project/pyvpp/), has been developed to facilitate the speedy and effortless download of HR-VPP products across all eLTER sites.


