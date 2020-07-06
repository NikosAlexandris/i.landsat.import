#!/usr/bin/python
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
#% description: Subsets of Landsat's set of spectral bands
#% descriptions: oli;Operational Land Imager, multi-spectral bands 1, 2, 3, 4, 5, 6, 7, 8, 9;tirs;Thermal Infrared Sensor, thermal bands 10, 11;bqa;Band Quality Assessment layer
#% options: all, bqa, coastal, infrared, ndvi, oli, panchromatic, tirs, visible
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

# globals
MONTHS = {'01': 'jan', '02': 'feb', '03': 'mar', '04': 'apr', '05': 'may',
          '06': 'jun', '07': 'jul', '08': 'aug', '09': 'sep', '10': 'oct',
          '11': 'nov', '12': 'dec'}

DATE_STRINGS = ['DATE_ACQUIRED', 'ACQUISITION_DATE']
TIME_STRINGS = ['SCENE_CENTER_TIME', 'SCENE_CENTER_SCAN_TIME']
ZERO_TIMEZONE = '+0000'
GRASS_VERBOSITY_LELVEL_3 = '3'
IMAGE_QUALITY_STRINGS = ['QA', 'VCID']
QA_STRING = 'QA'  # Merge with above?  # FIXME
MTL_STRING = 'MTL'
HORIZONTAL_LINE = 79 * '-' + '\n'
MEMORY_DEFAULT = '300'

# environment variables
grass_environment = grass.gisenv()
GISDBASE = grass_environment['GISDBASE']
LOCATION = grass_environment['LOCATION_NAME']
MAPSET = grass_environment['MAPSET']

# # path to "cell_misc"
CELL_MISC = 'cell_misc'

# scene and product identifiers, regular expression patterns and templates

# LANDSAT_PRODUCT_IDENTIFIER = {
#         'PREFIX': 0,
#         'SENSOR': 1,
#         'SATELLITE': {'START': 2, 'END': 3},
#         'PROCESSING_CORRECTION_LEVEL': {'START': 5, 'END': 9},
#         'PATH': {'START': 10, 'END': 13},
#         'ROW': {'START': 13, 'END': 16},
#         'ACQUISITION_DATE': {'START': 17, 'END': 25},
#         'PROCESSING_DATE': {'START': 26, 'END': 34},
#         'COLLECTION_NUMBER': {'START': 35, 'END': 37},
#         'COLLECTION_CATEGORY': {'START': 38, 'END': 40},
#         }


# Following the order of Landsat Identifiers

DELIMITER = '_'
DELIMITER_RE = '(?P<delimiter>_)'
DELIMITER_RE_GROUP = '(?P=delimiter)'
LANDSAT_PREFIX = 'L'
LANDSAT_PREFIX_RE = '(?P<prefix>{prefix})'.format(prefix=LANDSAT_PREFIX)
LANDSAT_PREFIX_RE_GROUP = '(?P<prefix>L)'
SENSORS_PRECOLLECTION = {
        'C': 'OLI/TIRS',
        'E': 'ETM+',
        'T': 'TM',
        'M': 'MSS'
        }
# FIXME: Below: T for TIRS and T for TM!
SENSORS = {
        'C': 'OLI/TIRS',
        'O': 'OLI',
        'T': 'TIRS',
        'E': 'ETM+',
        'TM': 'TM',
        'M': 'MSS'
        }
SENSOR_PRECOLLECTION_RE = '(?P<sensor>[C|T|E|M])'
SENSOR_RE = '(?P<sensor>[C|O|T|E|M])'
SENSOR = {
        'identifiers': ('C', 'T', 'E', 'M'),
        'regular_expression': {
            'Pre-Collection': '(?P<sensor>[C|T|E|M])',
            'Collection 1': '(?P<sensor>[C|O|T|E|M])'
            }
        }
SATELLITES = {
        '01': 'Landsat 1',
        '04': 'Landsat 4',
        '05': 'Landsat 5',
        '07': 'Landsat 7',
        '08': 'Landsat 8'
        }
SATELLITE_PRECOLLECTION_RE = '(?P<satellite>[14578])'
SATELLITE_RE = '(?P<satellite>0[14578])'
PROCESSING_CORRECTION_LEVELS = {
        'L1TP': 'L1TP',
        'L1GT': 'L1GT',
        'L1GS': 'L1GS'
        }
PROCESSING_CORRECTION_LEVEL_RE = '(?P<processing_correction_level>(L1(?:TP|GT|GS)))'
WRS_PATH_ROW_RE = '(?P<path>[012][0-9][0-9])(?P<row>[01][0-9][0-9]|2[0-4][0-3])'
ACQUISITION_YEAR = '(?P<acquisition_year>19|20\\d\\d)'
ACQUISITION_MONTH = '(?P<acquisition_month>0[1-9]|1[012])'
ACQUISITION_DAY = '(?P<acquisition_day>0[1-9]|[12][0-9]|3[01])'
JULIAN_DAY = '(?P<julian_day>[0-2][0-9][0-9]|3[0-6][0-6])'
GROUND_STATION_IDENTIFIER = '(?P<ground_station_identifier>[A-Z][A-Z][A-Z][0-9][0-9])'
PROCESSING_YEAR = '(?P<processing_year>19|20\\d\\d)'
PROCESSING_MONTH = '(?P<processing_month>0[1-9]|1[012])'
PROCESSING_DAY = '(?P<processing_day>0[1-9]|[12][0-9]|3[01])'
COLLECTION_NUMBERS = {
        '01': '01',
        '02': '02'
        }
COLLECTION_NUMBER_RE = '(?P<collection>0[12])'
COLLECTION_CATEGORIES = {
        'RT': 'Real-Time',
        'T1': 'Tier 1',
        'T2': 'Tier 2'
        }
COLLECTION_CATEGORY_RE = '(?P<category>RT|T[1|2])'

MSS123 = {
        'all': (4, 5, 6, 7),
        'visible': (4, 5),
        'infrared': (6, 7)
        }
MSS45 = {
        'all': (1, 2, 3, 4),
        'visible': (1, 2),
        'ndvi': (2, 3),
        'infrared': (3, 4)
        }
LANDSAT_BANDS_ = {
        'oli/tirs': {
            'all': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 'QA'],
            'oli': [1, 2, 3, 4, 5, 6, 7, 8, 9],
            'tirs': [10, 11],
            'visible': [1, 2, 3, 4],
            'ndvi': [4,5],
            'infrared': [5, 6, 7],
            'shortwave': [6, 7],
            'panchromatic': 8,
            'bqa': ['QA']
            },
        'etm+': {
            'all': (1, 2, 3, 4, 5, 6, 7, 8),
            'visible': (1, 2, 3),
            'ndvi': (3, 4),
            'infrared': (4, 5, 7),
            'shortwave': (5, 7),
            'tirs': 6,
            'panchromatic': 8
            },
        'tm': {
            'all': (1, 2, 3, 4, 5, 6, 7),
            'visible': (1, 2, 3),
            'ndvi': (3, 4),
            'infrared': (4, 5, 7),
            'tirs': 6
            },
        'mss1': MSS123,
        'mss2': MSS123,
        'mss3': MSS123,
        'mss4': MSS45,
        'mss5': MSS45
        }
LANDSAT_BANDS = {
        'all': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 'QA'],
        'bqa': ['QA'],
        'oli': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'tirs': [10, 11],
        'coastal': 1,
        'visible': [2, 3, 4],
        'ndvi': [4,5],
        'infrared': [5, 6, 7, 9],
        'panchromatic': 8
        }
BAND_PRECOLLECTION_RE = '[0-9Q][01A]?'
BAND_RE = '[0-9Q][01A]?'
BAND_RE_TEMPLATE = '(?P<band>B{band_pattern})'
GEOTIFF_EXTENSION = '.TIF'

PRECOLLECTION_SCENE_ID = LANDSAT_PREFIX \
        + SENSOR_PRECOLLECTION_RE \
        + SATELLITE_PRECOLLECTION_RE \
        + WRS_PATH_ROW_RE \
        + ACQUISITION_YEAR \
        + JULIAN_DAY \
        + GROUND_STATION_IDENTIFIER
PRECOLLECTION_BAND_TEMPLATE = \
        PRECOLLECTION_SCENE_ID \
        + DELIMITER \
        + BAND_RE_TEMPLATE \
        + GEOTIFF_EXTENSION

COLLECTION_1_SCENE_ID = LANDSAT_PREFIX \
        + SENSOR_RE \
        + SATELLITE_RE \
        + DELIMITER_RE \
        + PROCESSING_CORRECTION_LEVEL_RE \
        + DELIMITER_RE_GROUP \
        + WRS_PATH_ROW_RE \
        + DELIMITER_RE_GROUP \
        + ACQUISITION_YEAR \
        + ACQUISITION_MONTH \
        + ACQUISITION_DAY \
        + DELIMITER_RE_GROUP \
        + PROCESSING_YEAR \
        + PROCESSING_MONTH \
        + PROCESSING_DAY \
        + DELIMITER_RE_GROUP \
        + COLLECTION_NUMBER_RE \
        + DELIMITER_RE_GROUP \
        + COLLECTION_CATEGORY_RE
COLLECTION_1_BAND_TEMPLATE = \
        COLLECTION_1_SCENE_ID \
        + DELIMITER_RE_GROUP \
        + BAND_RE_TEMPLATE \
        + GEOTIFF_EXTENSION

LANDSAT_IDENTIFIERS = {
        'prefix': LANDSAT_PREFIX,
        'sensor': {
            'description': 'Sensor',
            'identifiers': {
                'Collection 1': SENSORS,
                'Pre-Collection': SENSORS_PRECOLLECTION
                },
            'regular_expression': {
                'Collection 1': SENSOR_RE,
                'Pre-Collection': SENSOR_PRECOLLECTION_RE
                }
            },
        'satellite': {
            'description': 'Satellite',
            'identifiers': SATELLITES,
            'regular_expression': {
                'Collection 1': SATELLITE_RE,
                'Pre-Collection': SATELLITE_PRECOLLECTION_RE
                }
            },
        'processing_correction_level': {
            'description': 'Processing correction level',
            'identifiers': PROCESSING_CORRECTION_LEVELS,
            'regular_expression': PROCESSING_CORRECTION_LEVEL_RE
            },
        'wrs_path_row': {
            'description': 'WRS Path and Row',
            'regular_expression': WRS_PATH_ROW_RE,
                },
        'acquisition_date': {
            'description': 'Acquisition date',
            'regular_expression': {
                'year': ACQUISITION_YEAR,
                'month': ACQUISITION_MONTH,
                'day': ACQUISITION_DAY,
                'julian_day': JULIAN_DAY
                },
            },
        'ground_station_identifier': GROUND_STATION_IDENTIFIER,
        'processing_date': {
            'description': 'Processing date',
            'regular_expression': {
                'year': PROCESSING_YEAR,
                'month': PROCESSING_MONTH,
                'day': PROCESSING_DAY
                }
            },
        'collection': {
            'description': 'Collection number',
            'identifiers': COLLECTION_NUMBERS,
            'regular_expression': COLLECTION_NUMBER_RE
            },
        'category': {
            'description': 'Collection category',
            'identifiers': COLLECTION_CATEGORIES,
            'regular_expression': COLLECTION_CATEGORY_RE
            },
        'scene_template': {
            'Collection 1': COLLECTION_1_SCENE_ID,
            'Pre-Collection': PRECOLLECTION_SCENE_ID
            },
        COLLECTION_1_SCENE_ID: 'Collection 1',
        PRECOLLECTION_SCENE_ID: 'Pre-Collection',
        'band_template': {
                'Collection 1': COLLECTION_1_BAND_TEMPLATE,
                'Pre-Collection': PRECOLLECTION_BAND_TEMPLATE
                },
        COLLECTION_1_BAND_TEMPLATE: 'Collection 1',
        PRECOLLECTION_BAND_TEMPLATE: 'Pre-Collection'
        }

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
            g.message(_("No match"))

def get_path_to_cell_misc(mapset):
    """
    Return path to the cell_misc directory inside the requested Mapset
    """
    path_to_cell_misc = '/'.join([GISDBASE, LOCATION, mapset, CELL_MISC])
    return path_to_cell_misc

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
    band_template = identify_product_collection(scene)
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

    return requested_bands


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

def get_name_band(scene, filename):
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
    if one_mapset:
        name = os.path.basename(scene) + '_' + name

    return name, band

def get_metafile(scene, tgis):
    """
    Get metadata MTL filename
    """
    metafile = str()
    if glob.glob(scene + '/*MTL.txt') == []:
        # grass.warning(_("Found an empty scene directory! Passing..."))
        message = "Missing 'MTL' metadata file!"
        message += ' Skipping import process for this scene.'
        grass.fatal(_(message))
        del(message)
        pass
    else:
        metafile = glob.glob(scene + '/*MTL.txt')[0]
        metafile_basename = os.path.basename(metafile)
        scene_basename = os.path.basename(scene)
    return metafile

def is_mtl_in_cell_misc(mapset):
    """
    To implement -- confirm existence of copied MTL in cell_misc instead of
    saying "yes, it's copied" without checking
    """
    cell_misc_directory = get_path_to_cell_misc(mapset)
    globbing = glob.glob(cell_misc_directory + '/' + mapset + '_MTL.txt')

    if not globbing:
        return False

    else:
        return True

def copy_mtl_in_cell_misc(scene, mapset, tgis, copy_mtl=True) :
    """
    Copies the *MTL.txt metadata file in the cell_misc directory inside
    the Landsat scene's independent Mapset or in else the requested single
    Mapset
    """

    if one_mapset:
        mapset = mapset

    path_to_cell_misc = get_path_to_cell_misc(mapset)

    if is_mtl_in_cell_misc(mapset):
        message = HORIZONTAL_LINE
        message += ' MTL exists in: {d}\n'.format(d=path_to_cell_misc)
        message += HORIZONTAL_LINE
        g.message(_(message))
        pass

    else:

        if copy_mtl:

            metafile = get_metafile(scene, tgis)

            # copy the metadata file -- Better: check if really copied!
            message = HORIZONTAL_LINE
            message += ' MTL file copied at <{directory}>.'
            message = message.format(directory=path_to_cell_misc)
            g.message(_(message))
            shutil.copy(metafile, path_to_cell_misc)

        else:
            message = HORIZONTAL_LINE
            message += ' MTL not transferred to {m}/cell_misc'.format(m=scene)
            g.message(_(message))

def validate_date_string(date_string):
    """
    """
    try:
        datetime.strptime(date_string, '%Y-%m-%d')

    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")

def validate_time_string(time_string):
    """
    """
    # if 'Z' in time_string:
    #     time_string = time_string.replace('Z', ' +0000')

    try:
        if '.' in time_string:
            datetime.strptime(time_string, '%H:%M:%S.%f')
        else:
            datetime.strptime(time_string, '%H:%M:%S')

    except ValueError:
        raise ValueError("Incorrect data format, should be HH:MM:SS.ssssss")

def add_leading_zeroes(real_number, n):
     """
     Add leading zeroes to floating point numbers
     Source: https://stackoverflow.com/a/7407943
     """
     bits = real_number.split('.')
     return '{integer}.{real}'.format(integer=bits[0].zfill(n), real=bits[1])

def get_timestamp(scene, tgis):
    """
    Scope:  Retrieve timestamp of a Landsat scene
    Input:  Metadata *MTL.txt file
    Output: Return date, time and timezone of acquisition
    """

    # if set, get time stamp from options
    if options['timestamp']:
        date_time = options['timestamp']
        # date_time_string = options['timestamp']
        # date = validate_date_time_string()
        timestamp_message = "(set manually)"

    else:

        # get metadata file
        metafile = get_metafile(scene, tgis)

        date_time = dict()

        try:
            metadata = open(metafile)

            for line in metadata.readlines():
                line = line.rstrip('\n')

                if len(line) == 0:
                    continue

                # get Date
                if any(x in line for x in DATE_STRINGS):
                    date_time['date'] = line.strip().split('=')[1].strip()
                    validate_date_string(date_time['date'])

                # get Time
                if any(x in line for x in TIME_STRINGS):

                    # remove " from detected line
                    if('\"' in line):
                        line = line.replace('\"', '')

                    # first, zero timezone if 'Z' is the last character
                    if line.endswith('Z'):
                        date_time['timezone'] = ZERO_TIMEZONE

                    # remove 'Z' and split the string before & after ':'
                    time = line.strip().split('=')[1].strip().translate(None, 'Z')

                    # split string, convert to int later -- This Is Not Right
                    hours, minutes, seconds = time.split('.')[0].split(':')

                    if not skip_microseconds:
                        # round microseconds to six digits!
                        microseconds = float(time.split('.')[1])
                        microseconds = round((microseconds / 10000000), 6)

                        # add to seconds
                        seconds = int(seconds)
                        seconds += microseconds
                        seconds = format(seconds, '.6f')
                        seconds = add_leading_zeroes(seconds, 2)

                    if float(seconds) < 10:
                        seconds = seconds.split('.')[0]

                    time = ':'.join([hours, minutes, str(seconds)])
                    validate_time_string(time)
                    time = time.split(':')

                    # create hours, minutes, seconds in date_time dictionary
                    date_time['hours'] = format(int(hours), '02d')
                    date_time['minutes'] = format(int(minutes), '02d')
                    date_time['seconds'] = seconds # float?

        finally:
            metadata.close()

    return date_time

def print_timestamp(scene, timestamp, tgis=False):
    """
    Print out the timestamp
    """
    date = timestamp['date']
    date_Ymd = datetime.strptime(date, "%Y-%m-%d")
    date_tgis = datetime.strftime(date_Ymd, "%d %b %Y")

    hours = str(timestamp['hours'])
    minutes = str(timestamp['minutes'])
    seconds = str(timestamp['seconds'])
    timezone = timestamp['timezone']

    time = ':'.join((hours, minutes, seconds))
    string_parse_time = "%H:%M:%S"
    if '.' not in time:
        time += '.000000'
    if '.' in time:
        string_parse_time += ".%f"
    time = datetime.strptime(time, string_parse_time)
    time = datetime.strftime(time, string_parse_time)

    message = 'Date\t\tTime\n'
    message += '\t{date}\t{time} {timezone}\n\n'

    # if -t requested
    if tgis:

        # verbose if -t instructed
        os.environ['GRASS_VERBOSE'] = GRASS_VERBOSITY_LELVEL_3

        # timezone = timezone.replace('+', '')
        prefix = '<Prefix>'
        if prefix:
            prefix = options['prefix']
        # message = '{p}{s}|{d} {t} {tz}'.format(s=scene, p=prefix, d=date, t=time, tz=timezone)
        message = '{p}{s}|{d} {t}'.format(s=scene, p=prefix, d=date_tgis, t=time)

        # add to timestamps
        if tgis_output:
            global timestamps
            timestamps.append(message)

    if not tgis:
        message = message.format(date=date, time=time, timezone=timezone)
    g.message(_(message))

def set_timestamp(band, timestamp):
    """
    Builds and sets the timestamp (as a string!) for a raster map
    """

    if isinstance(timestamp, dict):

        # year, month, day
        if ('-' in timestamp['date']):
            year, month, day = timestamp['date'].split('-')
        # else, if not ('-' in timestamp['date']): what?

        month = MONTHS[month]

        # assembly
        day_month_year = ' '.join((day, month, year))

        # hours, minutes, seconds
        hours = str(timestamp['hours'])
        minutes = str(timestamp['minutes'])
        seconds = str(timestamp['seconds'])

        # assembly
        hours_minutes_seconds = ':'.join((hours, minutes, seconds))

        # assembly the string
        timestamp = ' '.join((day_month_year, hours_minutes_seconds))
        # timestamp = shlex.quotes(timestamp)  # This is failing in my bash!

    # stamp bands
    grass.run_command('r.timestamp', map=band, date=timestamp, verbose=True)

def import_geotiffs(scene, bands, mapset, memory, list_bands, tgis = False):
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

    timestamp = get_timestamp(scene, tgis)
    print_timestamp(os.path.basename(scene), timestamp, tgis)

    if not one_mapset:
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
        name, band = get_name_band(scene, filename)
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
        copy_mtl_in_cell_misc(scene, mapset, tgis, copy_mtl)

def main():

    global GISDBASE, LOCATION, MAPSET, CELL_MISC
    global link_geotiffs, copy_mtl, override_projection, skip_import, mapset

    # flags
    link_geotiffs = flags['e']
    copy_mtl = not flags['c']
    override_projection = flags['o']
    skip_import = flags['s']
    remove_untarred = flags['r']
    list_bands = flags['l']
    count_scenes = flags['n']

    global skip_microseconds
    skip_microseconds = flags['m']

    global do_not_timestamp
    do_not_timestamp = flags['d']

    tgis = flags['t']

    global force_timestamp
    force_timestamp = flags['f']

    global one_mapset
    one_mapset = flags['1']

    # options
    scene = options['scene']

    # identify product collection
    product_collection = identify_product_collection(scene)
    regular_expression_template = LANDSAT_IDENTIFIERS['band_template'][product_collection]

    pool = options['pool']
    spectral_sets = options['set']

    if options['bands']:
        bands = options['bands'].split(',')
        bands = retrieve_selected_filenames(
                bands,
                scene,
                regular_expression_template)
    else:
        bands = 'all'

    # This will fail is the 'scene=' is a compressed one, i.e. tar.gz # FIXME
    if spectral_sets:
        # bands = list(LANDSAT_BANDS[spectral_set])
        if len(spectral_sets) > 1:
            spectral_sets = options['set'].split(',')

        bands = retrieve_selected_sets_of_bands(
                spectral_sets,
                scene)
        bands = retrieve_selected_filenames(
                bands,
                scene,
                regular_expression_template)

    timestamp = options['timestamp']

    global timestamps
    timestamps = []

    global tgis_output
    tgis_output = options['output_tgis']

    memory = options['memory']

    if list_bands or count_scenes:  # don't import
        os.environ['GRASS_VERBOSE'] = '3'

    # if a single mapset requested
    if one_mapset:
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
                        list_bands,
                        tgis)

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

            import_geotiffs(landsat_scene,
                    bands,
                    mapset,
                    memory,
                    list_bands,
                    tgis)

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
        output_file = file(tgis_output, 'w')

        for timestamp in timestamps:
            timestamp += '\n'
            output_file.write(timestamp)

        output_file.close()
        del(output_file)

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
