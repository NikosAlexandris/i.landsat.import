#!/usr/bin/python\<nl>\
# -*- coding: utf-8 -*-

"""
@author Nikos Alexandris |
"""

MAPSET='LC81840332014146LGN00'

import glob

def get_date_time(mapset):
    """
    Scope:  Retrieve timestamp of a Landsat scene
    Input:  Metadata *MTL.txt file 
    Output: Return time, timezone and date of acquisition
    """

    try:
        metafile = glob.glob(mapset + '/example*MTL.txt')[0]

    except IndexError:
        print "Error?"
        return

    print metafile

get_date_time(MAPSET)

