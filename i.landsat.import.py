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

######################
# %rules
# %  excludes: -s, --o
# %end
######################

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
#%  key: output_tgis
#%  key_desc: filename
#%  label: Output file name for t.register compliant timestamps
#%  description: List of scene names and corresponding timestamps
#%  multiple: no
#%  required: no
#% guisection: Output
#%end

#%rules
#%  requires_all: output_tgis, -t
#%end

#%option
#% key: prefix
#% key_desc: prefix string
#% type: string
#% label: Prefix for scene names in output_tgis
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
import tarfile
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
from constants import IMAGE_QUALITY_STRINGS
from constants import MEMORY_DEFAULT
from constants import MONTHS
from constants import MTL_STRING
from constants import QA_STRING
from identifiers import LANDSAT_BANDS
from identifiers import LANDSAT_IDENTIFIERS
from identifiers import GEOTIFF_EXTENSION
from metadata import get_metafile
from metadata import is_mtl_in_cell_misc
from metadata import copy_mtl_in_cell_misc
from timestamp import get_timestamp

grass_environment = grass.gisenv()
MAPSET = grass_environment['MAPSET']

# helper functions
def run(cmd, **kwargs):
    """
    Pass quiet flag to grass commands
    """
    grass.run_command(cmd, quiet=True, **kwargs)

def identify_product_collection(scene):
    """
    Identify the collection and the validity of a Landsat scene product
    identifier by trying to match it against pre-defined regular expression
    templates.

    Parameters
    ----------
    scene :
        A Landsat product identifier string

    template :
        A list of regular expression templates against which to validate the
        'scene' string

    Returns
    -------
    ...

    Raises
    ------
    ...
    """
    for template_key in LANDSAT_IDENTIFIERS['scene_template']:
        template = LANDSAT_IDENTIFIERS['scene_template'][template_key]
        try:
            # re.match(pattern, string, flags=0)
            if re.match(template, scene):
                return template_key
        except:
            g.fatal(_("No match"))

def find_existing_band(band):
    """
    Check if band exists in the current mapset

    Parameter "element": 'raster', 'raster_3d', 'vector'
    """

    result = grass.find_file(name=band, element='cell', mapset='.')
    if result['file']:
        # grass.verbose(_("Band {band} exists".format(band=band)))
        return True

    else:
        return False

def retrieve_selected_filenames(bands, scene, regular_expression):
    """
    Retrieve filenames of user requested bands from a Landsat scene

    To Do
    -----
    Fix: requires a fix for 'tar.gz' files, i.e. if 'scene' = '*.tar.gz'!

    Parameters
    ----------
    bands :
        User requested bands

    scene :
        Landsat scene directory

    Returns
    -------
        Returns list of filenames of user requested bands

    Example
    -------
        ...
    """
    band_template = identify_product_collection(os.path.basename(scene))
    requested_filenames = []
    for band in bands:
        for filename in os.listdir(scene):
            template = regular_expression.format(band_pattern=band)
            pattern = re.compile(template)
            if pattern.match(filename):
                absolute_filename = scene + '/' + filename
                requested_filename = os.path.basename(glob.glob(absolute_filename)[0])
                requested_filenames.append(requested_filename)
    # print "Requested bands:"
    # print('\n'.join(map(str, requested_bands)))
    return requested_filenames

def retrieve_selected_sets_of_bands(spectral_sets, scene):
    """
    """
    requested_bands = []
    for spectral_set in spectral_sets:
        bands = list(LANDSAT_BANDS[spectral_set])
        requested_bands.extend(bands)

    return list(set(requested_bands))


def sort_list_of_bands(bands):
    """
    """
    filenames = sorted(bands, key=lambda item:
            (int(item.partition('_B')[2].partition('.')[0])
                if item.partition('_B')[2].partition('.')[0].isdigit()
                else float('inf'), item))
    return filenames

def scene_is_empty(scene):
    """
    What to do when an empty scene directory is found?
    Fail and indicate there is a problem.
    """
    pass

def list_files_in_tar(tgz):
    """List files in tar.gz file"""
    g.message(_('Listing files in tar.gz file'))

    # open tar.gz file in read mode
    tar = tarfile.TarFile.open(name=tgz, mode='r')

    # get names
    members = tar.getnames()

    # print out
    members = """
    {}
    """.format('\n'.join(members[1:]))
    g.message(_(members))

def extract_tgz(tgz):
    """
    Decompress and unpack a .tgz file
    """

    g.message(_('Extracting files from tar.gz file'))

    # open tar.gz file in read mode
    tar = tarfile.TarFile.open(name=tgz, mode='r')

    # get the scene's (base)name
    tgz_base = os.path.basename(tgz).split('.tar.gz')[0]

    # try to create a directory with the scene's (base)name
    # source: <http://stackoverflow.com/a/14364249/1172302>
    try:
        os.makedirs(tgz_base)

    # if something went wrong, raise an error
    except OSError:
        if not os.path.isdir(tgz_base):
            raise

    # extract files indide the scene directory
    tar.extractall(path=tgz_base)

def get_name_band(scene, filename, single_mapset=False):
    """
    """
    absolute_filename = os.path.join(scene, filename)

    # detect image quality strings in filenames
    # source: https://stackoverflow.com/q/7351744/1172302
    if any(string in absolute_filename for string in IMAGE_QUALITY_STRINGS):
        name = "".join((os.path.splitext(absolute_filename)[0].rsplit('_'))[-1])

    # keep only the last part of the filename
    else:
        name = os.path.splitext(filename)[0].rsplit('_')[-1]

    # found a wrongly named *MTL.TIF file in LE71610432005160ASN00
    if MTL_STRING in absolute_filename:  # use grass.warning(_("..."))?
        message_fatal = "Detected an MTL file with the .TIF extension!"
        message_fatal += "\nPlease, rename the extension to .txt and retry."
        grass.fatal(_(message_fatal))

    # is it the QA layer?
    elif (QA_STRING) in absolute_filename:
        band = name

    # is it a two-digit multispectral band?
    elif len(name) == 3 and name[0] == 'B' and name[-1] == '0':
        band = int(name[1:3])

    # what is this for?
    elif len(name) == 3 and name[-1] == '0':
        band = int(name[1:2])

    # what is this for?
    elif len(name) == 3 and name[-1] != '0':
        band = int(name[1:3])

    # is it a single-digit band?
    else:
        band = int(name[-1:])

    # one Mapset requested? prefix raster map names with scene id
    if single_mapset:
        name = os.path.basename(scene) + '_' + name

    return name, band

def import_geotiffs(
        scene,
        bands,
        mapset,
        memory,
        single_mapset=False,
        list_bands=False,
        tgis=False,
        timestamp=None,
        skip_microseconds=False,
    ):
    """
    Imports all bands (GeoTIF format) of a Landsat scene be it Landsat 5,
    7 or 8.  All known naming conventions are respected, such as "VCID" and
    "QA" found in newer Landsat scenes for temperature channels and Quality
    respectively.

    Parameters
    ----------
    scene :
        Input scene name string

    bands :
        Bands to import

    mapset :
        Name of mapset to import to

    memory :
        See options for r.in.gdal

    list_bands :
        Boolean True or False

    tgis :
        Boolean True or False
    """

    if not timestamp:
        timestamp = get_timestamp(scene, tgis, skip_microseconds)
        # date_time = validate_date_time_string(date_time)
        timestamp_message = "(set manually)"
        print_timestamp(os.path.basename(scene), timestamp, tgis)

    if not single_mapset:
        # set mapset from scene name
        mapset = os.path.basename(scene)

    message = str()  # a string holder

    # verbosity: target Mapset
    if not any(x for x in (list_bands, tgis)):
        message = 'Target Mapset\n@{mapset}\n\n'.format(mapset=mapset)

    # communicate input band name
    if not tgis:
        message += 'Band\tFilename\n'
        g.message(_(message))

    # loop over files inside a "Landsat" directory
    # sort band numerals, source: https://stackoverflow.com/a/2669523/1172302

    if bands == 'all':
        filenames = sort_list_of_bands(os.listdir(scene))
        # filenames = sorted(os.listdir(scene), key=lambda item:
        #         (int(item.partition('_B')[2].partition('.')[0])
        #             if item.partition('_B')[2].partition('.')[0].isdigit()
        #             else float('inf'), item))

    else:
        filenames = sort_list_of_bands(bands)

    for filename in filenames:

        # if not GeoTIFF, keep on working
        if os.path.splitext(filename)[-1] != GEOTIFF_EXTENSION:
            continue

        # use the full path name to the file
        name, band = get_name_band(scene, filename, single_mapset)
        band_title = 'band {band}'.format(band = band)

        if not tgis:

            message_overwriting = '\t [ Exists, overwriting]'

            # communicate input band and source file name
            message = '{band}'.format(band = band)
            message += '\t{filename}'.format(filename = filename)
            if not skip_import:
                g.message(_(message))

            else:
                # message for skipping import
                message_skipping = '\t [ Exists, skipping ]'

        if not any(x for x in (list_bands, tgis)):

            # get absolute filename
            absolute_filename = os.path.join(scene, filename)

            # srt import parameters
            parameters = dict(input = absolute_filename,
                    output = name,
                    flags = '',
                    title = band_title,
                    quiet = True)

            if override_projection:
                parameters['flags'] += 'o'

            # create Mapset of interest, if it doesn't exist
            devnull = open(os.devnull, 'w')
            run('g.mapset',
                    flags='c',
                    mapset=mapset,
                    stderr = devnull)
            # g.mapset(flags='c', mapset=mapset)

            if (skip_import
                    and find_existing_band(name)
                    and not grass.overwrite()):

                if force_timestamp:
                    set_timestamp(name, timestamp)
                    g.message(_('   >>> Forced timestamping for {b}'.format(b=name)))

                message_skipping = message + message_skipping
                g.message(_(message_skipping))
                pass

            else:
                if (grass.overwrite() and find_existing_band(name)):
                    if force_timestamp:
                        set_timestamp(name, timestamp)
                        g.message(_('   >>> Forced timestamping for {b}'.format(b=name)))

                    message_overwriting = message + message_overwriting
                    g.message(_(message_overwriting))
                    pass

                if (skip_import and not find_existing_band(name)):
                    # FIXME
                    # communicate input band and source file name
                    message = '{band}'.format(band = band)
                    message += '\t{filename}'.format(filename = filename)
                    grass.message(_(message))

                if link_geotiffs:
                    # What happens with the '--overwrite' flag?
                    # Check if it can be retrieved.

                    r.external(**parameters)

                else:
                    if memory:
                        parameters['memory'] = memory
                    # try:
                    r.in_gdal(**parameters)

                    # except CalledModuleError:
                        # grass.fatal(_("Unable to read GDAL dataset {s}".format(s=scene)))

                if not do_not_timestamp:
                    set_timestamp(name, timestamp)

        else:
            pass

    # copy MTL
    if not list_bands and not tgis:
        copy_mtl_in_cell_misc(
                scene,
                mapset,
                tgis,
                single_mapset,
                copy_mtl
        )

def main():

    # flags
    link_geotiffs = flags['e']
    copy_mtl = not flags['c']
    override_projection = flags['o']
    skip_import = flags['s']
    remove_untarred = flags['r']
    list_bands = flags['l']
    count_scenes = flags['n']

    skip_microseconds = flags['m']
    do_not_timestamp = flags['d']
    tgis = flags['t']
    force_timestamp = flags['f']

    single_mapset = flags['1']

    # options
    scene = options['scene']

    # identify product collection
    product_collection = identify_product_collection(os.path.basename(scene))
    try:
        regular_expression_template = LANDSAT_IDENTIFIERS['band_template'][product_collection]
    except:
        grass.fatal(_("The given scene identifier does not match any known Landsat product file name pattern!"))

    pool = options['pool']

    if options['bands']:
        bands = options['bands'].split(',')
        bands = retrieve_selected_filenames(
                bands,
                scene,
                regular_expression_template)
    else:
        bands = 'all'

    # This will fail is the 'scene=' is a compressed one, i.e. tar.gz # FIXME
    if options['set']:
        # bands = list(LANDSAT_BANDS[spectral_set])
        if len(options['set']) > 1:
            spectral_sets = options['set'].split(',')

        bands = retrieve_selected_sets_of_bands(
                spectral_sets,
                scene)
        bands = retrieve_selected_filenames(
                bands,
                scene,
                regular_expression_template)

    timestamp = options['timestamp']
    timestamps = []

    tgis_output = options['output_tgis']

    memory = options['memory']

    if list_bands or count_scenes:  # don't import
        os.environ['GRASS_VERBOSE'] = '3'

    # if a single mapset requested
    if single_mapset:
        mapset = options['mapset']

    else:
        mapset = MAPSET

    if (memory != MEMORY_DEFAULT):
        message = HORIZONTAL_LINE
        message += ('Cache size set to {m} MB\n'.format(m = memory))
        message += HORIZONTAL_LINE
        grass.verbose(_(message))

    # import all scenes from pool
    if pool:
        landsat_scenes = [x[0] for x in os.walk(pool)][1:]

        if count_scenes:
            message = 'Number of scenes in pool: {n}'
            message = message.format(n = len(landsat_scenes))
            g.message(_(message))

        else:
            count = 0
            for landsat_scene in landsat_scenes:
                import_geotiffs(landsat_scene,
                        bands,
                        mapset,
                        memory,
                        single_mapset,
                        list_bands,
                        tgis,
                        timestamp,
                        skip_microseconds,
                )

    # import single or multiple given scenes
    if scene:
        landsat_scenes = scene.split(',')

        for landsat_scene in landsat_scenes:
            if 'tar.gz' in landsat_scene:
                if list_bands:
                    list_files_in_tar(landsat_scene)
                    break
                else:
                    extract_tgz(landsat_scene)
                    landsat_scene = landsat_scene.split('.tar.gz')[0]
                    message = 'Scene {s} decompressed and unpacked'
                    message = message.format(s = scene)
                    grass.verbose(_(message))
                    del(message)

            import_geotiffs(
                    landsat_scene,
                    bands,
                    mapset,
                    memory,
                    single_mapset,
                    list_bands,
                    tgis,
                    timestamp,
                    skip_microseconds,
            )

            if remove_untarred:
                message = 'Removing unpacked source directory {s}'
                message = message.format(s = scene)
                grass.verbose(_(message))
                del(message)
                shutil.rmtree(scene)

            if not tgis and not is_mtl_in_cell_misc(mapset) and (len(landsat_scenes) > 1):
                message = HORIZONTAL_LINE
                g.message(_(message))
                del(message)

    # output tgis compliant list of maps names and corresponding timestamps
    if tgis and tgis_output:
        output_file = open(tgis_output, 'w')

        for timestamp in timestamps:
            timestamp += '\n'
            output_file.write(timestamp)

        output_file.close()
        del(output_file)

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
