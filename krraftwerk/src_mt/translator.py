#!/usr/bin/env python3

import sys
import re
import rdflib
from dateutil import parser
from writer import writer
#from geoSolv import GeoIndex


def reachedLimit(i=0, limit=int(1e6)):
    return i > 0 and i % limit == 0

def nextline(f):
    b = f.read(1)
    if not b:
        return None  # eof

    s = b
    while b != b'\n':
        s += b
        b = f.read(1)

    return s

def percentageRead(f):
    pos = f.tell()  # cuirrent position
    f.seek(0, 2)  # jump to eof
    perc = pos / f.tell() * 100  # calculate percentage
    f.seek(pos, 0)  # restore old position

    return perc

def writeSubGraph(graph, partial=True, sformat='nt'):
    ofile = graph.identifier.toPython()
    part = re.sub(r'.*\.([0-9]*$)', r'\1', ofile)
    if not part.isdigit() and partial:
        ofile = ofile + '.0'

    writer.write(graph, ofile + extOf(sformat))

    if partial:
        newID = ofile.rstrip(part) + str(int(part) + 1) if part.isdigit() else ofile

        # create graph instance
        graph = rdflib.Graph(identifier=newID)
        graph.open('./store', create = True)

        return graph

def capitalize(s):
    result = ""
    for word in s.split():
        result += word.capitalize() + " " if len(word) > 3 else word + " "

    return result[:-1]     #To remove the last trailing space.

def isIdentifier(t):
    return re.match('[0-9|A-Z]{8}', t) is not None

def isData(t):
    return re.match('[0-9]{4}\/[0-9]{1,2}\/[0-9]{1,2}', t) is not None

def isURL(t):
    return re.match('^(http|https):\/\/', t) is not None

def isLocation(t):
    return re.match('[A-Z]{1}[a-z]+\, [A-Z{1}[a-z]+', t) is not None

def rawString(string):
    return re.sub('\s+', ' ', re.sub(r'\"', r'\\"', re.sub(r'\\', r'\\\\', string)))

def extOf(sformat=None):
    if sformat == 'n3':
        return '.n3'
    elif sformat == 'nquads':
        return '.nq'
    elif sformat == 'nt':
        return '.nt'
    elif sformat == 'pretty-xml':
        return '.xml'
    elif sformat == 'trig':
        return '.trig'
    elif sformat == 'trix':
        return '.trix'
    elif sformat == 'turtle':
        return '.ttl'
    elif sformat == 'xml':
        return '.xml'
    else:
        return '.rdf'


def init(graph, nss):
    magld = rdflib.URIRef(nss['base'] + 'MAG_LD')
    graph.add((magld, rdflib.URIRef(nss['rdf'] + 'type'), rdflib.URIRef(nss['void'] + 'Dataset')))
    graph.add((magld, \
               rdflib.URIRef(nss['foaf'] + 'homepage'),\
               rdflib.Literal('http://mag.spider.d2s.labs.vu.nl/',\
                              datatype=rdflib.URIRef(nss['xsd'] + 'anyURI'))))
    graph.add((magld, rdflib.URIRef(nss['dcterms'] + 'description'),\
              rdflib.Literal("A enriched Semantic Web translation of the Microsoft Academic Graph.", lang='en')))

    kddSubset = rdflib.URIRef(nss['base'] + 'MAG_KDD_Subset') # dct collection 
    graph.add((kddSubset, rdflib.URIRef(nss['rdf'] + 'type'), rdflib.URIRef(nss['dcterms'] + 'Collection')))
    graph.add((kddSubset, rdflib.URIRef(nss['dcterms'] + 'description'),\
              rdflib.Literal("A subset of the Microsoft Academic Graph as specified by the KDD for their 2016 KDD Cup.", lang='en')))

    graph.add((magld, rdflib.URIRef(nss['dcterms'] + 'hasPart'), kddSubset))
    graph.add((kddSubset, rdflib.URIRef(nss['dcterms'] + 'isPartOf'), magld))

def f2016KDDCupSelectedAffiliationsHandler(graph, nss, f):
    affiliations = []
    progress = 0
    for line in f:

        terms = line.strip().split('\t')

        ident = terms[0]
        name = capitalize(terms[-1])

        affiliations.append(ident)

        # affiliation node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Affiliation_' + ident)
        label = rdflib.Literal(rawString(name))
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        graph.add((root, rdflib.URIRef(nss['dcterms'] + 'isPartOf'), rdflib.URIRef(nss['base'] + 'MAG_KDD_Subset')))
        graph.add((rdflib.URIRef(nss['base'] + 'MAG_KDD_Subset'), rdflib.URIRef(nss['dcterms'] + 'hasPart'), root))

        # type
        tnode = rdflib.URIRef(nss['base'] + 'MAG_Affiliation')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node of affiliation
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['base'] +'MAG_hasID'), idNode))

        progress += 1
        if progress % 10000 == 0:
            sys.stdout.write('\r ' + str(progress) + ' lines read ')

    return affiliations


def f2016KDDCupSelectedPapersHandler(graph, nss, f):
    entries = []

    progress = 0
    for line in f:

        terms = line.strip().split('\t')

        ident = terms[0]
        title = capitalize(terms[1])
        year = terms[2]
        confID = terms[3]
        #confShortName = terms[4]

        entries.append((ident, confID, year))

        # paper node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + ident)
        label = rdflib.Literal(rawString(title), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        graph.add((root, rdflib.URIRef(nss['dcterms'] + 'isPartOf'), rdflib.URIRef(nss['base'] + 'MAG_KDD_Subset')))
        graph.add((rdflib.URIRef(nss['base'] + 'MAG_KDD_Subset'), rdflib.URIRef(nss['dcterms'] + 'hasPart'), root))

        # id node
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['base'] +'MAG_hasID'), idNode))

        # title
        graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasTitle'), rdflib.Literal(rawString(title), lang='en')))

        # year
        ynode = rdflib.Literal(year, datatype=rdflib.URIRef(nss['xsd'] + 'gYear'))
        graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasYearOfPublication'), ynode))

        # type
        tnode = rdflib.URIRef(nss['base'] + 'MAG_Paper')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node of conference plus link
        # overwrite if exists
        croot = rdflib.URIRef(nss['base'] + 'MAG_Conference_' + confID)
        #graph.add((root, rdflib.URIRef(nss['base'] +'MAG_isPresentedAt'), croot))
        #graph.add((croot, rdflib.URIRef(nss['base'] +'MAG_hasPresented'), root))

        graph.add((croot, rdflib.URIRef(nss['dcterms'] + 'isPartOf'), rdflib.URIRef(nss['base'] + 'MAG_KDD_Subset')))
        graph.add((rdflib.URIRef(nss['base'] + 'MAG_KDD_Subset'), rdflib.URIRef(nss['dcterms'] + 'hasPart'), croot))

        progress += 1
        if progress % 10000 == 0:
            sys.stdout.write('\r ' + str(progress) + ' lines read ')

    return entries


def fAffiliationsHandler(graph, nss, f, affiliationIDs):
    progress = 0
    for line in f:
        terms = line.strip().split('\t')

        ident = terms[0]
        name = capitalize(terms[1])

        progress += 1
        if progress % 10000 == 0:
            sys.stdout.write('\r ' + str(progress) + ' lines read ')

        if ident not in affiliationIDs:
            continue


        # affiliation node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Affiliation_' + ident)
        label = rdflib.Literal(rawString(name))
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        # type
        tnode = rdflib.URIRef(nss['base'] + 'MAG_Affiliation')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node of affiliation
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['base'] +'MAG_hasID'), idNode))



def fAuthorsHandler(nss, authors, input_queue, graph_list):
    while True:

        f = input_queue.get()
        # exit signal 
        if f == None:
            return

        graph = rdflib.Graph()

        for line in f:

            terms = line.strip().split('\t')

            ident = terms[0]
            name = terms[1].title()

            if ident not in authors:
                continue

            # author node plus label
            root = rdflib.URIRef(nss['base'] + 'MAG_Author_' + ident)
            label = rdflib.Literal(rawString(name))
            graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

            # type
            tnode = rdflib.URIRef(nss['base'] + 'MAG_Author')
            graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

            # id node of Author
            idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
            graph.add((root, rdflib.URIRef(nss['base'] +'MAG_hasID'), idNode))


        graph_list.append(graph)


def fConferencesHandler(graph, nss, f, confIDs):
    #conferenceIDs = [cid.value for conference, _, _ in graph.triples((None, rdflib.URIRef(nss['rdf'] + 'type'), rdflib.URIRef(nss['base'] + 'MAG_Conference'))) \
    #            for _, _, cid in graph.triples((conference, rdflib.URIRef(nss['base'] + 'MAG_hasID'), None))]

    progress = 0

    for line in f:

        terms = line.strip().split('\t')

        ident = terms[0]
        name = capitalize(terms[2])

        progress += 1
        if progress % 10000 == 0:
            sys.stdout.write('\r ' + str(progress) + ' lines read ')


        if ident not in confIDs:
            continue

        # Conference node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Conference_' + ident)
        label = rdflib.Literal(rawString(name), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        # type
        tnode = rdflib.URIRef(nss['base'] + 'MAG_Conference')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node of affiliation
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['base'] +'MAG_hasID'), idNode))


def fConferenceInstancesHandler(graph, nss, f, conferenceIDs, years, paperIDs, paperConfIDs):
    #geoIndex = GeoIndex()


    progress = 0

    for line in f:

        terms = line.strip().split('\t')

        organizationId = terms[0]
        ident = terms[1]
        shortName = terms[2] 
        name = terms[3]
        location = terms[4] if len(terms) > 4 and terms[4] != '' else None
        url = terms[5] if len(terms) > 5 and terms[5] != '' else None
        startdate = parser.parse(terms[6]) if len(terms) > 6 and terms[6] != '' else None
        enddate = parser.parse(terms[7]) if len(terms) > 7 and terms[7] != '' else None
        abstractdate = parser.parse(terms[8]) if len(terms) > 8 and terms[8] != '' else None
        subdate = parser.parse(terms[9]) if len(terms) > 9 and terms[9] != '' else None
        notdate = parser.parse(terms[10]) if len(terms) > 10 and terms[10] != '' else None
        finaldate = parser.parse(terms[11]) if len(terms) > 11 and terms[11] != '' else None

        progress += 1
        if progress % 10000 == 0:
            sys.stdout.write('\r ' + str(progress) + ' lines read ')

        if ' ' in ident:  # dirty fix cause the specs dont hold
            continue

        if startdate is not None:
            paperyear = startdate.year
        elif enddate is not None:
            paperyear = enddate.year
        elif finaldate is not None:
            paperyear = finaldate.year
        else:
            paperyear = -1

        if organizationId not in conferenceIDs or not (int(paperyear) > 2010 or int(paperyear) < 0):
            continue


        #conferenceInstances.add(ident) # add kdd conf instances

        # instance node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance_' + ident)
        label = rdflib.Literal(rawString(name), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        i = 0
        while i < len(paperConfIDs):
            if paperConfIDs[i] == organizationId and int(paperyear) == years[i]:
                graph.add((rdflib.URIRef(nss['base'] + 'MAG_Paper_' + paperIDs[i]), rdflib.URIRef(nss['base'] +'MAG_isPresentedAt'), root))
                graph.add((root, rdflib.URIRef(nss['base'] +'MAG_hasPresented'), rdflib.URIRef(nss['base'] + 'MAG_Paper_' + paperIDs[i])))
            i += 1

        # type
        tnode = rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node of affiliation
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['base'] +'MAG_hasID'), idNode))

        graph.add((rdflib.URIRef(nss['base'] + 'MAG_Conference_' + organizationId), \
                   rdflib.URIRef(nss['base'] + 'MAG_hasOrganized'), \
                   root))
        graph.add((root, \
                   rdflib.URIRef(nss['base'] + 'MAG_isOrganizedBy'), \
                   rdflib.URIRef(nss['base'] + 'MAG_Conference_' + organizationId)))

        # URL
        if url is not None and isURL(url):
            node = rdflib.Literal(url, datatype=rdflib.URIRef(nss['xsd'] + 'anyURI'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasUrl'), node))

        # short name
        node = rdflib.Literal(rawString(shortName), datatype=rdflib.URIRef(nss['xsd'] + 'string'))
        graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasShortName'), node))

        # location
        #geoURI =geoIndex.resolve(location)
        #if geoURI is None:
        #    loc = rdflib.Literal(location)
        #else:
        #    loc = rdflib.URIRef(geoURI) # range should actually be geoThing (coordinates)
        if location is not None and isLocation(location):
            loc = rdflib.Literal(location) # turned off for now
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasLocation'), loc))


        # to facilitate easy queries
        if paperyear is not None and int(paperyear) > 0:
            year = rdflib.Literal(int(paperyear), datatype=rdflib.URIRef(nss['xsd'] + 'gYear'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasYearOfOccurence'), year))

        # Start date
        if startdate is not None:
            startdateLiteral = rdflib.Literal(startdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasStartDate'), startdateLiteral))

        # end date
        if enddate is not None:
            enddateLiteral = rdflib.Literal(enddate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasEndDate'), enddateLiteral))

        # abstract date
        if abstractdate is not None:
            abstractdateLiteral = rdflib.Literal(abstractdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasAbstractDueOn'), abstractdateLiteral))

        # submission date
        if subdate is not None:
            subLiteral = rdflib.Literal(subdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasSubmissionDueOn'), subLiteral))

        # notification date
        if notdate is not None:
            notLiteral = rdflib.Literal(notdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasNotificationDueOn'), notLiteral))

        # final date
        if finaldate is not None:
            finalLiteral = rdflib.Literal(finaldate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasFinalDueOn'), finalLiteral))


    #return conferenceInstances

def fKDDConferenceInstancesHandler(graph, nss, f, conferenceIDs, years, paperIDs):
    #geoIndex = GeoIndex()

    """conferenceIDsPerYear = [(cid.value, y.value) \
                                 for pid in paperIDs \
                                 for paper, _, _ in graph.triples((None, rdflib.URIRef(nss['base'] + 'MAG_hasID'), rdflib.Literal(pid))) \
                                 for _, _, conference in graph.triples((paper, rdflib.URIRef(nss['base'] + 'MAG_presentedAt'), None)) \
                                 for _, _, cid in graph.triples((conference, rdflib.URIRef(nss['base'] + 'MAG_hasID'), None)) \
                                 for _, _, y in graph.triples((paper, rdflib.URIRef(nss['base'] + 'MAG_yearOfPublication'), None))]
    """
    # linked by indices
    #conferenceIDs, years = zip(*conferenceIDsPerYear)


    #kddConferenceInstances = set()

    progress = 0

    for line in f:

        terms = line.strip().split('\t')

        organizationId = terms[0]
        ident = terms[1]
        shortName = terms[2] 
        name = terms[3]
        location = terms[4] if len(terms) > 4 and terms[4] != '' else None
        url = terms[5] if len(terms) > 5 and terms[5] != '' else None
        startdate = parser.parse(terms[6]) if len(terms) > 6 and terms[6] != '' else None
        enddate = parser.parse(terms[7]) if len(terms) > 7 and terms[7] != '' else None
        abstractdate = parser.parse(terms[8]) if len(terms) > 8 and terms[8] != '' else None
        subdate = parser.parse(terms[9]) if len(terms) > 9 and terms[9] != '' else None
        notdate = parser.parse(terms[10]) if len(terms) > 10 and terms[10] != '' else None
        finaldate = parser.parse(terms[11]) if len(terms) > 11 and terms[11] != '' else None

        progress += 1
        if progress % 10000 == 0:
            sys.stdout.write('\r ' + str(progress) + ' lines read ')

        if ' ' in ident:  # dirty fix cause the specs dont hold
            continue

        if startdate is not None:
            paperyear = startdate.year
        elif enddate is not None:
            paperyear = enddate.year
        elif finaldate is not None:
            paperyear = finaldate.year
        else:
            paperyear = -1 

        i = 0
        while i < len(conferenceIDs):
            if conferenceIDs[i] == organizationId and (int(paperyear) > 2010 or int(paperyear) < 0):
                break
            i += 1
        if i >= len(conferenceIDs): # not a target conference
            continue

        # kddConferenceInstances.add(ident) # add kdd conf instances

        # instance node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance_' + ident)
        label = rdflib.Literal(rawString(name), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        if int(years[i]) == int(paperyear):
            graph.add((rdflib.URIRef(nss['base'] + 'MAG_Paper_' + paperIDs[i]), rdflib.URIRef(nss['base'] +'MAG_isPresentedAt'), root))
            graph.add((root, rdflib.URIRef(nss['base'] +'MAG_hasPresented'), rdflib.URIRef(nss['base'] + 'MAG_Paper_' + paperIDs[i])))

        # type
        tnode = rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node of affiliation
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['base'] +'MAG_hasID'), idNode))

        graph.add((rdflib.URIRef(nss['base'] + 'MAG_Conference_' + organizationId), \
                   rdflib.URIRef(nss['base'] + 'MAG_hasOrganized'), \
                   root))
        graph.add((root, \
                   rdflib.URIRef(nss['base'] + 'MAG_isOrganizedBy'), \
                   rdflib.URIRef(nss['base'] + 'MAG_Conference_' + organizationId)))

        # URL
        if url is not None and isURL(url):
            node = rdflib.Literal(url, datatype=rdflib.URIRef(nss['xsd'] + 'anyURI'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasUrl'), node)) 

        # short name
        node = rdflib.Literal(rawString(shortName), datatype=rdflib.URIRef(nss['xsd'] + 'string'))
        graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasShortName'), node)) 

        # location
        #geoURI =geoIndex.resolve(location)
        #if geoURI is None:
        #    loc = rdflib.Literal(location)
        #else:
        #    loc = rdflib.URIRef(geoURI) # range should actually be geoThing (coordinates)
        if location is not None and isLocation(location):
            loc = rdflib.Literal(location) # turned off for now
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasLocation'), loc))


        # to facilitate easy queries
        if paperyear is not None and int(paperyear) > 0:
            year = rdflib.Literal(int(paperyear), datatype=rdflib.URIRef(nss['xsd'] + 'gYear'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasYearOfOccurence'), year))

        # Start date
        if startdate is not None:
            startdateLiteral = rdflib.Literal(startdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasStartDate'), startdateLiteral))

        # end date
        if enddate is not None:
            enddateLiteral = rdflib.Literal(enddate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasEndDate'), enddateLiteral))

        # abstract date
        if abstractdate is not None:
            abstractdateLiteral = rdflib.Literal(abstractdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasAbstractDueOn'), abstractdateLiteral))

        # submission date
        if subdate is not None:
            subLiteral = rdflib.Literal(subdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasSubmissionDueOn'), subLiteral))

        # notification date
        if notdate is not None:
            notLiteral = rdflib.Literal(notdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasNotificationDueOn'), notLiteral))

        # final date
        if finaldate is not None:
            finalLiteral = rdflib.Literal(finaldate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasFinalDueOn'), finalLiteral))

        graph.add((root, rdflib.URIRef(nss['dcterms'] + 'isPartOf'), rdflib.URIRef(nss['base'] + 'MAG_KDD_Subset')))
        graph.add((rdflib.URIRef(nss['base'] + 'MAG_KDD_Subset'), rdflib.URIRef(nss['dcterms'] + 'hasPart'), root))

    #return kddConferenceInstances


def fFieldsOfStudyHandler(graph, nss, f):
    progress = 0

    for line in f:

        terms = line.strip().split('\t')

        ident = terms[0]
        name = terms[1]

        # add node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + ident)
        label = rdflib.Literal(rawString(name), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))
        graph.add((root, rdflib.URIRef(nss['skos'] + 'prefLabel'), rdflib.Literal(rawString(name), lang='en')))

        # type
        tnode = rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['base'] +'MAG_hasID'), idNode))

        progress += 1
        if progress % 10000 == 0:
            sys.stdout.write('\r ' + str(progress) + ' lines read ')

    return progress


# skosified
def fFieldOfStudyHierarchyHandler(graph, nss, f):
    root = rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudyHierarchy')
    tnode = rdflib.URIRef(nss['skos'] + 'ConceptScheme')
    graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

    progress = 0



    for line in f:

        terms = line.strip().split('\t')

        childId = terms[0]
        childLvl = terms[1][1:]
        parentId = terms[2]
        parentLvl = terms[3][1:]
        confidence = terms[4]

        graph.add((rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + childId), \
                   rdflib.URIRef(nss['skos'] + 'inScheme'), \
                   root))
        graph.add((rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + parentId), \
                   rdflib.URIRef(nss['skos'] + 'inScheme'), \
                   root))


        if int(childLvl) == 0 :
            graph.add((root, \
                       rdflib.URIRef(nss['skos'] + 'hasTopConcept'), \
                       rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + childId)))
        if int(parentLvl) == 0 :
            graph.add((root, \
                       rdflib.URIRef(nss['skos'] + 'hasTopConcept'), \
                       rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + parentId)))

        if int(childLvl) - int(parentLvl) == 1:
            graph.add((rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + childId), \
                       rdflib.URIRef(nss['skos'] + 'narrower'), \
                       rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + parentId)))
            graph.add((rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + parentId), \
                       rdflib.URIRef(nss['skos'] + 'broader'), \
                       rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + childId)))

            graph.add((rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + parentId), \
                       rdflib.URIRef(nss['skos'] + 'note'), \
                       rdflib.Literal('Confidence of being broader than {} is {}'.format(childId, confidence))))
            graph.add((rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + childId), \
                       rdflib.URIRef(nss['skos'] + 'note'), \
                       rdflib.Literal('Confidence of being narrower than {} is {}'.format(parentId, confidence))))
        elif int(parentLvl) - int(childLvl) == 1:
            graph.add((rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + childId), \
                       rdflib.URIRef(nss['skos'] + 'broader'), \
                       rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + parentId)))
            graph.add((rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + parentId), \
                       rdflib.URIRef(nss['skos'] + 'narrower'), \
                       rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + childId)))

            graph.add((rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + parentId), \
                       rdflib.URIRef(nss['skos'] + 'note'), \
                       rdflib.Literal('Confidence of being narrower than {} is {}'.format(childId, confidence))))
            graph.add((rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + childId), \
                       rdflib.URIRef(nss['skos'] + 'note'), \
                       rdflib.Literal('Confidence of being broader than {} is {}'.format(parentId, confidence))))

        progress += 1
        if progress % 10000 == 0:
            sys.stdout.write('\r ' + str(progress) + ' lines read ')




def fJournalsHandler(graph, nss, f, journalIDs):
    #journalIDs = [jid.value for journal, _, _ in graph.triples((None, rdflib.URIRef(nss['rdf'] + 'type'), rdflib.URIRef(nss['base'] + 'MAG_Journal'))) \
    #            for _, _, jid in graph.triples((journal, rdflib.URIRef(nss['base'] + 'MAG_hasID'), None))]

    progress = 0


    for line in f:

        terms = line.strip().split('\t')

        ident = terms[0]
        name = terms[1]

        progress += 1
        if progress % 10000 == 0:
            sys.stdout.write('\r ' + str(progress) + ' lines read ')

        if ident not in journalIDs:
            continue

        # add node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Journal_' + ident)
        label = rdflib.Literal(rawString(name), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        # type
        tnode = rdflib.URIRef(nss['base'] + 'MAG_Journal')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['base'] +'MAG_hasID'), idNode))



def getDate(s):
    d = None

    try:
        d = parser.parse(s)
    except ValueError:
        pass

    return d

def fPapersHandler(nss, kddPapers, confIDs, input_queue, graph_list, allPapers, journalIDs):

    #paperIDs = [pid.value for paper, _, _ in graph.triples((None, rdflib.URIRef(nss['rdf'] + 'type'), rdflib.URIRef(nss['base'] + 'MAG_Paper'))) \
    #            for _, _, pid in graph.triples((paper, rdflib.URIRef(nss['base'] + 'MAG_hasID'), None))]

    while True:

        f = input_queue.get()
        # exit signal 
        if f == None:
            return

        graph = rdflib.Graph()
        for line in f:
            terms = line.strip().split('\t')

            ident = terms[0]
            title = terms[1]
            # title_alt = terms[2] if terms[2] != '' else None
            year = terms[3] if terms[3] != '' else None
            date = getDate(terms[4]) if terms[4] != '' else None
            doi = terms[5] if terms[5] != '' else None
            # venue = terms[6] if terms[6] != '' else None   # superseded by conference ID
            # venue_alt = terms[7] if terms[7] != '' else None
            journalId = terms[8] if terms[8] != '' else None
            conferenceId = terms[9] if terms[9] != '' else None
            rank = terms[10] if terms[10] != '' else None

            if ident in kddPapers or not (conferenceId in confIDs and int(year) > 2010):
                continue

            allPapers.append((ident, year, conferenceId))


            # add node plus label
            root = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + ident)
            label = rdflib.Literal(rawString(title), lang='en')
            graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

            # title
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasTitle'), rdflib.Literal(rawString(title), lang='en')))

            # year
            if year is not None:
               ynode = rdflib.Literal(year, datatype=rdflib.URIRef(nss['xsd'] + 'gYear'))
               graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasYearOfPublication'), ynode))

            # date
            if date is not None:
                dnode = rdflib.Literal(date.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
                graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasDateOfPublication'), dnode))

            # type
            tnode = rdflib.URIRef(nss['base'] + 'MAG_Paper')
            graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

            # id node
            idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
            graph.add((root, rdflib.URIRef(nss['base'] +'MAG_hasID'), idNode))




            # doi
            if doi is not None:
                doinode = rdflib.Literal(doi, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
                graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasDoi'), doinode))

            # rank
            if rank is not None:
                ranknode = rdflib.Literal(rank, datatype=rdflib.URIRef(nss['xsd'] + 'positiveInteger'))
                graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasRank'), ranknode))

            # journal
            if journalId is not None:
                journalIDs.append(journalId)
                jnode = rdflib.URIRef(nss['base'] + 'MAG_Journal_' + journalId)
                graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_isPublishedIn'), jnode))
                graph.add((jnode, rdflib.URIRef(nss['base'] + 'MAG_hasPublished'), root))

        graph_list.append(graph)


def fKDDPapersHandler(nss, paperIDs, confIDs, input_queue, graph_list, journalIDs, allPaperConfIDs):
    while True:

        f = input_queue.get()
        # exit signal 
        if f == None:
            return

        graph = rdflib.Graph()
        for line in f:
            terms = line.strip().split('\t')

            ident = terms[0]
            title = terms[1]
            # title_alt = terms[2] if terms[2] != '' else None
            year = terms[3] if terms[3] != '' else None
            date = getDate(terms[4]) if terms[4] != '' else None
            doi = terms[5] if terms[5] != '' else None
            # venue = terms[6] if terms[6] != '' else None   # superseded by conference ID
            # venue_alt = terms[7] if terms[7] != '' else None
            journalId = terms[8] if terms[8] != '' else None
            conferenceId = terms[9] if terms[9] != '' else None
            rank = terms[10] if terms[10] != '' else None

            root = None
            if ident not in paperIDs:
                if conferenceId in confIDs and int(year) > 2010:
                    # add node plus label
                    root = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + ident)
                    label = rdflib.Literal(rawString(title), lang='en')
                    graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

                    # title
                    graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasTitle'), rdflib.Literal(rawString(title), lang='en')))

                    # year
                    if year is not None:
                       ynode = rdflib.Literal(year, datatype=rdflib.URIRef(nss['xsd'] + 'gYear'))
                       graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasYearOfPublication'), ynode))

                    # type
                    tnode = rdflib.URIRef(nss['base'] + 'MAG_Paper')
                    graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

                    # id node
                    idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
                    graph.add((root, rdflib.URIRef(nss['base'] +'MAG_hasID'), idNode))

                    if journalId is not None:
                        journalIDs.append(journalId)
                else:
                    allPaperConfIDs[ident] = conferenceId # exclude KDD subset as we already know about their confs
                    continue


            # add node plus label
            root = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + ident) if root is None else root
            #label = rdflib.Literal(rawString(title), lang='en')
            #graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

            # date
            if date is not None:
                dnode = rdflib.Literal(date.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
                graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasDateOfPublication'), dnode))


            # doi
            if doi is not None:
                doinode = rdflib.Literal(doi, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
                graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasDoi'), doinode))

            # rank
            if rank is not None:
                ranknode = rdflib.Literal(rank, datatype=rdflib.URIRef(nss['xsd'] + 'positiveInteger'))
                graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasRank'), ranknode))

            # journal
            if journalId is not None:
                journalIDs.append(journalId)
                jnode = rdflib.URIRef(nss['base'] + 'MAG_Journal_' + journalId)
                graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_isPublishedIn'), jnode))
                graph.add((jnode, rdflib.URIRef(nss['base'] + 'MAG_hasPublished'), root))

        graph_list.append(graph)


def fPaperAuthorAffiliationsHandler(nss, paperIDs, input_queue, graph_list, authors, affiliations):
    while True:

        f = input_queue.get()
        # exit signal 
        if f == None:
            return

        graph = rdflib.Graph()

        for line in f:

            terms = line.strip().split('\t')

            paperId = terms[0]
            authorId = terms[1]
            affiliationId = terms[2]
            #affiliationName = terms[3]
            #affiliationName_alt = terms[4]
            seqnum = terms[5]

            if paperId not in paperIDs:
                continue

            authors.append(authorId)
            affiliations.append(affiliationId)


            paper = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + paperId)
            author = rdflib.URIRef(nss['base'] + 'MAG_Author_' + authorId)

            # paper - author
            graph.add((paper, rdflib.URIRef(nss['base'] + 'MAG_hasAuthor'), author))
            graph.add((author, rdflib.URIRef(nss['base'] + 'MAG_isAuthorOf'), paper))

            # affiliation - author
            affiliation = rdflib.URIRef(nss['base'] + 'MAG_Affiliation_' + affiliationId)
            graph.add((affiliation, rdflib.URIRef(nss['base'] + 'MAG_hasMember'), author))
            graph.add((author, rdflib.URIRef(nss['base'] + 'MAG_isAffiliatedWith'), affiliation))

            # author sequence (not sure if this works out)
            if int(seqnum) == 1: # first author
                graph.add((paper, rdflib.URIRef(nss['base'] + 'MAG_hasFirstAuthor'), author))
            #elif int(seqnum) == 2:
            #    graph.add((paper, rdflib.URIRef(nss['base'] + 'MAG_secondAuthor'), author))
            #elif int(seqnum) == 3:
            #    graph.add((paper, rdflib.URIRef(nss['base'] + 'MAG_thirdAuthor'), author))
            # rest doesnt matter much (assumption)

        graph_list.append(graph)

def downwardsExpandKeywordTree(kwgraph, nss, keywords):
    expandedKeyswords = set()
    for keyword in keywords:
        expandedKeyswords = expandedKeyswords.union(recursiveDownwardsExpandKeywordTree(kwgraph, nss, keyword))

    return expandedKeyswords

def recursiveDownwardsExpandKeywordTree(g, nss, kw, kwset=None):
    if kwset is None:
        return recursiveDownwardsExpandKeywordTree(g, nss, kw, kwset={kw})

    for _, _, ekw in g.triples((rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + kw), rdflib.URIRef(nss['skos'] + 'narrower'), None)):
        ekw = re.sub('.*_', '', ekw.toPython())
        kwset = kwset.union(recursiveDownwardsExpandKeywordTree(g, nss, ekw, kwset={ekw}))

    return kwset

def fPaperKeywordsHandler(nss, paperIDs, paperConfIndex, input_queue, graph_list, allKDDSubsetFOS, confFOSIndex):
    while True:

        f = input_queue.get()
        # exit signal 
        if f == None:
            return

        graph = rdflib.Graph()

        for line in f:
            terms = line.strip().split('\t')

            paperId = terms[0]
            keyword = terms[1]
            fieldOfStudyId = terms[2]

            if paperId not in paperIDs:
                if paperId in paperConfIndex:
                    if paperConfIndex[paperId] not in confFOSIndex.keys():
                        confFOSIndex[paperConfIndex[paperId]] = {fieldOfStudyId}
                    else:
                        confFOSIndex[paperConfIndex[paperId]].add(fieldOfStudyId)

                continue


            # nodes
            paper = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + paperId)
            fieldOfStudy = rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + fieldOfStudyId)
            keywordNode = rdflib.Literal(keyword, lang='en')

            allKDDSubsetFOS.append(fieldOfStudyId)
            # paper - topic
            graph.add((paper, \
                       rdflib.URIRef(nss['base'] + 'MAG_hasKeyword'), \
                       keywordNode))

            # fieldOfStudy - topic
            graph.add((fieldOfStudy, \
                       rdflib.URIRef(nss['base'] + 'MAG_hasKeyword'), \
                       keywordNode))

        graph_list.append(graph)



def expandConferences(kddFOSs, confFOSIndex, nrOfTerms, maxDiff=0.4, topn=-1, d='hamming'):
    topn = 100 # temporary fix
    confs = []

    hashMapLength = nrOfTerms * 2
    kddFOSsVec = sparseHashingVectorization(kddFOSs, hashMapLength)
    if d != 'hamming':
        import numpy as np
        kddFOSsVecNorm = np.linalg.norm(kddFOSsVec.A[0])
    for conf, bow in confFOSIndex.items():
        vec = sparseHashingVectorization(bow, hashMapLength)

        if d == 'hamming':
            # normalized hamming distance
            diff = abs(kddFOSsVec - vec).sum() / nrOfTerms
        else:
            # cos similarity (sparse matrix not needed really)
            diff = 1.0 - np.dot(kddFOSsVec.A[0], vec.A[0]) / (np.linalg.norm(vec.A[0]) / kddFOSsVecNorm)

        if topn < 0 and diff >= maxDiff:
            continue

        confs.append((conf, diff))

    if topn > 0:
        confs.sort(key = lambda e: e[1])
        confs = confs[:topn]

    return confs


def sparseHashingVectorization(features, n):
    import numpy as np
    from scipy.sparse import csc_matrix

    vec = [0] * n
    for f in features:
        vec[hash(f)%n] = 1

    return csc_matrix(vec, dtype=np.int8)

def fPaperReferencesHandler(nss, paperIDs, input_queue, graph_list, paperRefs):
    while True:

        f = input_queue.get()
        # exit signal 
        if f == None:
            return

        graph = rdflib.Graph()

        for line in f:

            terms = line.strip().split('\t')

            paperId = terms[0]
            refId = terms[1]


            if paperId not in paperIDs:
                continue

            if paperId not in paperRefs:
                paperRefs[paperId] = 1
            else:
                paperRefs[paperId] += 1

            if refId not in paperIDs:
                continue

            # nodes
            paper = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + paperId)
            ref = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + refId)
            # paper - reference
            graph.add((paper, \
                       rdflib.URIRef(nss['base'] + 'MAG_hasCited'), \
                       ref))
            graph.add((ref, \
                       rdflib.URIRef(nss['base'] + 'MAG_isCitedBy'), \
                       paper))

        graph_list.append(graph)


def fPaperRefCount(graph, nss, paperRefs):
    for paperId, nrOfRefs in paperRefs.items():
        paper = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + paperId)
        graph.add((paper, \
                  rdflib.URIRef(nss['base']+ 'MAG_isNumberOfTimesCited'), \
                  rdflib.Literal(nrOfRefs, datatype=rdflib.URIRef(nss['xsd'] + 'positiveInteger'))))




def fPaperUrlsHandler(graph, nss, f, papers):
    progress = 0



    for line in f:

        terms = line.strip().split('\t')

        paperId = terms[0]
        url = terms[1]

        progress += 1
        if progress % 10000 == 0:
            sys.stdout.write('\r ' + str(progress) + ' lines read ')

        if paperId not in papers:
            continue

        # nodes
        paper = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + paperId)
        url = rdflib.Literal(url, datatype=rdflib.URIRef(nss['xsd'] + 'anyURI'))

        # paper - url
        graph.add((paper, \
                   rdflib.URIRef(nss['base'] + 'MAG_hasUrl'), \
                   url))



