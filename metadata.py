import os
import glob
import grass.script as grass
from grass.pygrass.modules.shortcuts import general as g
from constants import HORIZONTAL_LINE

# environment variables
grass_environment = grass.gisenv()
GISDBASE = grass_environment['GISDBASE']
LOCATION = grass_environment['LOCATION_NAME']
CELL_MISC = 'cell_misc'


def get_path_to_cell_misc(mapset):
    """
    Return path to the cell_misc directory inside the requested Mapset
    """
    path_to_cell_misc = '/'.join([GISDBASE, LOCATION, mapset, CELL_MISC])
    return path_to_cell_misc

def get_metafile(scene):
    """
    Get metadata MTL filename
    """
    metafile = str()
    if glob.glob(scene + '/*MTL.txt') == []:
        # grass.warning(_("Found an empty scene directory! Passing..."))
        message = "Missing 'MTL' metadata file!"
        message += f' Skipping import process for scene {scene}.'
        grass.fatal(_(message))
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

def copy_mtl_in_cell_misc(
        scene,
        mapset,
        tgis,
        single_mapset=False,
        copy_mtl=True,
    ):
    """
    Copies the *MTL.txt metadata file in the cell_misc directory inside
    the Landsat scene's independent Mapset or in else the requested single
    Mapset
    """

    if single_mapset:
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

