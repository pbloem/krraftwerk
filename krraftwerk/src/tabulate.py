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
import numpy as n

def main(argv):
    ifile = ''
    ofile = ''
    conference = ''

    try:
        opts, args = getopt.getopt(argv, "d:f:hi:o:c:", ["if=", "of=", "format=", "default_namespace="])
    except getopt.GetoptError, exc:
        print(exc.msg)
        print('tabulate.py -c <conference-name> -i <input dir> [-d <default namespace> -o <outputfile> -f <serialization format>]')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(str('A tool to translate the Microsoft Academic Graph, to its Semantic Web equivalent.\nUsage:\n\t' +
                      'tabulate.py -c <conference-name> -i <inputdir> [-d <default namespace> -o <outputfile> -f <serialization format>]'))
            sys.exit(0)
        elif opt in ("-i", "--ifile"):
            ifile = arg
        elif opt in ("-o", "--ofile"):
            ofile = arg
        elif opt in ("-c", "--conference"):
            conference = arg
            
    if ifile == '':
        print('Missing required input -i.\nUse \'tabulate.py -h\' for help.')
        sys.exit(1)
        
    if ifile == '':
        print('Missing required input -c.\nUse \'tabulate.py -h\' for help.')
        sys.exit(1)

    if ofile == '' and ifile != '':
        ofile = os.getcwd() + '/' + re.sub(r'^(?:.*/)?(.*)\..*$', r'\1', ifile) + '-{}'.format(str(datetime.now()))
    else:
        ofile = os.getcwd() + '/' + 'output.{}.{}'.format(conference,str(datetime.now()))

    # Read relevant papers
    paperIDs = set()
    yeartopapers = {}
    papertoyear = {}
    
    print('reading relevant papers')
    with open(ifile + '/2016KDDCupSelectedPapers.txt') as zf:            
        for line in zf:
            terms = line.decode('utf-8').strip().split('\t')

            ident = rawString(terms[0])
            title = rawString(terms[1])
            year = rawString(terms[2])
            confID = rawString(terms[3])
            confShortName = rawString(terms[4])
        
            if confShortName == conference:
                if not year in yeartopapers:
                    yeartopapers[year] = set()
                yeartopapers[year].add(ident)
                
                if not ident in papertoyear:
                    papertoyear[ident] = year
                papertoyear[ident] = year

    years = sorted(yeartopapers.keys())

    affiliations = []
    affiliationsSet = set()

    print('reading affiliations')
    with open(ifile + '/2016KDDCupSelectedAffiliations.txt') as zf:            
        for line in zf:
            terms = line.decode('utf-8').strip().split('\t')

            ident = rawString(terms[0])
            name = rawString(terms[-1])
            
            affiliations.append(ident)
            affiliationsSet.add(ident)
                

                
    # Read paper auth affiliations and tabulate scores
    progress = 0
    paa = {}
    print('checking affiliations')
    with open(ifile + '/SelectedPaperAuthorAffiliations.txt') as zf:
        for line in zf:
            if progress % 10000 == 0:
                sys.stdout.write('\r ' + str(progress) + ' paper/author affiliations read.')
    
            terms = line.decode('utf-8').strip().split('\t')

            progress = progress + 1
             
            paperID = rawString(terms[0])
            authorID = rawString(terms[1])
            affiliationID = rawString(terms[2])
            
            if not paperID in paa:
                paa[paperID] = {}
            if not authorID in paa[paperID]:
                paa[paperID][authorID] = set()
            paa[paperID][authorID][affiliationID]
    
    # set up the score matrix
    scores = n.zeros((len(affiliations), len(yeartopapers.keys())))
    
    print('computing scores')
    for paper_id in paa.keys():
        per_author = 1.0 / len(paa[paper_id].keys())
        
        paper_year = papertoyear[paper_id]
        year_index = years.index(paper_year) 
        
        for author_id in paa[paper_id].keys():
            per_affiliation = per_author / float(len(paa[paper_id][author_id].keys))
            
            for affiliation_id in paa[paper_id][author_id].keys():
                affiliation_index = affiliations.index(affiliation_id)
                
                scores[affiliation_index, year_index] += per_affiliation
    
    print(scores)
    
def rawString(string):
    return re.sub('\s+', ' ', re.sub(r'\"', r'\\"', re.sub(r'\\', r'\\\\', string)))

if __name__ == "__main__":
    main(sys.argv[1:])