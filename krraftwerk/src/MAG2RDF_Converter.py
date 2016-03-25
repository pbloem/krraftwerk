#!/usr/bin/env python3

import sys
import os
import re
import getopt
import zipfile
from datetime import datetime
import rdflib
from writer import writer
from dateutil import parser
from geoSolv import GeoIndex


def main(argv):
    ifile = ''
    ofile = ''
    default_ns = 'http://www.example.org/'
    sformat = 'turtle'

    try:
        opts, args = getopt.getopt(argv, "d:f:hi:o:", ["if=", "of=", "format=", "default_namespace="])
    except getopt.GetoptError:
        print('mag2rdf -i <inputfile> [-d <default namespace> -o <outputfile> -f <serialization format>]')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(str('A tool to translate the Microsoft Academic Graph, to its Semantic Web equivalent.\nUsage:\n\t' +
                      'mag2rdf.py -i <inputfile> [-d <default namespace> -o <outputfile> -f <serialization format>]'))
            sys.exit(0)
        elif opt in ("-i", "--ifile"):
            ifile = arg
        elif opt in ("-o", "--ofile"):
            ofile = arg
        elif opt in ("-d", "--default_namespace"):
            default_ns = arg
        elif opt in ("-f", "--format"):
            sformat = arg

    if ifile == '':
        print('Missing required input (flags).\nUse \'MAG2RDF.py -h\' for help.')
        sys.exit(1)

    if ofile == '' and ifile != '' :
        ofile = os.getcwd() + '/' + re.sub(r'^(?:.*/)?(.*)\..*$', r'\1', ifile) + '-{}'.format(str(datetime.now()))
    else:
        ofile = os.getcwd() + '/' + 'output-{}'.format(str(datetime.now()))

    graph = translate(ifile, default_ns)

    if graph is not None:
        writer.write(graph, ofile + extOf(sformat), sformat)
    else:
        raise Exception


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


def translate(ifile, ns):
    if not os.path.isfile(ifile):
        raise OSError('File not found: ' + ifile)

    # create graph instance
    graph = rdflib.Graph(identifier='MAG-LD')

    # set namespaces
    nsmgr = rdflib.namespace.NamespaceManager(graph)
    nsmgr.bind('base', rdflib.Namespace(ns))
    nsmgr.bind('dcterms', rdflib.Namespace('http://purl.org/dc/elements/1.1/'))
    nsmgr.bind('SWRC', rdflib.Namespace('http://swrc.ontoware.org/ontology#'))
    nsmgr.bind('swc', rdflib.Namespace('http://data.semanticweb.org/ns/swc/ontology#'))
    nsmgr.bind('conf', rdflib.Namespace('http://ebiquity.umbc.edu/ontology/conference.owl#'))
    nsmgr.bind('foaf', rdflib.Namespace('http://xmlns.com/foaf/0.1/'))
    nsmgr.bind('xsd', rdflib.Namespace('http://www.w3.org/2001/XMLSchema#'))
    nsmgr.bind('skos', rdflib.Namespace('http://www.w3.org/2004/02/skos/core#'))
    nsmgr.bind('prism', rdflib.Namespace('http://prismstandard.org/namespaces/1.2/basic/'))
    nsmgr.bind('bibo', rdflib.Namespace('http://purl.org/ontology/bibo/'))

    nss = dict(nsmgr.namespaces())

    with zipfile.ZipFile(ifile, 'r') as zfile:
        # with zfile.open('2016KDDCupSelectedAffiliations.txt') as zf:
        #    kddAffiliationsHandler(graph, nss, zf)
        # with zfile.open('2016KDDCupSelectedPapers.txt') as zf:
        #    kddPapersHandler(graph, nss, zf)
        print('importing affiliations')
        with zfile.open('Affiliations.txt') as zf:
            affiliationsHandler(graph, nss, zf)
        
        print('importing authors (this will take a while)')
        with zfile.open('Authors.txt') as zf:
            authorsHandler(graph, nss, zf)
            
        print('importing conferences')
        with zfile.open('Conferences.txt') as zf:
            conferencesHandler(graph, nss, zf)
            
        print('importing conference instances')
        with zfile.open('ConferenceInstances.txt') as zf:
            conferenceInstancesHandler(graph, nss, zf)
                                                       
        print('importing fields of study')
        with zfile.open('FieldsOfStudy.txt') as zf:
            fieldsOfStudyHandler(graph, nss, zf)
        
        print('importing fields of study hierarchy')
        with zfile.open('FieldOfStudyHierarchy.txt') as zf:
            fieldOfStudyHierarchyHandler(graph, nss, zf)
        
        print('importing journals')
        with zfile.open('Journals.txt') as zf:
            journalHandler(graph, nss, zf)
        
        print('importing papers')
        with zfile.open('Papers.txt') as zf:
            paperHandler(graph, nss, zf)
        
        print('importing papers-authors-affiliations')
        with zfile.open('PaperAuthorAffiliations.txt') as zf:
            paperAuthorAffiliationsHandler(graph, nss, zf)
        
        print('importing papers keywords')
        with zfile.open('PaperKeywords.txt') as zf:
            paperKeywordsHandler(graph, nss, zf)
        
        print('importing papers references')
        with zfile.open('PaperReferences.txt') as zf:
            paperReferenceHandler(graph, nss, zf)
        
        print('importing papers URIs')
        with zfile.open('PaperUrls.txt') as zf:
            paperUrlsHandler(graph, nss, zf)
        

    return graph


def kddAffiliationsHandler(graph, nss, f):
    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        ident = rawString(terms[0])
        name = rawString(terms[-1])

        # affiliation node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Affiliation_' + ident)
        label = rdflib.Literal('Affiliation \\"{}\\"'.format(name), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        # type
        tnode = rdflib.URIRef(nss['SWRC'] + 'Organization')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node of affiliation
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['dcterms'] +'identifier'), idNode))

def kddPapersHandler(graph, nss, f):
    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        ident = rawString(terms[0])
        title = rawString(terms[1])
        year = rawString(terms[2])
        confID = rawString(terms[3])
        #confShortName = rawString(terms[4])

        # paper node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + ident)
        label = rdflib.Literal('Paper with title \\"{}\\"'.format(title), lang='en')            
            
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))
        # title
        graph.add((root, rdflib.URIRef(nss['dcterms'] + 'title'), rdflib.Literal(title, lang='en')))
        # year
        ynode = rdflib.Literal(year, datatype=rdflib.URIRef(nss['xsd'] + 'gYear'))   
        graph.add((root, rdflib.URIRef(nss['dcterms'] + 'date'), ynode))
        # type
        tnode = rdflib.URIRef(nss['SWRC'] + 'Publication')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node of conference plus link
        # overwrite if exists
        croot = rdflib.URIRef(nss['base'] + 'MAG_Conference_' + confID)
        idNode = rdflib.Literal(confID, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((croot, rdflib.URIRef(nss['SWRC'] +''), idNode))
        # SWRC links paper to author and author to conference

def affiliationsHandler(graph, nss, f):
    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        ident = rawString(terms[0])
        name = rawString(terms[1])

        # affiliation node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Affiliation_' + ident)
        label = rdflib.Literal('Affiliation \\"{}\\"'.format(name), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        # type
        tnode = rdflib.URIRef(nss['foaf'] + 'Organization')
        tnode_alt = rdflib.URIRef(nss['SWRC'] + 'Organization')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode_alt))

        # id node of affiliation
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['dcterms'] +'identifier'), idNode))

def authorsHandler(graph, nss, f):
    progress = 0
    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        ident = rawString(terms[0])
        name = rawString(terms[1])

        # author node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Author_' + ident)
        label = rdflib.Literal('\\"{}\\"'.format(name), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        # type
        tnode = rdflib.URIRef(nss['foaf'] + 'Person')
        tnode_alt = rdflib.URIRef(nss['SWRC'] + 'Person')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode_alt))

        # id node of Author
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['dcterms'] +'identifier'), idNode))
        
        progress += 1
        if progress % 10000 == 0:
            sys.stdout.write('\r ' + str(progress) + ' authors read.')
        

def conferencesHandler(graph, nss, f):
    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        ident = rawString(terms[0])
        name = rawString(terms[2])
        
        # shortName = rawString(terms[1])
        # TODO: add?

        # Conference node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Conference_' + ident)
        label = rdflib.Literal('Conference \\"{}\\"'.format(name), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        # type
        """
        I think we should see this as the organization behind the conference events. 
        You dont go to the KDD, you go to the KDD 2016 as organised by the KDD organization. 
        Does this sound reasonable?
        """
        tnode = rdflib.URIRef(nss['foaf'] + 'Organization')
        tnode_alt = rdflib.URIRef(nss['SWRC'] + 'Organization')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode_alt))

        # id node of affiliation
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['dcterms'] +'identifier'), idNode))

def conferenceInstancesHandler(graph, nss, f):
    geoIndex = GeoIndex()

    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        organizationId = rawString(terms[0])
        ident = rawString(terms[1])
        #shortName = rawString(terms[2]) # not used
        name = rawString(terms[3])
        location = rawString(terms[4])
        url = rawString(terms[5])
        startdate = parser.parse(terms[6]) if len(terms) > 6 and terms[6] != '' else None
        enddate = parser.parse(terms[7]) if len(terms) > 7 and terms[7] != '' else None
        abstractdate = parser.parse(terms[8]) if len(terms) > 8 and terms[8] != '' else None
        subdate = parser.parse(terms[9]) if len(terms) > 9 and terms[9] != '' else None
        notdate = parser.parse(terms[10]) if len(terms) > 10 and terms[10] != '' else None
        finaldate = parser.parse(terms[11]) if len(terms) > 11 and terms[11] != '' else None
        
        # instance node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance_' + ident)
        label = rdflib.Literal('Conference instance \\"{}\\"'.format(name), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        # type
        tnode = rdflib.URIRef(nss['SWRC'] + 'Conference')
        tnode_alt = rdflib.URIRef(nss['swc'] + 'ConferenceEvent')
        tnode_alt_b = rdflib.URIRef(nss['conf'] + 'Conference')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode_alt))
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode_alt_b))
        
        # id node of affiliation
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['dcterms'] +'identifier'), idNode))

        # link to conference organization
        #graph.add((rdflib.URIRef(nss['base'] + 'MAG_Conference_' + organizationId), ?, root))  # organized?
        #graph.add((root, ?, rdflib.URIRef(nss['base'] + 'MAG_Conference_' + organizationId)))  # organized by by?

        # URL 
        node = rdflib.URIRef(url)
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'seeAlso'), node)) # not the best predicate
        
        # location
        #geoURI =geoIndex.resolve(location)
        #if geoURI is None:
        #    loc = rdflib.Literal(location)
        #else:
        #    loc = rdflib.URIRef(geoURI) # range should actually be geoThing (coordinates)
        loc = rdflib.Literal(location) # turned off for now

        graph.add((root, rdflib.URIRef(nss['swc'] + 'hasLocation'), loc))


        # to facilitate easy queries
        if startdate is not None:
            year = rdflib.Literal(startdate.year, datatype=rdflib.URIRef(nss['xsd'] + 'gYear'))
            graph.add((root, rdflib.URIRef(nss['dcterms'] + 'date'), year))

        # Start date 
        if startdate is not None:
            startdateLiteral = rdflib.Literal(startdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['conf'] + 'startDate'), startdateLiteral))
        
        # end date 
        if enddate is not None:
            enddateLiteral = rdflib.Literal(enddate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['conf'] + 'endDate'), enddateLiteral))

        # abstract date 
        if abstractdate is not None:
            abstractdateLiteral = rdflib.Literal(abstractdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['conf'] + 'abstractDueOn'), abstractdateLiteral))
            graph.add((root, rdflib.URIRef(nss['conf'] + 'registrationDueOn'), abstractdateLiteral))
        
        
        ### A better solution is needed here ###
        
        # submission date 
        if subdate is not None:
            subLiteral = rdflib.Literal(subdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['conf'] + 'paperDueOn'), subLiteral))
 
        # final date 
        if finaldate is not None:
            finalLiteral = rdflib.Literal(finaldate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
            graph.add((root, rdflib.URIRef(nss['conf'] + 'paperDueOn'), finalLiteral))

def fieldsOfStudyHandler(graph, nss, f):
    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        ident = rawString(terms[0])
        name = rawString(terms[1])

        # add node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + ident)
        label = rdflib.Literal('Field of study \\"{}\\"'.format(name), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))
        graph.add((root, rdflib.URIRef(nss['skos'] + 'prefLabel'), rdflib.Literal(name, lang='en')))

        # type
        tnode = rdflib.URIRef(nss['skos'] + 'Concept')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['dcterms'] +'identifier'), idNode))

# skosified
def fieldOfStudyHierarchyHandler(graph, nss, f):
    root = rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudyHierarchy')
    tnode = rdflib.URIRef(nss['skos'] + 'ConceptScheme')
    graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))
  
    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        childId = rawString(terms[0])
        childLvl = rawString(terms[1])[1:]
        parentId = rawString(terms[2])
        parentLvl = rawString(terms[3])[1:]
        confidence = rawString(terms[4])

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

def journalHandler(graph, nss, f):
    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        ident = rawString(terms[0])
        name = rawString(terms[1])

        # add node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Journal_' + ident)
        label = rdflib.Literal('Journal \\"{}\\"'.format(name), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        # type
        tnode = rdflib.URIRef(nss['SWRC'] + 'Journal')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['dcterms'] +'identifier'), idNode))

def paperHandler(graph, nss, f):
    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        ident = rawString(terms[0])
        title = rawString(terms[1]) 
        # title_alt = rawString(terms[2]) if terms[2] != '' else None
        year = rawString(terms[3]) if terms[3] != '' else None
        date = parser.parse(rawString(terms[4])) if terms[4] != '' else None
        doi = rawString(terms[5]) if terms[5] != '' else None
        # venue = rawString(terms[6]) if terms[6] != '' else None   # superseded by conference ID
        # venue_alt = rawString(terms[7]) if terms[7] != '' else None
        journalId = rawString(terms[8]) if terms[8] != '' else None
        conferenceId = rawString(terms[9]) if terms[9] != '' else None
        rank = rawString(terms[10]) if terms[10] != '' else None

        # add node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + ident)
        label = rdflib.Literal('Paper titled \\"{}\\"'.format(title), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        # title
        graph.add((root, rdflib.URIRef(nss['dcterms'] + 'title'), rdflib.Literal(title, lang='en')))

        # year
        if year is not None:
            ynode = rdflib.Literal(year, datatype=rdflib.URIRef(nss['xsd'] + 'gYear'))   
            graph.add((root, rdflib.URIRef(nss['dcterms'] + 'date'), ynode))

        # date
        if date is not None:
            dnode = rdflib.Literal(date.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))   
            graph.add((root, rdflib.URIRef(nss['dcterms'] + 'issued'), dnode))

        # doi
        if doi is not None:
            doinode = rdflib.Literal(doi, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))   
            graph.add((root, rdflib.URIRef(nss['prism'] + 'doi'), doinode))

        # rank
        if rank is not None:
            ranknode = rdflib.Literal(rank, datatype=rdflib.URIRef(nss['xsd'] + 'positiveInteger'))
            graph.add((root, rdflib.URIRef(nss['base'] + 'MAG_hasRank'), ranknode))

        # journal
        if journalId is not None:
            jnode = rdflib.URIRef(nss['base'] + 'MAG_Journal_' + journalId)
            graph.add((root, rdflib.URIRef(nss['dcterms'] + 'hasPart'), jnode))
            graph.add((jnode, rdflib.URIRef(nss['dcterms'] + 'partOf'), root))

        # conference
        if conferenceId is not None:
            cnode = rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance_' + conferenceId)
            graph.add((root, rdflib.URIRef(nss['bibo'] + 'presentedAt'), cnode))
            graph.add((root, rdflib.URIRef(nss['swc'] + 'relatedToEvent'), cnode))
            graph.add((cnode, rdflib.URIRef(nss['bibo'] + 'presents'), root))
            graph.add((cnode, rdflib.URIRef(nss['swc'] + 'hasRelatedDocument'), root))

        # type
        tnode = rdflib.URIRef(nss['SWRC'] + 'Publication')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['dcterms'] +'identifier'), idNode))

def paperAuthorAffiliationsHandler(graph, nss, f):
    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        paperId = rawString(terms[0])
        authorId = rawString(terms[1])
        affiliationId = rawString(terms[2])
        #affiliationName = rawString(terms[3])
        #affiliationName_alt = rawString(terms[4])
        seqnum = rawString(terms[5])

        paper = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + paperId)
        author = rdflib.URIRef(nss['base'] + 'MAG_Author_' + authorId)
        affiliation = rdflib.URIRef(nss['base'] + 'MAG_Affiliation_' + affiliationId)
        
        # paper - author
        graph.add((paper, rdflib.URIRef(nss['dcterms'] + 'creator'), author))
        graph.add((paper, rdflib.URIRef(nss['SWRC'] + 'creator'), author))
        graph.add((paper, rdflib.URIRef(nss['foaf'] + 'maker'), author))
        graph.add((author, rdflib.URIRef(nss['foaf'] + 'made'), paper))
        
        # affiliation - author
        graph.add((affiliation, rdflib.URIRef(nss['foaf'] + 'member'), author))
        graph.add((author, rdflib.URIRef(nss['SWRC'] + 'affiliation'), affiliation))

        # author sequence (not sure if this works out)
        if int(seqnum) == 1: # first author
            graph.add((paper, rdflib.URIRef(nss['base'] + 'MAG_firstAuthor'), author))
        elif int(seqnum) == 2: 
            graph.add((paper, rdflib.URIRef(nss['base'] + 'MAG_secondAuthor'), author))
        elif int(seqnum) == 3: 
            graph.add((paper, rdflib.URIRef(nss['base'] + 'MAG_thirdAuthor'), author))
        # rest doesnt matter much (assumption)

        
        # paper - affiliation (of author)
        #graph.add((paper, rdflib.URIRef(nss['dcterms'] + 'creator'), affiliation))
        #graph.add((paper, rdflib.URIRef(nss['SWRC'] + 'creator'), affiliation))
        #graph.add((affiliation, rdflib.URIRef(nss['foaf'] + 'maker'), paper))
        #graph.add((affiliation, rdflib.URIRef(nss['foaf'] + 'made'), paper))

def paperKeywordsHandler(graph, nss, f):
    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        paperId = rawString(terms[0])
        keyword = rawString(terms[1])
        fieldOfStudyId = rawString(terms[2])

        # nodes
        paper = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + paperId)
        fieldOfStudy = rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + fieldOfStudyId)
        keywordNode = rdflib.Literal(keyword, lang='en')

        # paper - topic
        graph.add((paper, \
                   rdflib.URIRef(nss['foaf'] + 'topic'), \
                   keywordNode))

        # fieldOfStudy - topic
        graph.add((fieldOfStudy, \
                   rdflib.URIRef(nss['foaf'] + 'topic'), \
                   keywordNode))

def paperReferenceHandler(graph, nss, f):
    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        paperId = rawString(terms[0])
        refId = rawString(terms[1])

        # nodes
        paper = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + paperId)
        ref = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + refId)

        # paper - reference
        graph.add((paper, \
                   rdflib.URIRef(nss['bibo'] + 'cites'), \
                   ref))
        graph.add((ref, \
                   rdflib.URIRef(nss['bibo'] + 'isReferencedBy'), \
                   paper))

def paperUrlsHandler(graph, nss, f):
    for line in f:
        terms = line.decode('utf-8').strip().split('\t')

        paperId = rawString(terms[0])
        url = rawString(terms[1])

        # nodes
        paper = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + paperId)
        url = rdflib.Literal(url, datatype=rdflib.URIRef(nss['xsd'] + 'anyURI'))

        # paper - url
        graph.add((paper, \
                   rdflib.URIRef(nss['rdfs'] + 'seeAlso'), \
                   url))

def rawString(string):
    return re.sub('\s+', ' ', re.sub(r'\"', r'\\"', re.sub(r'\\', r'\\\\', string)))

if __name__ == "__main__":
    main(sys.argv[1:])
