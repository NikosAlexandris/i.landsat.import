#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
MODULE:         r.in.landsat  (or i.landsat.import?)

AUTHOR(S):      Martin Landa
                <http://grasswiki.osgeo.org/wiki/LANDSAT#Automated_data_import>

                Nikos Alexandris (handling Landsat 8 data)
                Pietro Zambelli (various improvements)

PURPOSE:        Automated importing of Landsat scenes in GRASS GIS' data base

COPYRIGHT:     (C) 2013 by the GRASS Development Team

                This program is free software under the GNU General Public
                License (>=v2). Read the file COPYING that comes with GRASS
                for details.

ToDo            use grass.warning(_("...")?
"""

#%module
#% description: Imports bands of Landsat scenes in independent Mapsets
#% keywords: imagery
#% keywords: landsat
#% keywords: import
#%end

#%flag
#%  key: o
#%  description: Override projection check
#%end

#%option
#% key: scene
#% key_desc: scene id(s)
#% description: Directory containing one OR multiple Landsat scenes
#% multiple: yes
#% required: yes
#%end

# constants
MONTHS = {'01': 'jan', '02': 'feb', '03': 'mar', '04': 'apr', '05': 'may',
          '06': 'jun', '07': 'jul', '08': 'aug', '09': 'sep', '10': 'oct',
          '11': 'nov', '12': 'dec'}

# globals


# imports
import os
import shutil
import sys
import glob
import grass.script as grass


def run(cmd, **kwargs):
    """Pass quiet flag to grass commands"""
    grass.run_command(cmd, quiet=True, **kwargs)


def copy_metafile(mapset):
    """!Copies the *MTL.txt metadata file in the cell_misc directory inside
    the Landsat scene's independent Mapset"""

    # get the metadata file
    try:
        metafile = glob.glob(mapset + '/*MTL.txt')[0]
        print '\nIdentified metadata file: <%s>.' % metafile.split('/')[1]

    except IndexError:
        return

    # get environment variables & define path to "cell_misc"
    gisenv = grass.gisenv()
    CELL_MISC_DIR = gisenv['GISDBASE'] + \
        '/' + gisenv['LOCATION_NAME'] + '/' + gisenv['MAPSET'] + '/cell_misc'

    # copy the metadata file -- better check if really copied!
    print 'Will copy at: <%s>.\n' % CELL_MISC_DIR
    shutil.copy(metafile, CELL_MISC_DIR)


def get_timestamp(mapset):
    """!Gets the timestamp for each band of a Landsat scene from its metadata
    Returns the date of acquisition for each band of a Landsat scene from
    its metadata file (*MTL.txt)"""

    try:
        metafile = glob.glob(mapset + '/*MTL.txt')[0]

    except IndexError:
        return

    result = dict()
    try:
        fd = open(metafile)

        for line in fd.readlines():
            line = line.rstrip('\n')

            if len(line) == 0:
                continue

            if any(x in line for x in ('DATE_ACQUIRED', 'ACQUISITION_DATE')):
                result['date'] = line.strip().split('=')[1].strip()
    finally:
        fd.close()

    return result


def import_geotiffs(mapset):
    """!Imports all bands (GeoTIF format) of a Landsat scene be it Landsat 5,
    7 or 8.  All known naming conventions are respected, such as "VCID" and
    "QA" found in newer Landsat scenes for temperature channels and Quality
    respectively."""

    # communicate
    grass.message('Importing... \n')  # why is it printed twice?

    # get the timestamp
    meta = get_timestamp(mapset)

    # loop ober files inside a "Landsat" directory
    for file in os.listdir(mapset):

        # if GeoTIFF, keep on working
        if os.path.splitext(file)[-1] != '.TIF':
            continue

        # use the full path name to the file
        ffile = os.path.join(mapset, file)

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
        grass.message('%s -> %s @%s...' % (file, name, mapset))

        # create Mapset of interest
        run('g.mapset', flags='c',
            mapset=mapset,
            stderr=open(os.devnull, 'w'))

        # import bands
        if isinstance(band, str):
            run('r.in.gdal', input=ffile, output=name, title='band %s' % band)

        else:
            run('r.in.gdal', input=ffile, output=name, title='band %d' % band)

        if meta:
            # add timestamp
            year, month, day = meta['date'].split('-')
            run('r.timestamp', map=name,
                date=' '.join((day, MONTHS[month], year)))

    # copy metadata file (MTL)
    copy_metafile(mapset)


def main():

    landsat_scenes = options['scene'].split(',')

    for directory in landsat_scenes:
        import_geotiffs(directory)


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
