#!/usr/bin/env python3

import sys
import os
import re
import getopt
import zipfile
from datetime import datetime
import rdflib
from writer import writer
import dateutil 
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
        with zfile.open('ConferencesInstances.txt') as zf:
            conferenceInstancesHandler(graph, nss, zf)
                                                       
        # TODO Add other handlers

    return graph


def kddAffiliationsHandler(graph, nss, f):
    for line in f:
        terms = line.split('\t')

        ident = rawString(terms[0].decode('utf-8'))
        name = rawString(terms[-1].decode('utf-8'))

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
        terms = line.split('\t')

        ident = rawString(terms[0].decode('utf-8'))
        title = rawString(terms[1].decode('utf-8'))
        year = rawString(terms[2].decode("utf-8"))
        confID = rawString(terms[3].decode("utf-8"))
        #confShortName = rawString(terms[4].decode("utf-8"))

        # paper node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + ident)
        label = rdflib.Literal('Paper with title \\"{}\\"'.format(title.encode('utf-8')), lang='en')            
            
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
        terms = line.split('\t')

        ident = rawString(terms[0].decode("utf-8"))
        name = rawString(terms[1].decode("utf-8"))

        # affiliation node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Affiliation_' + ident)
        label = rdflib.Literal('Affiliation \\"{}\\"'.format(name.encode('utf-8')), lang='en')
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
        terms = line.split('\t')

        ident = rawString(terms[0].decode('utf-8'))
        name = rawString(terms[1].decode('utf-8'))

        # author node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Author_' + ident)
        label = rdflib.Literal('\\"{}\\"'.format(name.encode('utf-8')), lang='en')
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
        terms = line.split('\t')

        ident = rawString(terms[0].decode('utf-8'))
        name = rawString(terms[2].decode('utf-8'))
        
        # shortName = rawString(terms[1].decode('utf-8'))
        # TODO: add?

        # Conference node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Conference_' + ident)
        label = rdflib.Literal('Conference \\"{}\\"'.format(name.encode('utf-8')), lang='en')
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
        terms = line.split('\t')

        organizationId = rawString(terms[0].decode("utf-8"))
        ident = rawString(terms[1].decode("utf-8"))
        #shortName = rawString(terms[2].decode("utf-8")) # not used
        name = rawString(terms[3].decode("utf-8"))
        location = rawString(terms[4].decode("utf-8"))
        url = rawString(terms[5].decode("utf-8"))
        startdate = dateutil.parser.parse(terms[6].decode("utf-8")) if len(terms) >= 7 else None
        enddate = dateutil.parser.parse(terms[7].decode("utf-8")) if len(terms) >= 8 else None
        abstractdate = dateutil.parser.parse(terms[8].decode("utf-8")) if len(terms) >= 9 else None
        subdate = dateutil.parser.parse(terms[9].decode("utf-8")) if len(terms) >= 10 else None
        notdate = dateutil.parser.parse(terms[10].decode("utf-8")) if len(terms) >= 11 else None
        finaldate = dateutil.parser.parse(terms[11].decode("utf-8")) if len(terms) >= 12 else None
        
        # instance node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_ConferenceInstance_' + ident)
        label = rdflib.Literal('Conference instance \\"{}\\"'.format(name.encode('utf-8')), lang='en')
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
        geoURI =geoIndex.resolve(location)
        if geoURI is None:
            loc = rdflib.Literal(location)
        else:
            loc = rdflib.URIRef(geoURI) # range should actually be geoThing (coordinates)

        graph.add((root, rdflib.URIRef(nss['swc'] + 'hasLocation'), loc))


        # to facilitate easy queries
        year = rdflib.Literal(startdate.year, datatype=rdflib.URIRef(nss['xsd'] + 'gYear'))
        graph.add((root, rdflib.URIRef(nss['dcterms'] + 'date'), year))

        # Start date 
        startdateLiteral = rdflib.Literal(startdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
        graph.add((root, rdflib.URIRef(nss['conf'] + 'startDate'), startdateLiteral))
        
        # end date 
        enddateLiteral = rdflib.Literal(enddate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
        graph.add((root, rdflib.URIRef(nss['conf'] + 'endDate'), enddateLiteral))

        # abstract date 
        abstractdateLiteral = rdflib.Literal(abstractdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
        graph.add((root, rdflib.URIRef(nss['conf'] + 'abstractDueOn'), abstractdateLiteral))
        graph.add((root, rdflib.URIRef(nss['conf'] + 'registrationDueOn'), abstractdateLiteral))
        
        
        ### A better solution is needed here ###
        
        # submission date 
        subLiteral = rdflib.Literal(subdate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
        graph.add((root, rdflib.URIRef(nss['conf'] + 'paperDueOn'), subLiteral))
 
        # final date 
        finalLiteral = rdflib.Literal(finaldate.isoformat(), datatype=rdflib.URIRef(nss['xsd'] + 'Date'))
        graph.add((root, rdflib.URIRef(nss['conf'] + 'paperDueOn'), finalLiteral))

def fieldsOfStudyHandler(graph, nss, f):
    for line in f:
        terms = line.split('\t')

        ident = rawString(terms[0].decode("utf-8"))
        name = rawString(terms[1].decode("utf-8"))

        # add node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudy_' + ident)
        label = rdflib.Literal('Field of study \\"{}\\"'.format(name.encode('utf-8')), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))
        graph.add((root, rdflib.URIRef(nss['skos'] + 'prefLabel'), rdflib.Literal(name, lang='en')))

        # type
        tnode = rdflib.URIRef(nss['SWRC'] + 'Topic')
        tnode_alt = rdflib.URIRef(nss['skos'] + 'Concept')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode_alt))

        # id node
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['dcterms'] +'identifier'), idNode))

# skosified
def fieldOfStudyHierarchyHandler(graph, nss, f):
    root = rdflib.URIRef(nss['base'] + 'MAG_FieldOfStudyHierarchy')
    tnode = rdflib.URIRef(nss['skos'] + 'ConceptScheme')
    graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))
  
    for line in f:
        terms = line.split('\t')

        childId = rawString(terms[0].decode("utf-8"))
        childLvl = rawString(terms[1].decode("utf-8"))[1:]
        parentId = rawString(terms[2].decode("utf-8"))
        parentLvl = rawString(terms[3].decode("utf-8"))[1:]
        confidence = rawString(terms[4].decode("utf-8"))

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

        if int(parentLvl) - int(childLvl) == 1:
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


def rawString(string):
    return re.sub('\s+', ' ', re.sub(r'\"', r'\\"', re.sub(r'\\', r'\\\\', string)))

if __name__ == "__main__":
    main(sys.argv[1:])
