*Work in progress*

i.landsat.import
================

*i.landsat.import* is a GRASS-GIS module that imports Landsat satellite imagery
scenes in GRASS GIS' data base. It treats Landsat scenes of both forms, `tar.gz`
(packed and compressed) as well as (decompressed and unpacked) GeoTiFF files of
a single scene that reside inside an independent directory. The module handles
also multiple scenes. It imports all bands that pertain to a scene in one
indepenendet Mapset. Date (year, month, day) and time (hours, minutes, seconds,
timezone) of acquisition are transferred to each imported band.


Notes
=====

- The "first" source for this module was a script published in
<http://grasswiki.osgeo.org/wiki/LANDSAT#Automated_data_import>.


Examples
========

To list all bands (and their GeoTiFF filenames), 
```
i.landsat.import pool=landsat_scenes -l
```

To derive a list of scenes (with a prefix --**To Do**--) and a valid TGIS timestamp (to use
with `t.register`):
```
i.landsat.import pool=landsat_scenes -t
```

And more to add...

To Do
=====

- Deduplicate code
- Test for range of input date, time, timezone
- Test if MTL file already exists in cell_misc
- What other meta can be transferred from the MTL file?

Sources
=======

Unsorted

- http://landsathandbook.gsfc.nasa.gov/pdfs/Landsat_Calibration_Summary_RSE.pdf
- http://landsat.usgs.gov/band_designations_landsat_satellites.php
- https://landsat.usgs.gov/what-are-band-designations-landsat-satellites
- https://landsat.usgs.gov/collectionqualityband
