from constants import IMAGE_QUALITY_STRINGS
from constants import QA_STRING
from constants import MTL_STRING
from identifiers import LANDSAT_BANDS
from identifiers import LANDSAT_IDENTIFIERS
from messages import MESSAGE_UNKNOWN_LANDSAT_IDENTIFIER
import os
import glob
import re
import grass.script as grass
from identify import identify_product_collection


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

def match_band_filenames(bands, scene):
    """
    Retrieve filenames of user requested bands from a Landsat scene

    To Do
    -----
    Fix: requires a fix for 'tar.gz' files, i.e. if 'scene' = '*.tar.gz'!

    Parameters
    ----------
    bands :
        List of user requested bands

    scene :
        Landsat scene directory

    Returns
    -------
        Returns list of filenames of user requested bands

    Example
    -------
        ...
    """
    product_collection = identify_product_collection(os.path.basename(scene))
    try:
        regular_expression_template = LANDSAT_IDENTIFIERS['band_template'][product_collection]
    except:
        grass.fatal(_(MESSAGE_UNKNOWN_LANDSAT_IDENTIFIER.format(scene=scene)))

    band_template = identify_product_collection(os.path.basename(scene))
    requested_filenames = []
    for band in bands:
        for filename in os.listdir(scene):
            template = regular_expression_template.format(band_pattern=band)
            pattern = re.compile(template)
            if pattern.match(filename):
                absolute_filename = scene + '/' + filename
                requested_filename = os.path.basename(glob.glob(absolute_filename)[0])
                requested_filenames.append(requested_filename)
    # print "Requested bands:"
    # print('\n'.join(map(str, requested_bands)))
    return sort_band_filenames(requested_filenames)

def retrieve_band_filenames(
        bands,
        spectral_sets,
        scene,
    ):
    """
    """
    # This will fail if the 'scene=' is a compressed one, i.e. tar.gz # FIXME
    if bands == [''] and spectral_sets == ['']:
        spectral_sets = ['all']

    if not spectral_sets == ['']:
        band_subset = list_band_sets(
                        spectral_sets,
                        scene,
                    )
        bands.extend(band_subset)

    band_filenames = match_band_filenames(
                bands=bands,
                scene=scene,
            )
    return band_filenames

def list_band_sets(spectral_sets, scene):
    """
    """
    requested_bands = []
    for spectral_set in spectral_sets:
        bands = list(LANDSAT_BANDS[spectral_set])
        requested_bands.extend(bands)
    return list(set(requested_bands))

def sort_band_filenames(band_filenames):
    """
    """
    filenames = sorted(band_filenames, key=lambda item:
            (int(item.partition('_B')[2].partition('.')[0])
                if item.partition('_B')[2].partition('.')[0].isdigit()
                else float('inf'), item))
    return filenames

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
        grass.fatal(message_fatal)

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
