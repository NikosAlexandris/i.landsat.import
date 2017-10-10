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
#% description: Imports bands of Landsat scenes (from compressed tar.gz files or unpacked independent directories) in independent Mapsets
#% keywords: imagery
#% keywords: landsat
#% keywords: import
#%end

#%flag
#%  key: o
#%  description: Override projection check
#%end

#%flag
#%  key: s
#%  description: Skip import and continue if band exists
#%end

#%flag
#%  key: r
#%  description: Remove unpacked scene directory after import if source is a tar.gz file
#%end

#%flag
#%  key: l
#%  description: List bands but do not import
#%end

#%flag
#%  key: t
#%  description: t.register compliant list of scene names and their timestamp, one per line
#%end

#%flag
#%  key: n
#%  description: Number of scenes in pool
#%end

#%option
#% key: scene
#% key_desc: name
#% description: Directory containing one or multiple Landsat scenes (compressed tar.gz files)
#% multiple: yes
#% required: no
#%end

#%rules
#% requires_all: -r, scene
#%end

#%option
#% key: pool
#% key_desc: directory
#% description: Directory containing multiple decompressed Landsat scenes as independent directories
#% multiple: no
#% required: no
#%end

#%option
#% key: timestamp
#% key_desc: Time stamp
#% type: string
#% label: Manual definition of a time stamp
#% description: Timestamp for bands of a Landsat scene
#% required: no
#%end

#%option
#%  key: tgis
#%  key_desc:
#%  label: File for t.register
#%  description: Scene names and their timestamp
#%  multiple: no
#%  required: no
#%end

# required librairies
import os
import sys
import shutil
import tarfile
import glob
# import shlex
import atexit
import grass.script as grass
from grass.pygrass.modules.shortcuts import general as g

# globals
MONTHS = {'01': 'jan', '02': 'feb', '03': 'mar', '04': 'apr', '05': 'may',
          '06': 'jun', '07': 'jul', '08': 'aug', '09': 'sep', '10': 'oct',
          '11': 'nov', '12': 'dec'}

# environment variables
gisenv = grass.gisenv()

# path to "cell_misc"
CELL_MISC_DIR = gisenv['GISDBASE'] + \
          '/' + gisenv['LOCATION_NAME'] + \
          '/' + gisenv['MAPSET'] + \
          '/cell_misc'

# helper functions
def run(cmd, **kwargs):
    """
    Pass quiet flag to grass commands
    """
    grass.run_command(cmd, quiet=True, **kwargs)

def find_existing_band(band):
    """
    Check if band exists in the current mapset

    Parameter "element": 'raster', 'raster_3d', 'vector'
    """

    result = grass.find_file(name=band, element='cell', mapset='.')
    if result['file']:
        grass.verbose(_("Band {band} exists".format(band=band)))
        return True

    else:
        return False

def import_raster(raster, name, band):
    """
    """
    run('r.in.gdal', flags='o', input=raster, output=name, title='band {band}'.format(band=band))
    pass


def extract_tgz(tgz):
    """
    Decompress and unpack a .tgz file
    """

    g.message('Extracting files from tar.gz file')

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


def get_metafile(scene, tgis, **kwargs):
    """
    Get metadata MTL filename
    """

    metafile = glob.glob(scene + '/*MTL.txt')[0]

    if not tgis:
        message = '\n'
        message += ('Scene\t\t\tMetafile\n\n')
        metafile_basename = os.path.basename(metafile)
        scene_basename = os.path.basename(scene)
        message += ('{scene}\t{mtl}\n\n'.format(scene=scene_basename, mtl=metafile_basename))
        g.message(_(message, **kwargs))

    return metafile

def search_cell_misc():
    """
    To implement -- confirm existence of copied MTL in cell_misc instead of
    saying "yes, it's copied" without checking
    """
    pass

def copy_metafile(metafile):
    """
    Copies the *MTL.txt metadata file in the cell_misc directory inside
    the Landsat scene's independent Mapset
    """

    # copy the metadata file -- Better: check if really copied!
    message = 'Meta file copied at <{cell_misc_directory}>.\n'
    message = message.format(cell_misc_directory=CELL_MISC_DIR)
    g.message(message)
    shutil.copy(metafile, CELL_MISC_DIR)

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
                if any(x in line for x in ('DATE_ACQUIRED', 'ACQUISITION_DATE')):
                    date_time['date'] = line.strip().split('=')[1].strip()

                # get Time
                if ('SCENE_CENTER_TIME' in line):

                    # remove " from detected line
                    if('\"' in line):
                        line = line.replace('\"', '')

                    # first, zero timezone if 'Z' is the last character
                    if line.endswith('Z'):
                        date_time['timezone'] = '+0000'

                    # remove 'Z' and split the string before & after ':'
                    time = line.strip().split('=')[1].strip().translate(None, 'Z').split(':')

                    # create hours, minutes, seconds in date_time dictionary
                    date_time['hours'] = format(int(time[0]), '02d')
                    date_time['minutes'] = format(int(time[1]), '02d')
                    date_time['seconds'] = add_leading_zeroes(time[2], 2) # float?

        finally:
            metadata.close()

    return date_time

def print_timestamp(scene, timestamp, tgis=False):
    """
    """
    date = timestamp['date']
    hours = str(timestamp['hours'])
    minutes = str(timestamp['minutes'])
    seconds = str(timestamp['seconds'])
    timezone = timestamp['timezone']
    time = ':'.join((hours, minutes, seconds))

    message = 'Time\t\t\tDate\n\n{time} {timezone}\t{date}\n\n'

    # if -t requested
    if tgis:

        # timezone = timezone.replace('+', '')
        message = '{scene}<Suffix>|{date} {time} {timezone}'.format(date=date, scene=scene, time=time, timezone=timezone)

    g.message(message.format(date=date, time=time, timezone=timezone))

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
    run('r.timestamp', map=band, date=timestamp)

def import_geotiffs(scene, list_only, tgis=False):
    """
    Imports all bands (GeoTIF format) of a Landsat scene be it Landsat 5,
    7 or 8.  All known naming conventions are respected, such as "VCID" and
    "QA" found in newer Landsat scenes for temperature channels and Quality
    respectively.
    """

    # get time stamp
    timestamp = get_timestamp(scene, tgis)

    # print it
    print_timestamp(os.path.basename(scene), timestamp, tgis)

    # set mapset from scene name
    mapset = os.path.basename(scene)

    message = str()

    # print target mapset
    if not tgis:
        message = 'Target Mapset\t@{mapset}\n\n'.format(mapset=mapset)

    if list_only:
        message = ('List of bands without importing\n\n')
    print "GRASS_VERBOSE:", os.environ['GRASS_VERBOSE']

    # communicate input band name
    if not tgis:
        message += 'Band\tFilename\n'
        g.message(message)

    # loop over files inside a "Landsat" directory
    for filename in os.listdir(scene):

        # if not GeoTIFF, keep on working
        if os.path.splitext(filename)[-1] != '.TIF':
            continue

        # use the full path name to the file
        absolute_filename = os.path.join(scene, filename)

        # detect QA or VCID strings
        if any(string in absolute_filename for string in ('QA', 'VCID')):
            name = "".join((os.path.splitext(absolute_filename)[0].split('_'))[1::2])

        else:
            name = os.path.splitext(filename)[0].split('_')[-1]

        # found a wrongly named *MTL.TIF file in LE71610432005160ASN00
        if ('MTL') in absolute_filename:  # use grass.warning(_("...")?
            g.message(_("Found a wrongly named *MTL.TIF file!", flags='w'))
            grass.fatal(_("Please, rename the extension to .txt and retry."))
            break

        elif ('QA') in absolute_filename:
            band = name

        elif len(name) == 3 and name[0] == 'B' and name[-1] == '0':
            band = int(name[1:3])

        elif len(name) == 3 and name[-1] == '0':
            band = int(name[1:2])

        elif len(name) == 3 and name[-1] != '0':
            band = int(name[1:3])

        else:
            band = int(name[-1:])


        if not tgis:
            # # communicate input band name
            message = '{name}'.format(name=name)
            # g.message(message)

            # communicate source
            message += '\t{filename}\n'
            message = message.format(filename=filename)
            g.message(message)

        if not any(x for x in (list_only, tgis)):

            # verbosity?
            g.message(_('Importing...', flags='v')

            # create Mapset of interest
            run('g.mapset', flags='c', mapset=mapset, stderr=open(os.devnull, 'w'))

            # import BQA band
            if isinstance(band, str):

                override_projection = flags['o']
                if override_projection:
                    run('r.in.gdal', flags='o',
                            input=absolute_filename, output=name,
                            title='band {band}'.format(band=band))

                else:

                    skip_import=flags['s']
                    if (skip_import and find_existing_band(name)):

                        g.message(_(">>> Skipping import of already existing band {b}".format(b=band)))
                        pass

                    else:
                        run('r.in.gdal',
                            input=absolute_filename, output=name,
                            title='band {band}'.format(band=band))

            # import band
            else:

                skip_import=flags['s']

                if (skip_import and find_existing_band(name)):

                    g.message(_(">>> Skipping import of already existing band {b}".format(b=band)))
                    pass

                else:
                    run('r.in.gdal',
                            input=absolute_filename, output=name,
                            title='band {band}'.format(band=band))

            # set date & time
            set_timestamp(name,timestamp)

        else:
            pass


def main():

    # flags
    remove_untarred = flags['r']
    list_only = flags['l']
    number_of_scenes = flags['n']
    temporal_register = flags['t']


    if list_only:  # don't import
        os.environ['GRASS_VERBOSE'] = '3'

    if options['pool']:
        pool = options['pool']
        scenes = [x[0] for x in os.walk(pool)][1:]

        if number_of_scenes:
            g.message(_("Number of scenes in pool: {n}".format(n=len(scenes))))

        else:
            for scene in scenes:
                import_geotiffs(scene, list_only, temporal_register)

    if options['scene']:
        landsat_scenes = options['scene'].split(',')

        for scene in landsat_scenes:
            if 'tar.gz' in scene:
                extract_tgz(scene)
                scene = scene.split('.tar.gz')[0]

            # import
            import_geotiffs(scene, list_only, temporal_register)

            if remove_untarred:
                g.message('Removing unpacked source directory {scene}'.format(scene=scene))
                shutil.rmtree(scene)

    # copy metadata file (MTL)
    if not list_only and not temporal_register:
        metafile = get_metafile(scene, temporal_register, quiet=True)
        copy_metafile(metafile)


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
