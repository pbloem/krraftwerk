#!/usr/bin/env python3

import sys
import os
import re
import getopt
import zipfile
from datetime import datetime
import rdflib
from writer import writer

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
    nsmgr.bind('foaf', rdflib.Namespace('http://xmlns.com/foaf/0.1/'))


    nss = dict(nsmgr.namespaces())

    with zipfile.ZipFile(ifile, 'r') as zfile:
        # with zfile.open('2016KDDCupSelectedAffiliations.txt') as zf:
        #    kddAffiliationsHandler(graph, nss, zf)
        # with zfile.open('2016KDDCupSelectedPapers.txt') as zf:
        #    kddPapersHandler(graph, nss, zf)
        with zfile.open('Affiliations.txt') as zf:
            affiliationsHandler(graph, nss, zf)
            
        # TODO Add other handlers

    return graph


def kddAffiliationsHandler(graph, nss, f):
    for line in f:
        terms = line.split()

        ident = rawString(terms[0].decode("utf-8"))
        name = rawString(' '.join([s.decode("utf-8") for s in terms[1:]]))

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

def affiliationsHandler(graph, nss, f):
    for line in f:
        terms = line.split()

        ident = rawString(terms[0].decode("utf-8"))
        name = rawString(' '.join([s.decode("utf-8") for s in terms[1:]]))

        # affiliation node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Affiliation_' + ident)
        label = rdflib.Literal('Affiliation \\"{}\\"'.format(name.encode('utf-8')), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        # type
        tnode = rdflib.URIRef(nss['SWRC'] + 'Organization')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node of affiliation
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['dcterms'] +'identifier'), idNode))

def authorsHandler(graph, nss, f):
    for line in f:
        terms = line.split()

        ident = rawString(terms[0].decode("utf-8"))
        name = rawString(' '.join([s.decode("utf-8") for s in terms[1:]]))

        # author node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Author_' + ident)
        label = rdflib.Literal('\\"{}\\"'.format(name.encode('utf-8')), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        # type
        tnode = rdflib.URIRef(nss['foaf'] + 'Person')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node of affiliation
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['dcterms'] +'identifier'), idNode))

def conferenceHandler(graph, nss, f):
    for line in f:
        terms = line.split()

        ident = rawString(terms[0].decode("utf-8"))
        name = rawString(' '.join([s.decode("utf-8") for s in terms[1:]]))

        # author node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Author_' + ident)
        label = rdflib.Literal('Conference \\"{}\\"'.format(name.encode('utf-8')), lang='en')
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))

        # type
        tnode = rdflib.URIRef(nss['SWRC'] + 'Conference')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        # id node of affiliation
        idNode = rdflib.Literal(ident, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((root, rdflib.URIRef(nss['dcterms'] +'identifier'), idNode))


def kddPapersHandler(graph, nss, f):
    for line in f:
        terms = line.split()

        ident = rawString(terms[0].decode("utf-8"))
        title = rawString(' '.join([s.decode("utf-8") for s in terms[1:len(terms)-3]]))
        year = rawString(terms[len(terms)-3].decode("utf-8"))
        confID = rawString(terms[len(terms)-2].decode("utf-8"))

        # paper node plus label
        root = rdflib.URIRef(nss['base'] + 'MAG_Paper_' + ident)
        label = ''
        try:
            label = rdflib.Literal('Paper with title \\"{}\\"'.format(title.encode('utf-8')), lang='en')
        except:
            print('Could not parse title: ' + title.encode('utf-8'))     
            
            
        graph.add((root, rdflib.URIRef(nss['rdfs'] + 'label'), label))
        # title
        graph.add((root, rdflib.URIRef(nss['dcterms'] + 'title'), rdflib.Literal(title, lang='en')))
        # year
        ynode = rdflib.Literal(year, datatype=rdflib.URIRef(nss['xsd'] + 'gYear'))   
            
        graph.add((root, rdflib.URIRef(nss['dcterms'] + 'date'), ynode))
        # type
        tnode = rdflib.URIRef(nss['SWRC'] + 'Publication')
        graph.add((root, rdflib.URIRef(nss['rdf'] + 'type'), tnode))

        """
        # id node of conference plus link
        # overwrite if exists
        croot = rdflib.URIRef(nss['base'] + 'MAG_Conference_' + confID)
        idNode = rdflib.Literal(confID, datatype=rdflib.URIRef(nss['xsd'] + 'ID'))
        graph.add((croot, rdflib.URIRef(nss['dcterms'] +'identifier'), idNode))

        SWRC links paper to author and author to conference
        """



def rawString(string):
    return re.sub('\s+', ' ', re.sub(r'\"', r'\\"', re.sub(r'\\', r'\\\\', string)))

if __name__ == "__main__":
    main(sys.argv[1:])
