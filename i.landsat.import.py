#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
 MODULE:       i.landsat.import

 AUTHOR(S):    Nikos Alexandris <nik@nikosalexandris.net>
               Based on a python script published in GRASS-Wiki

 PURPOSE:      Import Landsat scenes in GRASS' data base

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
#%  key: r
#%  description: If input is a tar.gz file, remove unpacked scene directory after import completion
#%end

#%flag
#%  key: p
#%  description: Pretend what *would* have been imported if -p weren't used.
#%end

#%option
#% key: scene
#% key_desc: name
#% description: Directory containing one or multiple Landsat scenes (compressed tar.gz files)
#% multiple: yes
#% required: no
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

# required librairies
import os
import sys
import shutil
import tarfile
import glob
import grass.script as grass

# globals
MONTHS = {'01': 'jan', '02': 'feb', '03': 'mar', '04': 'apr', '05': 'may',
          '06': 'jun', '07': 'jul', '08': 'aug', '09': 'sep', '10': 'oct',
          '11': 'nov', '12': 'dec'}


# helper functions
def run(cmd, **kwargs):
    """
    Pass quiet flag to grass commands
    """
    grass.run_command(cmd, quiet=True, **kwargs)


def extract_tgz(tgz):
    """
    Decompress and unpack a .tgz file
    """

    # open tar.gz file in read mode
    tar = tarfile.TarFile.open(name=tgz, mode='r')

    # create a directory with the scene's (base)name
    tgz_base = os.path.basename(tgz).split('.tar.gz')[0]

    # try to create a directory with the landsat's scene (base)name
    # source: <http://stackoverflow.com/a/14364249/1172302>
    try:
        os.makedirs(tgz_base)

    # if something went wrong, then raise error
    except OSError:
        if not os.path.isdir(tgz_base):
            raise

    # extract files indide the scene directory
    tar.extractall(path=tgz_base)


def get_metafile(scene):
    """
    """
    metafile = glob.glob(scene + '/*MTL.txt')[0]
    # grass.message('\n | Metadata file: <%s>.' % metafile.split('/')[1])
    # grass.message('\nIdentified metadata file: <%s>.' % metafile)

    return metafile


def copy_metafile(scene):
    """
    Copies the *MTL.txt metadata file in the cell_misc directory inside
    the Landsat scene's independent Mapset
    """

    # get metadata file
    metafile = get_metafile(scene)

    # get environment variables & define path to "cell_misc"
    gisenv = grass.gisenv()

    CELL_MISC_DIR = gisenv['GISDBASE'] + \
        '/' + gisenv['LOCATION_NAME'] + '/' + gisenv['MAPSET'] + '/cell_misc'

    # copy the metadata file -- Better: check if really copied!
    print 'Will copy at: <%s>.\n' % CELL_MISC_DIR
    shutil.copy(metafile, CELL_MISC_DIR)


def get_timestamp(scene):
    """
    Scope:  Retrieve timestamp of a Landsat scene
    Input:  Metadata *MTL.txt file
    Output: Return date, time and timezone of acquisition
    """

    # if set, get time stamp from options
    if options['timestamp']:
        date_time = options['timestamp']

    else:

        # get metadata file
        metafile = get_metafile(scene)

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

                    # first, zero timezone if 'Z' is the last character
                    if line.endswith('Z'):
                        date_time['timezone'] = '+0000'

                    # remove 'Z' and split the string before & after ':'
                    time = line.strip().split('=')[1].strip().translate(None, 'Z').split(':')

                    # create hours, minutes, seconds in date_time dictionary
                    date_time['hours'] = int(time[0])
                    date_time['minutes'] = int(time[1])
                    date_time['seconds'] = float(time[2])

        finally:
            metadata.close()

    return date_time


def set_timestamp(band, timestamp):
    """
    """

    if isinstance(timestamp, dict):

        # year, month, day
        if ('-' in timestamp['date']):
            year, month, day = timestamp['date'].split('-')
        month = MONTHS[month]

        dmy = ' '.join((day, month, year))

        # hours, minutes, seconds
        hours = str(timestamp['hours'])
        minutes = str(timestamp['minutes'])
        seconds = str(timestamp['seconds'])

        # r.timestamp does not tolerate single-digit seconds!
        if len(seconds.split('.')[0]) == 1:
            seconds = '0' + seconds

        hrs = ':'.join((hours, minutes, seconds))

        # assembly the string
        timestamp =' '.join((dmy, hrs))

    # stamp bands
    run('r.timestamp', map=band, date=timestamp)
    # grass.message( "| Time stamp " + timestamp_message)


def import_geotiffs(scene):
    """
    Imports all bands (GeoTIF format) of a Landsat scene be it Landsat 5,
    7 or 8.  All known naming conventions are respected, such as "VCID" and
    "QA" found in newer Landsat scenes for temperature channels and Quality
    respectively.
    """

    # communicate
    grass.message('Importing... \n')  # why is it printed twice?

    # get time stamp
    timestamp = get_timestamp(scene)

    # loop over files inside a "Landsat" directory
    for file in os.listdir(scene):

        # if not GeoTIFF, keep on working
        if os.path.splitext(file)[-1] != '.TIF':
            continue

        # use the full path name to the file
        ffile = os.path.join(scene, file)

        # if correctly handled below, use the "any" instruction!
        if ('QA') or ('VCID') in ffile:
            name = "".join((os.path.splitext(file)[0].split('_'))[1::2])

        else:
            name = os.path.splitext(file)[0].split('_')[-1]

        # found a wrongly named *MTL.TIF file in LE71610432005160ASN00
        if ('MTL') in ffile:  # use grass.warning(_("...")?
            grass.message(_("Found a wrongly named *MTL.TIF file!", flags='w'))
            grass.fatal(_("Please rename the extension to .txt"))
            break

        elif ('QA') in ffile:
            band = name

        elif len(name) == 3 and name[-1] == '0':
            band = int(name[1:2])

        elif len(name) == 3 and name[-1] != '0':
            band = int(name[1:3])

        else:
            band = int(name[-1:])

        # communicate
        grass.message('Band name: %s' % (name))
        mapset = os.path.basename(scene)
        grass.message('   %s -> %s @%s' % (file, name, mapset))

        pretend = flags['p']
        if not pretend:

            # create Mapset of interest
            run('g.mapset', flags='c', mapset=mapset, stderr=open(os.devnull, 'w'))

            # import bands
            if isinstance(band, str):

                override_projection = flags['o']
                if override_projection:
                    run('r.in.gdal', input=ffile, output=name,
                        title='band %s' % band)

                else:
                    run('r.in.gdal', flags='o',
                        input=ffile, output=name, title='band %s' % band)

            else:
                run('r.in.gdal', input=ffile, output=name, title='band %d' % band)

            # set date & time
            set_timestamp(name,timestamp)

    # copy metadata file (MTL)
    copy_metafile(scene)

    # communicate
    grass.message('Scene imported in %s' % mapset)
    if options['timestamp']:
        timestamp_message = "set manually"
    timestamp_message = "retrieved from metadata"
    grass.message('with timestamp %s' % timestamp)


def main():

    # flags
    remove_untarred = flags['r']

    if options['pool']:
        pool = options['pool']

        for directory in filter(os.path.isdir, os.listdir(pool)):
            import_geotiffs(directory)

    if options['scene']:
        landsat_scenes = options['scene'].split(',')

        for scene in landsat_scenes:
            if 'tar.gz' in scene:
                grass.message('Extracting files from tar.gz file')
                extract_tgz(scene)
                scene = scene.split('.tar.gz')[0]

                import_geotiffs(scene)

                if remove_untarred:
                    grass.message('Removing directory %s' % scene)
                    shutil.rmtree(scene)

            else:
                import_geotiffs(scene)


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
