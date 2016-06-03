#!/usr/bin/env python3

import sys
import os
import getopt
import time
from datetime import datetime
import rdflib
from writer import writer
import translator
import schema
import multiprocessing
from multiprocessing import Process, Manager
from io import StringIO


NUM_CORES_PER_CPU = 4
NUM_OF_WORKERS = multiprocessing.cpu_count() * NUM_CORES_PER_CPU 
CHUNKSIZE = 5e5

def main(argv):
    idir = ''
    ofile = ''
    default_ns = 'http://www.example.org/'
    sformat = 'turtle'
    gen_ontology = False

    try:
        opts, args = getopt.getopt(argv, "d:f:hi:o:", ["dir=", "of=", "format=", "default_namespace=", \
                                                       "generate_ontology"])
    except getopt.GetoptError:
        print('mag2rdf -i <input directory> [-d <default namespace> -o <outputfile> -f <serialization format>' +
              '--generate_ontology]')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(str('A tool to translate the Microsoft Academic Graph, to its Semantic Web equivalent.\nUsage:\n\t' +
                      'mag2rdf.py -i <input directory> [-d <default namespace> -o <outputfile> -f <serialization format>' +
                      '--generate_ontology]'))
            sys.exit(0)
        elif opt in ("-i", "--dir"):
            idir = arg
        elif opt in ("-o", "--of"):
            ofile = arg
        elif opt in ("-d", "--default_namespace"):
            default_ns = arg
        elif opt in ("--generate_ontology"):
            gen_ontology = True
        elif opt in ("-f", "--format"):
            sformat = arg

    if idir == ''and gen_ontology is False:
        print('Missing required input (flags).\nUse \'MAG2RDF.py -h\' for help.')
        sys.exit(1)

    if not idir.endswith('/'):
        idir = idir + '/'

    if ofile == '':
        ofile = os.getcwd() + '/' + 'output-{}'.format(str(datetime.now()))

    dataGraph = None
    schemaGraph = None
    if idir != '':
        dataGraph = translate(idir, default_ns)
    if gen_ontology:
        schemaGraph = writeOntologyGraph(default_ns)

    if dataGraph is not None:
        writer.write(dataGraph, ofile + extOf(sformat), sformat)
    if schemaGraph is not None:
        writer.write(schemaGraph, ofile + '_Ontology' + extOf(sformat), sformat)


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


def writeOntologyGraph(ns):
    # create graph instance
    graph = rdflib.Graph(identifier='Microsoft_Academic_Graph.Schema')
    graph.open('./store', create = True)

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
    nsmgr.bind('geo', rdflib.Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#'))
    nsmgr.bind('bibo', rdflib.Namespace('http://purl.org/ontology/bibo/'))
    nsmgr.bind('void', rdflib.Namespace('http://rdfs.org/ns/void#'))

    nss = dict(nsmgr.namespaces())

    schema.generate(graph, nss)

    return graph



def translate(idir, ns):
    manager = Manager()  # manager for multiprocessing

    # create graphdata graph instance
    graph = rdflib.Graph(identifier='Microsoft_Academic_Graph.Data')
    graph.open('./store', create = True)

    # set namespaces
    nsmgr = rdflib.namespace.NamespaceManager(graph)
    nsmgr.bind('base', rdflib.Namespace(ns))
    nsmgr.bind('skos', rdflib.Namespace('http://www.w3.org/2004/02/skos/core#'))
    nsmgr.bind('void', rdflib.Namespace('http://rdfs.org/ns/void#'))
    nsmgr.bind('dcterms', rdflib.Namespace('http://purl.org/dc/elements/1.1/'))
    nsmgr.bind('foaf', rdflib.Namespace('http://xmlns.com/foaf/0.1/'))

    nss = dict(nsmgr.namespaces())

    print('initiating graph...')
    translator.init(graph, nss)

    #with open(idir + '2016KDDCupSelectedAffiliations.txt') as f:
        #print('processing affiliations...')
        #affiliations = translator.f2016KDDCupSelectedAffiliationsHandler(graph, nss, f)
    
    # gather all KDD selected papers plus their conferences (== targets) plus year
    with open(idir + '2016KDDCupSelectedPapers.txt') as f:
        print('processing 2016 papers...')
        kddPapers, kddConfs, kddYears = zip(*translator.f2016KDDCupSelectedPapersHandler(graph, nss, f))
    print()
    print('found {} papers, with conferences, and years'.format(len(kddPapers)))
    

    # add conference instances from from all target conferences from year > 2010
    with open(idir + 'ConferenceInstances.txt') as f:
        print('processing conference instances...')
        translator.fKDDConferenceInstancesHandler(graph, nss, f, kddConfs, kddYears, kddPapers)

    del kddYears
    print()

    # add papers from target conference instances
    kddJournals = manager.list()
    paperConfIndex = manager.dict()
    mtrun(graph, nss, manager, idir + 'Papers.txt', 'fKDDPapersHandler', din=[kddPapers, kddConfs],\
                                                                         dout=[kddJournals, paperConfIndex])
    kddJournals = set(kddJournals) # rmv duplicates
    print()
    print('found {} KDD journals and {} Non-KDD paper/conference pairs'.format(len(kddJournals), len(paperConfIndex)))


    # gather all relevant fields of study for target conferences
    kddKeywords = manager.list()
    allKeywords = manager.dict()
    mtrun(graph, nss, manager, idir + 'PaperKeywords.txt', 'fPaperKeywordsHandler', din=[kddPapers, paperConfIndex],\
                                                                         dout=[kddKeywords, allKeywords])
    kddKeywords = set(kddKeywords) # rmv duplicates
    del paperConfIndex
    print()
    print('found {} KDD keywords and {} Non-KDD conference/keywords pairs'.format(len(kddKeywords), len(allKeywords)))


    print('processing keyword graph...')
    kwgraph, nrOfKws = fieldOfStudyParser(idir, nss)  # keyword hierarchy graph
    print()
    print('found {} keywords in total'.format(nrOfKws))
    print('expanding KDD Keywords...')
    kddKeywords = translator.downwardsExpandKeywordTree(kwgraph, nss, kddKeywords)
    print()
    print('expanded to {} KDD keywords'.format(len(kddKeywords)))
    print('expanding non-KDD Keywords...')
    for k,v in allKeywords.items():
        allKeywords[k] = translator.downwardsExpandKeywordTree(kwgraph, nss, v)

    kddConfs = set(kddConfs)  # rmv duplicates
    l = len(kddConfs)
    # all potentially interesting conferences
    print('expanding conferences...')
    allConfs = translator.expandConferences(kddKeywords, allKeywords, nrOfKws)
    allConfs.extend(kddConfs)
    del kddKeywords
    del kddConfs
    print()
    print('expanded from {} to {} conferences'.format(l, len(allConfs)))
    print(allConfs)
    
    # add papers from related conferences
    paperYearConfs = manager.list()
    journals = manager.list()
    mtrun(graph, nss, manager, idir + 'Papers.txt', 'fPapersHandler', din=[kddPapers, allConfs],\
                                                                         dout=[paperYearConfs, journals])
    journals = set(journals) # rmv duplicates
    journals = journals.union(kddJournals)
    papers, years, confs = zip(*paperYearConfs)

    print()
    print('found {} additional journals and {} papers'.format(len(journals), len(papers)))
    
    del paperYearConfs
    del kddJournals

    # add conference instances from from all related conferences from year > 2010
    l = len(graph)
    with open(idir + 'ConferenceInstances.txt') as f:
        print('expanding conference instances...')
        translator.fConferenceInstancesHandler(graph, nss, f, allConfs, years, papers, confs)
    print()
    print('expanded graph with {} conference instance triples'.format(len(graph)-l))

    ### rest is generic ###
    
    papers = list(papers)
    papers.extend(kddPapers)
    del kddPapers
    print()
    print('expanded to {} papers'.format(len(papers)))

    # add conference organizations  
    l0 = len(graph)
    with open(idir + 'Conferences.txt') as f:
        print('processing conferences...')
        translator.fConferencesHandler(graph, nss, f, allConfs)
    print()
    print('expanded graph with {} conference triples'.format(len(graph)-l0))

    # add journals from papers
    l0 = len(graph)
    with open(idir + 'Journals.txt') as f:
        print('processing journals...')
        translator.fJournalsHandler(graph, nss, f, journals)
    print()
    print('expanded graph with {} journal triples'.format(len(graph)-l0))

    # add nr of citations by others
    l0 = len(graph)
    paperRefs = manager.dict()
    mtrun(graph, nss, manager, idir + 'PaperReferences.txt', 'fPaperReferencesHandler', din=[papers],\
                                                                         dout=[paperRefs])
    translator.fPaperRefCount(graph, nss, paperRefs)
    print()
    print('expanded graph with {} reference triples'.format(len(graph)-l0))
    
    # not relevant feature
    #with open(idir + 'PaperUrls.txt') as f:
    #    translator.fPaperUrlsHandler(graph, nss, f, papers)
    
  
    # add authors from papers + affiliation
    authors = manager.list()
    affiliations = manager.list()
    mtrun(graph, nss, manager, idir + 'PaperAuthorAffiliations.txt', 'fPaperAuthorAffiliationsHandler', din=[papers],\
                                                                         dout=[authors, affiliations])
    authors = set(authors)
    affiliations = set(affiliations)
    print()
    print('found {} authors and {} affiliations'.format(len(authors), len(affiliations)))
    
    with open(idir + 'Affiliations.txt') as f:
        print('processing affiliations...')
        translator.fAffiliationsHandler(graph, nss, f, affiliations)
   
    # add names 
    mtrun(graph, nss, manager, idir + 'Authors.txt', 'fAuthorsHandler', din=[authors],\
                                                                         dout=[])
    
    print()
    print('{} triples in total'.format(len(graph)))
    return graph

def mtrun(graph, nss, manager, fname, func, **arg):
    din = arg['din'] if 'din' in arg else None
    dout = arg['dout'] if 'dout' in arg else None

    # initialize shared variables
    subgraphs = manager.list()
    work = manager.Queue(NUM_OF_WORKERS)

    # start for workers    
    pool = []
    for i in range(NUM_OF_WORKERS):
        p = Process(target=getattr(translator, func),\
                    args=(nss, *din, work, subgraphs, *dout))
        p.start()
        pool.append(p)

    # produce data
    with open(fname) as f:
        print('processing {}...'.format(fname))
        chunk = StringIO()
        for i, line in enumerate(f,1):
            chunk.write(line)

            if not i%CHUNKSIZE:
                chunk.seek(0)
                work.put(chunk)

                sys.stdout.write('\r ' + str(i) + ' lines read ')
                chunk = StringIO()

                time.sleep(0.01)

        if i%CHUNKSIZE:  # anything left?
            chunk.seek(0)
            work.put(chunk)

            sys.stdout.write('\r ' + str(i) + ' lines read ')
            time.sleep(0.01)

        # terminate workers
        for worker in range(NUM_OF_WORKERS):
            work.put(None)
            time.sleep(0.01)

    print()
    # join shared variables
    for p in pool:
        p.join()

    # merge graphs
    for subgraph in subgraphs:
        graph += subgraph

def fieldOfStudyParser(idir, nss):
    # create fos graph instance
    graph = rdflib.Graph(identifier='Microsoft_Academic_Graph.FieldsOfStudy')
    graph.open('./store', create = True)

    # set namespaces
    #nsmgr = rdflib.namespace.NamespaceManager(graph)
    #nsmgr.bind('base', rdflib.Namespace(ns))
    #nsmgr.bind('skos', rdflib.Namespace('http://www.w3.org/2004/02/skos/core#'))

    #nss = dict(nsmgr.namespaces())
    length = 0
    print('importing fields of study')
    with open(idir + 'FieldsOfStudy.txt') as f:
        length = translator.fFieldsOfStudyHandler(graph, nss, f)

    print('importing fields of study hierarchy')
    with open(idir + 'FieldOfStudyHierarchy.txt') as f:
        translator.fFieldOfStudyHierarchyHandler(graph, nss, f)

    return (graph, length)

if __name__ == "__main__":
    main(sys.argv[1:])
