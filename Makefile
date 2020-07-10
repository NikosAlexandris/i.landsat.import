MODULE_TOPDIR = ../..

PGM = i.landsat.import

ETCFILES = constants identifiers metadata

include $(MODULE_TOPDIR)/include/Make/Script.make
include $(MODULE_TOPDIR)/include/Make/Python.make

default: script
