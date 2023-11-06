import os
import ee

import deims

from .geemap import *
from .common import *

def add_elter_site(m=geeltermap.Map(), site=site):

    """function to add elter sites to the map

    Args:
        id_ (str): id of the site or network site to add to the map
    """
    a = deims.getSiteBoundaries(site)
    b = gdf_to_ee(a)
    m.add_ee_layer(b)

