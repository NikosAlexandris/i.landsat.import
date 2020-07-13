MODULE_TOPDIR = ../..

PGM = i.landsat.import

ETCFILES = bands constants geotiff helpers identifiers identify metadata messages tar timestamp

include $(MODULE_TOPDIR)/include/Make/Script.make
include $(MODULE_TOPDIR)/include/Make/Python.make

default: script
