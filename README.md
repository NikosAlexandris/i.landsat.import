*Work in progress*

i.landsat.import
================

*i.landsat.import* is a GRASS-GIS module that imports Landsat satellite imagery
scenes as native GRASS raster maps in its data base.

Landsat scenes can be acquired in two forms. One is a (packed and compressed)
`tar.gz` file. Another is an (uncompressed and unpacked) directory containing
the multispectral band and thermal channel acquisitions in form of GeoTiFF
files. Albeit, along with various metadata. The module treats both forms.
[option `scene`, single or multiple inputs]

The MTL metadata file is copied under the target mapset's `cell_misc`
directory. This can be cancelled by using the `-c` flag. Date (year, month,
day) and time (hours, minutes, seconds, timezone) of acquisitions are
transferred to each imported band. [see `r.timestamp`]

Alternatively, the module creates pseudo GRASS raster maps via the `-e` flag.
Instead of creating native GRASS raster maps, it links directly to the original
GeoTIFF files. [see `r.external`]

For whatsoever might be the reason, it is possible to rerun the import process.
Existing bands may be retained by skipping the import via the `-s` flag.
At the same time, for bands which might lack of a timestamp, time stamping may
be forced via the `-f` flag.

Multiple scenes are imported in individual Mapsets. That is bands of one scene,
are imported in one indepenendet Mapset. If requested, all scenes are imported
in one single Mapset. [flag `-1` and option `mapset`]. For the latter, band
names are prefixed with each scene's unique identifier. This may ease off
building time series via GRASS' temporal `t.`-modules.

The module has got some handy skills to count the number of scenes inside a
given `pool` directory [flag `-n`], list basic metadata and bands that pertain
to each scene [flag `-l`] as well as print, or export in a file, a valid TGIS
list of timestamps (one to use along with `t.register`) [flag `-t`].

Examples
========

In the following examples, work is demoed with the LC81840332014146LGN00
(decompressed and unpacked) scene.

First grass-y things first: create a Location for this scene. It lies inside the
WRS2 tile Path 184 and Row 033, which is covered by UTM zone 34N. This is done
automagically by using the geo-meta-tags that are part of all GeoTIFF files.

```
grass72 -c LC81840332014146LGN00_B1.TIF /grassdb/l8/
```

## Single scenes

Let's list basic metadata and bands
```
i.landsat.import -l LC81840332014146LGN00
```
will return
```
Date            Time

2014-05-26      09:10:26.7368720 +0000


Band    Filename

BQA     LC81840332014146LGN00_BQA.TIF
B11     LC81840332014146LGN00_B11.TIF
B6      LC81840332014146LGN00_B6.TIF
B1      LC81840332014146LGN00_B1.TIF
B8      LC81840332014146LGN00_B8.TIF
B10     LC81840332014146LGN00_B10.TIF
B9      LC81840332014146LGN00_B9.TIF
B7      LC81840332014146LGN00_B7.TIF
B4      LC81840332014146LGN00_B4.TIF
B3      LC81840332014146LGN00_B3.TIF
B2      LC81840332014146LGN00_B2.TIF
B5      LC81840332014146LGN00_B5.TIF
```

Its timestamp, in form to use with GRASS' TGIS, is:
```
i.landsat.import -t LC81840332014146LGN00

LC81840332014146LGN00<Suffix>|2014-05-26 09:10:26.7368720 +0000
```

*At the moment*, it is required to edit manually the <Suffix> part to
comply with the name of a STRDS. [ToDo: provide for a prefix to do this less
cumbersome].

We can import the scene in its own Mapset (use --v for verbosity) and request
from the module to *not* copy the MTL file under `cell_misc`
```
i.landsat.import -m LC81840332014146LGN00
```

By the way, the module will create a new Mapset, named after the directory
that contains the requested scene. Re-running the import command for the same
scene, will simply pass the step of recreating the existing Mapset.

If decision is made afterwards to copy the MTL file, we may re-run the import
process. The `-s` flag is therefore useful to skip over existing bands which
otherwise would break the execution. As well, it helps in cases where some
bands have been removed.

```
i.landsat.import LC81840332014146LGN00 -s --v
```

Noteworthy is the memory option which is passed, internally, to `r.in.gdal`,
the actual importer. [see also `r.in.gdal`]

As usual in GRASS GIS, the `--o` flag is always handy in case overwriting
existing maps is desired.

### Link to GeoTIFF files

Using the `-e` flags, the module calls internally `r.external`. GeoTIFF files
will be linked directly to GRASS' data base via pseudo GRASS raster maps.

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

Assuming we have in addition the scene LC81840332014226LGN00, we can list
them
```
i.landsat.import scene=LC81840332014146LGN00,LC81840332014226LGN00 -l
```
```
Date            Time

2014-05-26      09:10:26.7368720 +0000


Band    Filename

BQA     LC81840332014146LGN00_BQA.TIF
B11     LC81840332014146LGN00_B11.TIF
B6      LC81840332014146LGN00_B6.TIF
B1      LC81840332014146LGN00_B1.TIF
B8      LC81840332014146LGN00_B8.TIF
B10     LC81840332014146LGN00_B10.TIF
B9      LC81840332014146LGN00_B9.TIF
B7      LC81840332014146LGN00_B7.TIF
B4      LC81840332014146LGN00_B4.TIF
B3      LC81840332014146LGN00_B3.TIF
B2      LC81840332014146LGN00_B2.TIF
B5      LC81840332014146LGN00_B5.TIF
-------------------------------------------------------------------------------
Date            Time

2014-08-14      09:10:58.4714680 +0000


Band    Filename

B4      LC81840332014226LGN00_B4.TIF
B3      LC81840332014226LGN00_B3.TIF
B2      LC81840332014226LGN00_B2.TIF
B5      LC81840332014226LGN00_B5.TIF
B10     LC81840332014226LGN00_B10.TIF
B8      LC81840332014226LGN00_B8.TIF
B6      LC81840332014226LGN00_B6.TIF
B1      LC81840332014226LGN00_B1.TIF
B7      LC81840332014226LGN00_B7.TIF
BQA     LC81840332014226LGN00_BQA.TIF
B9      LC81840332014226LGN00_B9.TIF
B11     LC81840332014226LGN00_B11.TIF
-------------------------------------------------------------------------------
```
get their timestamps
```
i.landsat.import scene=LC81840332014146LGN00,LC81840332014226LGN00 -t
```
```
LC81840332014146LGN00<Suffix>|2014-05-26 09:10:26.7368720 +0000
LC81840332014226LGN00<Suffix>|2014-08-14 09:10:58.4714680 +0000
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
- `tgis` output file to collect timestamps suitable for t.register yet to be
implemented.
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
