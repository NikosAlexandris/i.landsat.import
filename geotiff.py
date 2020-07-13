import os
from helpers import run
from identifiers import GEOTIFF_EXTENSION
from metadata import copy_mtl_in_cell_misc
from timestamp import get_timestamp
from timestamp import set_timestamp
from timestamp import build_tgis_timestamp
from timestamp import simple_timestamp
import grass.script as grass
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from bands import get_name_band
from bands import find_existing_band
from bands import sort_band_filenames


def import_geotiffs(
        scene,
        band_filenames,
        mapset,
        memory,
        override_projection=False,
        prefix=None,
        link_geotiffs=False,
        skip_import=True,
        single_mapset=False,
        list_bands=False,
        list_timestamps=False,
        tgis_output=None,
        timestamp=None,
        force_timestamp=False,
        do_not_timestamp=False,
        skip_microseconds=False,
        copy_mtl=True,
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

    band_filenames :
        Bands to import

    mapset :
        Name of mapset to import to

    memory :
        See options for r.in.gdal

    prefix :
        Input scene name prefix string

    single_mapset :
        Import all scenes in a single Mapset

    list_bands :
        Boolean True or False

    list_timestamps :
        Boolean True or False
    """
    if not single_mapset:
        mapset = os.path.basename(scene)

    message = str()
    if not any(x for x in (list_bands, list_timestamps)):
        message = f'Date\t\tTime\t\tTimezone\n{simple_timestamp(timestamp)}'
        message += f'Target Mapset\n@{mapset}\n\n'

    if not list_timestamps:
        message += 'Band\tFilename\n'
        g.message(_(message))

    # loop over files inside a "Landsat" directory
    # sort band numerals, source: https://stackoverflow.com/a/2669523/1172302
    for filename in band_filenames:

        # if not GeoTIFF, keep on working
        if os.path.splitext(filename)[-1] != GEOTIFF_EXTENSION:
            continue

        # use the full path name to the file
        name, band = get_name_band(scene, filename, single_mapset)
        band_title = f'band {band}'

        if not list_timestamps:
            message_overwriting = '\t [ Exists, overwriting]'

            # communicate input band and source file name
            message = f'{band}'
            message += f'\t{filename}'
            if not skip_import:
                g.message(_(message))

            else:
                # message for skipping import
                message_skipping = '\t [ Exists, skipping ]'

        if not any(x for x in (list_bands, list_timestamps)):
            absolute_filename = os.path.join(scene, filename)

            # sort import parameters
            parameters = dict(
                    input = absolute_filename,
                    output = name,
                    flags = '',
                    title = band_title,
                    quiet = True,
            )
            if override_projection:
                parameters['flags'] += 'o'

            # create Mapset of interest, if it doesn't exist
            devnull = open(os.devnull, 'w')
            run(
                    'g.mapset',
                    flags='c',
                    mapset=mapset,
                    stderr = devnull,
            )
            if (
                    skip_import
                    and find_existing_band(name)
                    and not grass.overwrite()
            ):

                if force_timestamp:
                    set_timestamp(name, timestamp)
                    g.message(_(f'   >>> Force-stamp {timestamp} @ band {name}'))

                message_skipping = message + message_skipping
                g.message(_(message_skipping))
                pass

            else:
                if (
                        grass.overwrite()
                        and find_existing_band(name)
                ):
                    if force_timestamp:
                        set_timestamp(name, timestamp)
                        g.message(_(f'   >>> Force-stamp {timestamp} @ band {name}'))

                    message_overwriting = message + message_overwriting
                    g.message(_(message_overwriting))
                    pass

                if (skip_import and not find_existing_band(name)):
                    # FIXME
                    # communicate input band and source file name
                    message = f'{band}\t{filename}'
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
    if not list_bands and not list_timestamps:
        copy_mtl_in_cell_misc(
                scene,
                mapset,
                list_timestamps,
                single_mapset,
                copy_mtl
        )
