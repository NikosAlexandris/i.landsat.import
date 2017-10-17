*Work in progress*

i.landsat.import
================

*i.landsat.import* is a GRASS-GIS module that imports Landsat satellite imagery
scenes in GRASS GIS' data base. It treats Landsat scenes of both forms, `tar.gz`
(packed and compressed) as well as (decompressed and unpacked) GeoTiFF files of
a single scene that reside inside a directory named after the scene.

The module handles also multiple scenes. It imports all bands that pertain to a
scene in one indepenendet Mapset. If requested, multiple scenes are imported in
one Mapset and band names are prefixed with each scene's unique identifier.

The MTL metadata file is copied under the target mapset's `cell_misc`
directory. This can be however overriden by using the `m` flag.
Date (year, month, day) and time (hours, minutes, seconds, timezone) of
acquisition are transferred to each imported band.

The module has got some handy skills to print out only the number of scenes
inside the `pool` directory, list basic metadata and bands that pertain to each
scene as well as print out a valid TGIS list of timestamps (one to use along
with `t.register`).

Examples
========

## Single scenes

Assuming we have beforehand the scene LC81840332014146LGN00 (decompressed and
unpacked), let's list basic metadata and bands of a scene
```
i.landsat.import -l LC81840332014146LGN00
```

The timestamp for this scene, to use with GRASS' TGIS, is:
```
LC81840332014146LGN00<Suffix>|2014-05-26 09:10:26.7368720 +0000
```

Note, at the moment, it is required to edit manually the <Suffix> part to
comply with the name of a STRDS. [ToDo: provide for a prefix to do this less
cumbersome].

We can import this scene in its own Mapset (use --v for verbosity) and request
from the module to not copy the MTL file under `cell_misc`
```
i.landsat.import -m LC81840332014146LGN00
```

By the way, the module will only create a new Mapset, named after the directory
that contains the requested scene. In this way, re-running the same command
will skip recreating an existing Mapset.

If we decide to copy afterwards the MTL file, or, even, if we somehow have
removed one of the bands, the module will skip re-importing existing bands.

Expectedly, repeating the previous command `i.landsat.import -m
LC81840332014146LGN00`, will break and complaing about existing bands. Using
the -s flag, the module will skip existing bands
```
i.landsat.import LC81840332014146LGN00 -s --v
```

## Multiples scenes

### In independent Mapsets

We import both scenes in one step, each in its own Mapset. For this example, the
command
```
i.landsat.import scene=LC81840332014146LGN00,LC81840332014226LGN00 --v
```
will fail at first since we have already imported the first scene. We may
remove the respective Mapset and and re-import everything. Or, we may use the
-s flag to skip existing material
```
i.landsat.import scene=LC81840332014146LGN00,LC81840332014226LGN00 --v -s
```

If we have many scenes, we can avoid typing or collecting all scene identifiers
to feed the `scene` option and collect all scenes under one directory. This one
directory can be fed to the module's `pool` option. For testing, we instruct
the following and expect to get the list of (already existing band scenes, each
in its own Mapset)
```
i.landsat.import pool=scenes --v -s
```

The module will fail if, among the scenes, it will detect one with a projectio
that does not match the one of the current Location! Moving the scene out of
the "pool" directory, will let the module (re-)run successfull. If, however,
the user knows that the suspicious scene is indeed in the same projection, as
the Location's one, the -o flag will override this check.


### All in one Mapset

Assuming we have in addition the scecen *LC81840332014226LGN00*, we can list
them
```
i.landsat.import scene=LC81840332014146LGN00,LC81840332014226LGN00 -l
```
get their timestamps
```
i.landsat.import scene=LC81840332014146LGN00,LC81840332014226LGN00 -t
```
or/and import both scenes in a Mapset customly named `LC8184033`
```
i.landsat.import scene=LC81840332014146LGN00,LC81840332014226LGN00 --v -1 mapset=LC8184033
```

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

- Complete README.md, update/improve manual
- memory option is not passed to `r.in.gdal`
- Fix: MTL file is copied as file named `cell_misc` under the PERMANENT mapset.
- Test for range of input date, time, timezone
- What other meta can be transferred from the MTL file?

Notes
=====

- The "first" source for this module was a script published in
<http://grasswiki.osgeo.org/wiki/LANDSAT#Automated_data_import>.

Sources
=======

Unsorted

- http://landsathandbook.gsfc.nasa.gov/pdfs/Landsat_Calibration_Summary_RSE.pdf
- http://landsat.usgs.gov/band_designations_landsat_satellites.php
- https://landsat.usgs.gov/what-are-band-designations-landsat-satellites
- https://landsat.usgs.gov/collectionqualityband
