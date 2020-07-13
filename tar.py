import os
import tarfile
from grass.pygrass.modules.shortcuts import general as g


def list_files_in_tar(tgz):
    """List files in tar.gz file"""
    compressed_scene = os.path.basename(tgz)
    g.message(_(f'Reading compressed scene \'{compressed_scene}\'...'))
    tar = tarfile.TarFile.open(name=tgz, mode='r')
    members = tar.getnames()
    members = """
    {}
    """.format('\n'.join(members[1:]))
    index_of_dot = compressed_scene.index('.')
    scene = compressed_scene[:index_of_dot]
    message = f'List of files in {scene}'
    message += members
    g.message(_(message))

def extract_tgz(tgz):
    """
    Decompress and unpack a .tgz file
    """
    tar = tarfile.TarFile.open(name=tgz, mode='r')
    tgz_base = os.path.basename(tgz).split('.tar.gz')[0]

    # try to create a directory with the scene's (base)name
    # source: <http://stackoverflow.com/a/14364249/1172302>
    try:
        os.makedirs(tgz_base)

    except OSError:
        if not os.path.isdir(tgz_base):
            raise

    # extract files indide the scene directory
    compressed_scene = os.path.basename(tgz)
    g.message(_(f'Extracting files from compressed_scene {compressed_scene}'))
    tar.extractall(path=tgz_base)
