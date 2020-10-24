*Work in progress*

i.landsat.import
================

*i.landsat.import* is a GRASS-GIS module that imports Landsat satellite imagery
scenes as native GRASS raster maps in its data base.

### Landsat scenes

Landsat scenes can be acquired in two forms. One is a (packed and compressed)
`tar.gz` file. Another is an (uncompressed and unpacked) directory containing
the multispectral band and thermal channel acquisitions in form of GeoTiFF
files. Albeit, along with various metadata. The module treats both forms.
[option `scene`, single or multiple inputs]

### Scene metadata

The MTL metadata file is copied under the target mapset's `cell_misc`
directory. This can be cancelled by using the `-c` flag. Date (year, month,
day) and time (hours, minutes, seconds, timezone) of acquisitions are
transferred to each imported band. [see `r.timestamp`]

### Link to GeoTIFF files

Alternatively, the module creates pseudo GRASS raster maps via the `-e` flag.
Instead of creating native GRASS raster maps, it links directly to the original
GeoTIFF files. [see `r.external`]

### Re-run the import script

For whatsoever might be the reason, it is possible to rerun the import process.
Existing bands may be retained by skipping the import via the `-s` flag.
At the same time, for bands which might lack of a timestamp, time stamping may
be forced via the `-f` flag.

### One or many mapsets

Multiple scenes are imported in individual Mapsets. That is bands of one scene,
are imported in one indepenendet Mapset. If requested, all scenes are imported
in one single Mapset. [flag `-1` and option `mapset`]. For the latter, band
names are prefixed with each scene's unique identifier. This may ease off
building time series via GRASS' temporal `t.*` modules.

### TGIS compliant list of timestamps

The module has got some handy skills to count the number of scenes inside a
given `pool` directory [flag `-n`], list basic metadata and bands that pertain
to each scene [flag `-l`] as well as print, or export in a file, a valid TGIS
list of timestamps, one to use along with `t.register` [flag `-t`].

Examples
========

In the following examples, work is demoed with the LC81840332014146LGN00
(decompressed and unpacked) scene.

First grass-y things first: create a Location for this scene. Remember, a
Location is defined by one and only spatial reference system. The scene in
question lies inside the WRS2 tile Path 184 and Row 033, which is covered by
UTM zone 34N. This is done automagically by using the geo-meta-tags that are
part of a GeoTIFF file.

```
grass78 -c LC08_L1TP_184033_20180403_20180417_01_T1_B1.TIF /grassdb/wrs2_184033/
```

## Single scenes

Let's list basic metadata and bands
```
i.landsat.import -l LC08_L1TP_184033_20180403_20180417_01_T1
```
will return
```
Band Filename
1 LC08_L1TP_184033_20180403_20180417_01_T1_B1.TIF
2 LC08_L1TP_184033_20180403_20180417_01_T1_B2.TIF
3 LC08_L1TP_184033_20180403_20180417_01_T1_B3.TIF
4 LC08_L1TP_184033_20180403_20180417_01_T1_B4.TIF
5 LC08_L1TP_184033_20180403_20180417_01_T1_B5.TIF
6 LC08_L1TP_184033_20180403_20180417_01_T1_B6.TIF
7 LC08_L1TP_184033_20180403_20180417_01_T1_B7.TIF
8 LC08_L1TP_184033_20180403_20180417_01_T1_B8.TIF
9 LC08_L1TP_184033_20180403_20180417_01_T1_B9.TIF
10 LC08_L1TP_184033_20180403_20180417_01_T1_B10.TIF
11 LC08_L1TP_184033_20180403_20180417_01_T1_B11.TIF
BQA LC08_L1TP_184033_20180403_20180417_01_T1_BQA.TIF
```

Get its timestamp, in form to use with GRASS' TGIS, via:
```
i.landsat.import -t LC08_L1TP_184033_20180403_20180417_01_T1

LC08_L1TP_184033_20180403_20180417_01_T1|03 Apr 2018 09:10:20.674074 +0000
```

We can import the scene in its own Mapset and request
from the module to *not* copy the MTL file under `cell_misc`
```
i.landsat.import -c LC08_L1TP_184033_20180403_20180417_01_T1

Date Time Timezone
2018-04-03 09:10:20.674074 +0000

Target Mapset
@LC08_L1TP_184033_20180403_20180417_01_T1

Band Filename
1 LC08_L1TP_184033_20180403_20180417_01_T1_B1.TIF
2 LC08_L1TP_184033_20180403_20180417_01_T1_B2.TIF
3 LC08_L1TP_184033_20180403_20180417_01_T1_B3.TIF
4 LC08_L1TP_184033_20180403_20180417_01_T1_B4.TIF
5 LC08_L1TP_184033_20180403_20180417_01_T1_B5.TIF
6 LC08_L1TP_184033_20180403_20180417_01_T1_B6.TIF
7 LC08_L1TP_184033_20180403_20180417_01_T1_B7.TIF
8 LC08_L1TP_184033_20180403_20180417_01_T1_B8.TIF
9 LC08_L1TP_184033_20180403_20180417_01_T1_B9.TIF
10 LC08_L1TP_184033_20180403_20180417_01_T1_B10.TIF
11 LC08_L1TP_184033_20180403_20180417_01_T1_B11.TIF
BQA LC08_L1TP_184033_20180403_20180417_01_T1_BQA.TIF

-------------------------------------------------------------------------------
MTL not transferred to:
/geoyeux/grassdb/wrs2_180034/LC08_L1TP_184033_20180403_20180417_01_T1/cell_misc
-------------------------------------------------------------------------------
```

By the way, the module will create a new Mapset, named after the directory
that contains the requested scene. Expectedly, the directory is named after the
scene's unique identifier. Re-running the import command for the same
scene, will simply pass the step of recreating the existing Mapset.

To create a copy of the MTL file under `cell_misc`, at a later stage, we may
re-run the import process. The `-s` flag is therefore useful to skip over
existing bands which otherwise would break the execution. As well, it helps in
cases where some bands have been removed.

```
i.landsat.import LC08_L1TP_184033_20180403_20180417_01_T1 -s
```

Noteworthy is the `memory` option. It is passed, internally, to `r.in.gdal`,
the actual importer. [see also `r.in.gdal`]

As usual in GRASS GIS, the `--o` flag is always handy in case overwriting
existing maps is desired.

### Link to GeoTIFF files

Using the `-e` flags, the module calls internally `r.external`. GeoTIFF files
will be linked to GRASS' data base via pseudo GRASS raster maps.

*** Below To Update ***

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

In case of many scenes, we can avoid typing or collecting all scene identifiers
to feed the `scene` option and collect all scenes under one directory. This one
directory can be fed to the module's `pool` option. For testing, we instruct
the following and expect to get the list of (already existing band scenes, each
in its own Mapset)
```
i.landsat.import pool=scenes --v -s
```

The module will fail if, among the scenes, it will detect one with a projection
that does not match the current Location! Moving the scene out of
the "pool" directory, will let the module (re-)run successfull. If, however,
the user knows that the suspicious scene is indeed in the same projection, as
the Location's one, the -o flag will override this check.


### All in one Mapset

Assuming we have in addition the scene LC81840332014226LGN00, we can list
out their components
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

[High]

- Test for empty Landsat scene directories and corrupted files. Act upon
accordingly. At the moment, a corrupted Landsat GeoTIFF will break the import
process. This will, subsequently, brake any scripted workflow in which
`i.landsat.import` is part of. 

[Low]

- Update README.md and manual
- Test for range of input date, time, timezone 
- What other meta can be transferred from the MTL file? Why not all! As in
https://github.com/NikosAlexandris/i.landsat8.swlst/blob/master/landsat8_mtl.py?

Notes
=====

- The "first" source for this module was a script published in
<https://grasswiki.osgeo.org/wiki/LANDSAT#Automated_data_import>.
- Microseconds are ignored in the TGIS world

Sources
=======

Unsorted

- http://landsathandbook.gsfc.nasa.gov/pdfs/Landsat_Calibration_Summary_RSE.pdf
- http://landsat.usgs.gov/band_designations_landsat_satellites.php
- https://landsat.usgs.gov/what-are-band-designations-landsat-satellites
- https://landsat.usgs.gov/collectionqualityband
