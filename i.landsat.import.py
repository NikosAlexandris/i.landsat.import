#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
 MODULE:       i.landsat.import

 AUTHOR(S):    Nikos Alexandris <nik@nikosalexandris.net>
               Based on a python script published in GRASS-Wiki

 PURPOSE:      Import Landsat scenes in independent Mapsets inside GRASS' data
               base

 COPYRIGHT:    (C) 2017 by the GRASS Development Team

               This program is free software under the GNU General Public
               License (>=v2). Read the file COPYING that comes with GRASS
               for details.
"""

#%module
#% description: Imports Landsat scenes (from compressed tar.gz files or unpacked directories)
#% keywords: imagery
#% keywords: landsat
#% keywords: import
#%end

#%flag
#%  key: l
#%  description: List input bands and exit
#%  guisection: Input
#%end

#%flag
#%  key: n
#%  description: Count scenes in pool
#%  guisection: Input
#%end

#%flag
#%  key: t
#%  description: t.register compliant list of scene names and their timestamp, one per line
#%  guisection: Input
#%end

#%rules
#% exclusive: -n, -t, -l
#%end

#%flag
#%  key: o
#%  description: Override projection check
#%  guisection: Input
#%end

#%flag
#%  key: c
#%  description: Do not copy the metatada file in GRASS' data base
#%  guisection: Input
#%end

#%flag
#%  key: e
#%  description: Link a scene's GeoTIFF band as a pseudo GRASS raster map
#%  guisection: Input
#%end

#%flag
#%  key: s
#%  description: Skip import of existing band(s)
#%end

#%rules
# %  excludes: -s, --o
#% excludes: -l, -s
#%end

#%flag
#%  key: r
#%  description: Remove scene directory after import if source is a tar.gz file
#%end

#%flag
#%  key: f
#%  description: Force time-stamping. Useful for imported bands lacking a timestamp.
#%end

#%flag
#%  key: d
#%  description: Do not timestamp imported bands
#%  guisection: Input
#%end

#%flag
#%  key: m
#%  description: Skip microseconds
#%  guisection: Input
#%end

#%flag
#%  key: 1
#%  description: Import all scenes in one Mapset
#%  guisection: Optional
#%end

#%option
#% key: scene
#% key_desc: id
#% label: One or multiple Landsat scenes
#% description: Compressed tar.gz files or decompressed and unpacked directories
#% multiple: yes
#% required: no
#%end

#%rules
#% requires_all: -r, scene
#%end

#%option
#% key: pool
#% key_desc: directory
#% label: Directory containing multiple Landsat scenes
#% description: Decompressed and untarred directories
#% multiple: no
#% required: no
#%end

#%rules
#% requires_all: -n, pool
#%end

#%option
#% key: bands
#% type: string
#% required: no
#% multiple: yes
#% description: Input band(s) to select (default is all bands)
#% descriptions: 1;Band 1;2;Band 2;3;Band 3;4;Band 4;5;Band 5;6;Band 6;7;Band 7;8;Band 8;9;Band 9;10;Thermal band 10;11;Thermal band 11;QA;Band Quality Assessment layer
#% options: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, QA
#% guisection: Input
#%end

#%option
#% key: set
#% key_desc: spectral subset
#% label: One or multiple subsets from a Landsat set of spectral bands
#% description: Subsets or index-specific Landsat spectral bands | Mosts subsets currently implemented for Landsat 8
#% descriptions: oli;Operational Land Imager, multi-spectral bands 1, 2, 3, 4, 5, 6, 7, 8, 9;tirs;Thermal Infrared Sensor, thermal bands 10, 11;bqa;Band Quality Assessment layer
#% options: all, arvi, avi, bqa, bsi, evi, gci, gndvi, infrared, msi, nbr, ndgi, ndmi, ndsi, ndvi, ndwi, oli, panchromatic, savi, shortwave, sipi, tirs, visible

#% multiple: yes
#% required: no
#%end

#%option
#% key: mapset
#% key_desc: name
#% label: Mapset to import all scenes in
#% multiple: no
#% required: no
#%end

#%rules
#% collective: -1, mapset
#%end

#%option
#% key: timestamp
#% key_desc: 'yyyy-mm-dd hh:mm:ss.ssssss +zzzz'
#% type: string
#% label: Manual timestamp definition
#% description: Date and time of scene acquisition
#% required: no
#%end

#%option G_OPT_F_OUTPUT
#%  key: tgis_output
#%  key_desc: filename
#%  label: Output file name for t.register compliant timestamps
#%  description: List of scene names and corresponding timestamps
#%  multiple: no
#%  required: no
#% guisection: Output
#%end

#%rules
##%  requires_all: tgis_output, -t
#%end

#%option
#% key: prefix
#% key_desc: prefix string
#% type: string
#% label: Prefix for scene names in tgis_output
#% description: Scene names will get this prefix in the tgis output file
#% required: no
#%end

#%option
#%  key: memory
#%  key_desc: Cache
#%  label: Maximum cache memory (in MB) to be used
#%  description: Cache size for raster rows
#%  type: integer
#%  multiple: no
#%  required: no
#%  options: 0-2047
#%  answer: 300
#%end

# required librairies
import os
import sys
sys.path.insert(
        1,
        os.path.join(os.path.dirname(sys.path[0]),
            'etc',
            'i.landsat.import',
        )
)

import shutil
import glob
import re
# import shlex
from datetime import datetime
import atexit
import grass.script as grass
from grass.exceptions import CalledModuleError
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from constants import HORIZONTAL_LINE
from constants import MEMORY_DEFAULT
from messages import MESSAGE_LIST_TIMESTAMPS_HEADLINE
from metadata import is_mtl_in_cell_misc
from metadata import copy_mtl_in_cell_misc
from timestamp import build_tgis_timestamp
from timestamp import get_timestamp
from bands import retrieve_band_filenames
from tar import list_files_in_tar
from tar import extract_tgz
from geotiff import import_geotiffs

grass_environment = grass.gisenv()
MAPSET = grass_environment['MAPSET']

def main():

    # flags
    list_bands = flags['l']
    count_scenes = flags['n']
    list_timestamps = flags['t']
    override_projection = flags['o']
    copy_mtl = not flags['c']
    link_geotiffs = flags['e']
    skip_import = flags['s']
    remove_untarred = flags['r']
    force_timestamp = flags['f']
    do_not_timestamp = flags['d']
    skip_microseconds = flags['m']
    single_mapset = flags['1']
    if single_mapset:
        mapset = options['mapset']
    else:
        mapset = MAPSET

    # options
    prefix = options['prefix']
    scene = options['scene']
    pool = options['pool']
    bands = options['bands'].split(',')
    spectral_sets = options['set'].split(',')
    timestamp = options['timestamp']
    tgis_output = options['tgis_output']
    memory = options['memory']
    if (memory != MEMORY_DEFAULT):
        message = HORIZONTAL_LINE
        message += (f'Cache size set to {memory} MB\n')
        message += HORIZONTAL_LINE
        grass.verbose(_(message))

    if pool:  # import all scenes from pool
        landsat_scenes, files = [item for item in os.walk(pool)][0][1:]
        landsat_scenes += files
        if count_scenes:
            count = len(landsat_scenes)
            message = f'Number of scenes in pool: {count}'
            g.message(_(message))
            return

    if scene:  # import single or multiple given scenes
        landsat_scenes = scene.split(',')

    for landsat_scene in landsat_scenes:
        if pool:  # requires the full path to the scene
            landsat_scene = os.path.join(pool, landsat_scene)

        if 'tar.gz' in landsat_scene:
            if list_bands:
                files_in_tar = list_files_in_tar(landsat_scene)
                break  # FIXME -- Will list only first tgz file!

            else:
                extract_tgz(landsat_scene)
                landsat_scene = landsat_scene.split('.tar.gz')[0]
                message = f'Scene {scene} decompressed and unpacked'
                grass.verbose(_(message))

        timestamp = get_timestamp(
                        scene=landsat_scene,
                        skip_microseconds=skip_microseconds,
                    )
        # date_time = validate_date_time_string(date_time)
        tgis_timestamp = build_tgis_timestamp(
                            prefix=prefix,
                            scene=os.path.basename(landsat_scene),
                            timestamp=timestamp,
                        )
        timestamps.append(tgis_timestamp)

        band_filenames = retrieve_band_filenames(
                            bands=bands,
                            spectral_sets=spectral_sets,
                            scene=landsat_scene,
                            )
        import_geotiffs(
                scene=landsat_scene,
                band_filenames=band_filenames,
                mapset=mapset,
                memory=memory,
                override_projection=override_projection,
                prefix=prefix,
                link_geotiffs=link_geotiffs,
                skip_import=skip_import,
                single_mapset=single_mapset,
                list_bands=list_bands,
                list_timestamps=list_timestamps,
                tgis_output=tgis_output,
                timestamp=timestamp,
                force_timestamp=force_timestamp,
                do_not_timestamp=do_not_timestamp,
                skip_microseconds=skip_microseconds,
                copy_mtl=copy_mtl,
        )

        if remove_untarred:
            message = f'Removing unpacked source directory {scene}'
            grass.verbose(_(message))
            shutil.rmtree(scene)

        if (
                not list_timestamps
                and not is_mtl_in_cell_misc(mapset)
                and (len(landsat_scenes) > 1)
        ):
            message = HORIZONTAL_LINE
            g.message(_(message))

    if list_timestamps:
        for timestamp in timestamps:
            g.message(_(timestamp))

    if tgis_output:
        output_file = open(tgis_output, 'w')
        for timestamp in timestamps:
            timestamp += '\n'
            output_file.write(timestamp)
        output_file.close()

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
