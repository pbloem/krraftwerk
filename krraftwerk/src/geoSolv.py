#!/usr/bin/env python3

import os
import re
import requests


COUNTRY_ISO_TABLE = '../geonames/countryInfo.txt'
GEONAMES_USERNAME = 'me'
GEONAMES_API_URI = 'http://api.geonames.org/search?username=' + GEONAMES_USERNAME
GEONAMES_BASE_URI = 'http://www.geonames.org/'

class GeoIndex():
    def __init__(self):
        self.isoIndex = dict()
        self.placeGeonamesIndex = dict()
        self.importISOTable(COUNTRY_ISO_TABLE)

    def resolve(self, location=''):
        geoURI = None

        if location == '':
            return None

        # prevent unnecessary lookups
        if location in self.placeGeonamesIndex:
            return self.placeGeonamesIndex[location]

        # get correct format for API call parameters
        place, country = location.split(', ')
        isoCode = self.isoIndex[country] if country in self.isoIndex else None
        if isoCode is None:
            return None

        # generate and execute API call
        apiCall = self.generateGeonamesAPICall(isoCode, place)
        r = requests.get(apiCall)

        # assume first record is the one we want
        terms = r.text.split('geonameId')
        if len(terms) < 3:
            # something wrong in returned data
            return None

        # extract ID
        geoId = re.sub(r'>([0-9]*)</', r'\1', terms[1]) # geoname ID

        # generate URI
        geoURI = self.generateGeonamesURI(geoId)

        # store URI for future use
        self.placeGeonamesIndex[location] = geoURI

        return geoURI


    def generateGeonamesURI(self, geonameId):
        return GEONAMES_BASE_URI + geonameId + '/about.rdf'

    def generateGeonamesAPICall(self, country='', place=''):
        return GEONAMES_API_URI + '&country=' + country + '&place=' + place


    def importISOTable(self, path=None):
        if not os.path.isfile(path):
            raise OSError('File not found: ' + path)

        with open(path) as f:
            for line in f:
                if line.startswith('#'):
                    continue

                terms = line.split('\t')
                self.isoIndex[terms[4]] = terms[0]
