DESCRIPTION
-----------

*i.landsat.import* is a GRASS-GIS module that imports Landsat satellite imagery
in GRASS GIS data base. It treats Landsat data of both forms, `tar.gz` (packed
and compressed) as well as (decompressed and unpacked) GeoTiFF files of a
single scene that reside inside an independent directory. The module handles
also multiple scenes. It imports all bands that pertain to a scene in one
indepenendet Mapset. Date (year, month, day) and time (hours, minutes,
seconds, timezone) of acquisition are transferred to each imported band.

### Overview

```
Band 1 - Ultra Blue (coastal/aerosol)
Band 2 - Blue
Band 3 - Green
Band 4 - Red
Band 5 - Near Infrared (NIR)
Band 6 - Shortwave Infrared (SWIR) 1
Band 7 - Shortwave Infrared (SWIR) 2
Band 8 - Panchromatic
Band 9 - Cirrus
Band 10 - Thermal Infrared (TIRS) 1
Band 11 - Thermal Infrared (TIRS) 2
```

### Details


NOTES
-----

?


EXAMPLES
--------

## Remarks


TODO
----

- What other meta can be transferred from the MTL file?

REFERENCES
----------

https://landsat.usgs.gov/landsat-8

- https://landsat.usgs.gov/what-are-band-designations-landsat-satellites
- https://landsat.usgs.gov/how-does-landsat-8-differ-previous-landsat-satellites
- https://landsat.usgs.gov/using-usgs-landsat-8-product
- https://landsat.usgs.gov/landsat-8-l8-data-users-handbook
- https://landsat.usgs.gov/collectionqualityband

SEE ALSO
--------


AUTHORS
-------

Nikos Alexandris
GRASS GIS Wiki Authors
