#!/usr/bin/python
# -*- coding: utf-8 -*-

# Following the order of Landsat Identifiers

# scene and product identifiers, regular expression patterns and templates

# LANDSAT_PRODUCT_IDENTIFIER = {
#         'PREFIX': 0,
#         'SENSOR': 1,
#         'SATELLITE': {'START': 2, 'END': 3},
#         'PROCESSING_CORRECTION_LEVEL': {'START': 5, 'END': 9},
#         'PATH': {'START': 10, 'END': 13},
#         'ROW': {'START': 13, 'END': 16},
#         'ACQUISITION_DATE': {'START': 17, 'END': 25},
#         'PROCESSING_DATE': {'START': 26, 'END': 34},
#         'COLLECTION_NUMBER': {'START': 35, 'END': 37},
#         'COLLECTION_CATEGORY': {'START': 38, 'END': 40},
#         }

DELIMITER = '_'
DELIMITER_RE = '(?P<delimiter>_)'
DELIMITER_RE_GROUP = '(?P=delimiter)'
LANDSAT_PREFIX = 'L'
LANDSAT_PREFIX_RE = '(?P<prefix>{prefix})'.format(prefix=LANDSAT_PREFIX)
LANDSAT_PREFIX_RE_GROUP = '(?P<prefix>L)'
SENSORS_PRECOLLECTION = {
        'C': 'OLI/TIRS',
        'E': 'ETM+',
        'M': 'TM',
        'S': 'MSS'
        }
# FIXME: Below: T for TIRS and T for TM!
SENSORS = {
        'C': 'OLI/TIRS',
        'O': 'OLI',
        'T': 'TIRS',
        'E': 'ETM+',
        'M': 'TM',
        'S': 'MSS'
        }
SENSOR_PRECOLLECTION_RE = '(?P<sensor>[C|E|M|S])'
SENSOR_RE = '(?P<sensor>[C|O|T|E|S])'
SENSOR = {
        'identifiers': ('C', 'T', 'E', 'M'),
        'regular_expression': {
            'Pre-Collection': '(?P<sensor>[C|T|M|S])',
            'Collection 1': '(?P<sensor>[C|O|T|E|S])'
            }
        }
SATELLITES = {
        '01': 'Landsat 1',
        '04': 'Landsat 4',
        '05': 'Landsat 5',
        '07': 'Landsat 7',
        '08': 'Landsat 8'
        }
SATELLITE_PRECOLLECTION_RE = '(?P<satellite>[14578])'
SATELLITE_RE = '(?P<satellite>0[14578])'
PROCESSING_CORRECTION_LEVELS = {
        'L1TP': 'L1TP',
        'L1GT': 'L1GT',
        'L1GS': 'L1GS'
        }
PROCESSING_CORRECTION_LEVEL_RE = '(?P<processing_correction_level>(L1(?:TP|GT|GS)))'
WRS_PATH_ROW_RE = '(?P<path>[012][0-9][0-9])(?P<row>[01][0-9][0-9]|2[0-4][0-3])'
ACQUISITION_YEAR = '(?P<acquisition_year>19|20\\d\\d)'
ACQUISITION_MONTH = '(?P<acquisition_month>0[1-9]|1[012])'
ACQUISITION_DAY = '(?P<acquisition_day>0[1-9]|[12][0-9]|3[01])'
JULIAN_DAY = '(?P<julian_day>[0-2][0-9][0-9]|3[0-6][0-6])'
GROUND_STATION_IDENTIFIER = '(?P<ground_station_identifier>[A-Z][A-Z][A-Z][0-9][0-9])'
PROCESSING_YEAR = '(?P<processing_year>19|20\\d\\d)'
PROCESSING_MONTH = '(?P<processing_month>0[1-9]|1[012])'
PROCESSING_DAY = '(?P<processing_day>0[1-9]|[12][0-9]|3[01])'
COLLECTION_NUMBERS = {
        '01': '01',
        '02': '02'
        }
COLLECTION_NUMBER_RE = '(?P<collection>0[12])'
COLLECTION_CATEGORIES = {
        'RT': 'Real-Time',
        'T1': 'Tier 1',
        'T2': 'Tier 2'
        }
COLLECTION_CATEGORY_RE = '(?P<category>RT|T[1|2])'

MSS123 = {
        'all': (4, 5, 6, 7),
        'visible': (4, 5),
        'infrared': (6, 7)
        }
MSS45 = {
        'all': (1, 2, 3, 4),
        'visible': (1, 2),
        'ndvi': (2, 3),
        'infrared': (3, 4)
        }
LANDSAT_BANDS_ = {
        'oli/tirs': {
            'all': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 'QA'],
            'oli': [1, 2, 3, 4, 5, 6, 7, 8, 9],
            'tirs': [10, 11],
            'visible': [1, 2, 3, 4],
            'ndvi': [4,5],
            'infrared': [5, 6, 7],
            'shortwave': [6, 7],
            'panchromatic': 8,
            'bqa': ['QA']
            },
        'etm+': {
            'all': (1, 2, 3, 4, 5, 6, 7, 8),
            'visible': (1, 2, 3),
            'ndvi': (3, 4),
            'infrared': (4, 5, 7),
            'shortwave': (5, 7),
            'tirs': 6,
            'panchromatic': 8
            },
        'tm': {
            'all': (1, 2, 3, 4, 5, 6, 7),
            'visible': (1, 2, 3),
            'ndvi': (3, 4),
            'infrared': (4, 5, 7),
            'tirs': 6
            },
        'mss1': MSS123,
        'mss2': MSS123,
        'mss3': MSS123,
        'mss4': MSS45,
        'mss5': MSS45
        }
LANDSAT_BANDS = {
        'all': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 'QA'],
        'bqa': ['QA'],
        'oli': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'tirs': [10, 11],
        'coastal': 1,
        'visible': [2, 3, 4],
        'ndvi': [4,5],
        'infrared': [5, 6, 7, 9],
        'panchromatic': 8
        }
BAND_PRECOLLECTION_RE = '[0-9Q][01A]?'
BAND_RE = '[0-9Q][01A]?'
BAND_RE_TEMPLATE = '(?P<band>B{band_pattern})'
GEOTIFF_EXTENSION = '.TIF'

PRECOLLECTION_SCENE_ID = LANDSAT_PREFIX \
        + SENSOR_PRECOLLECTION_RE \
        + SATELLITE_PRECOLLECTION_RE \
        + WRS_PATH_ROW_RE \
        + ACQUISITION_YEAR \
        + JULIAN_DAY \
        + GROUND_STATION_IDENTIFIER
PRECOLLECTION_BAND_TEMPLATE = \
        PRECOLLECTION_SCENE_ID \
        + DELIMITER \
        + BAND_RE_TEMPLATE \
        + GEOTIFF_EXTENSION

COLLECTION_1_SCENE_ID = LANDSAT_PREFIX \
        + SENSOR_RE \
        + SATELLITE_RE \
        + DELIMITER_RE \
        + PROCESSING_CORRECTION_LEVEL_RE \
        + DELIMITER_RE_GROUP \
        + WRS_PATH_ROW_RE \
        + DELIMITER_RE_GROUP \
        + ACQUISITION_YEAR \
        + ACQUISITION_MONTH \
        + ACQUISITION_DAY \
        + DELIMITER_RE_GROUP \
        + PROCESSING_YEAR \
        + PROCESSING_MONTH \
        + PROCESSING_DAY \
        + DELIMITER_RE_GROUP \
        + COLLECTION_NUMBER_RE \
        + DELIMITER_RE_GROUP \
        + COLLECTION_CATEGORY_RE
COLLECTION_1_BAND_TEMPLATE = \
        COLLECTION_1_SCENE_ID \
        + DELIMITER_RE_GROUP \
        + BAND_RE_TEMPLATE \
        + GEOTIFF_EXTENSION

LANDSAT_IDENTIFIERS = {
        'prefix': LANDSAT_PREFIX,
        'sensor': {
            'description': 'Sensor',
            'identifiers': {
                'Collection 1': SENSORS,
                'Pre-Collection': SENSORS_PRECOLLECTION
                },
            'regular_expression': {
                'Collection 1': SENSOR_RE,
                'Pre-Collection': SENSOR_PRECOLLECTION_RE
                }
            },
        'satellite': {
            'description': 'Satellite',
            'identifiers': SATELLITES,
            'regular_expression': {
                'Collection 1': SATELLITE_RE,
                'Pre-Collection': SATELLITE_PRECOLLECTION_RE
                }
            },
        'processing_correction_level': {
            'description': 'Processing correction level',
            'identifiers': PROCESSING_CORRECTION_LEVELS,
            'regular_expression': PROCESSING_CORRECTION_LEVEL_RE
            },
        'wrs_path_row': {
            'description': 'WRS Path and Row',
            'regular_expression': WRS_PATH_ROW_RE,
                },
        'acquisition_date': {
            'description': 'Acquisition date',
            'regular_expression': {
                'year': ACQUISITION_YEAR,
                'month': ACQUISITION_MONTH,
                'day': ACQUISITION_DAY,
                'julian_day': JULIAN_DAY
                },
            },
        'ground_station_identifier': GROUND_STATION_IDENTIFIER,
        'processing_date': {
            'description': 'Processing date',
            'regular_expression': {
                'year': PROCESSING_YEAR,
                'month': PROCESSING_MONTH,
                'day': PROCESSING_DAY
                }
            },
        'collection': {
            'description': 'Collection number',
            'identifiers' : COLLECTION_NUMBERS,
            'regular_expression': COLLECTION_NUMBER_RE
            },
        'category': {
            'description': 'Collection category',
            'identifiers': COLLECTION_CATEGORIES,
            'regular_expression': COLLECTION_CATEGORY_RE
            },
        'scene_template': {
            'Collection 1': COLLECTION_1_SCENE_ID,
            'Pre-Collection': PRECOLLECTION_SCENE_ID
            },
        COLLECTION_1_SCENE_ID: 'Collection 1',
        PRECOLLECTION_SCENE_ID: 'Pre-Collection',
        'band_template': {
                'Collection 1': COLLECTION_1_BAND_TEMPLATE,
                'Pre-Collection': PRECOLLECTION_BAND_TEMPLATE
                },
        COLLECTION_1_BAND_TEMPLATE: 'Collection 1',
        PRECOLLECTION_BAND_TEMPLATE: 'Pre-Collection'
        }
