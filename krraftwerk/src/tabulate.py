import sys
import os
import re
import getopt
import zipfile
from datetime import datetime
import rdflib
from dateutil import parser
import numpy as n

def main(argv):
    ifile = ''
    ofile = ''
    conference = ''

    try:
        opts, args = getopt.getopt(argv, "d:f:hi:o:c:", ["if=", "of=", "format=", "default_namespace="])
    except getopt.GetoptError, exc:
        print(exc.msg)
        print('tabulate.py -i <input dir> [-d <default namespace> -o <outputfile> -f <serialization format>]')
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
    paper_ids = set()
    years = set()
    yctopapers = {}
    papertoyear = {}
    papertoconf = {}
    conftoyears = {}
    
    print('reading relevant papers')
    with open(ifile + '/2016KDDCupSelectedPapers.txt') as zf:            
        for line in zf:
            terms = line.decode('utf-8').strip().split('\t')

            ident = rawString(terms[0])
            title = rawString(terms[1])
            year = rawString(terms[2])
            conf_id = rawString(terms[3])
            conf_name = rawString(terms[4])
            
            if not (year, conf_name) in yctopapers:
                yctopapers[(year, conf_name)] = set()
            yctopapers[year, conf_name].add(ident)
            
            if not conf_name in conftoyears:
                conftoyears[conf_name] = set()
            conftoyears[conf_name].add(year)
                
            papertoyear[ident] = year            
            papertoconf[ident] = conf_name
                
            paper_ids.add(ident)

    affiliations = []
    affiliations_set = set()

    print('reading affiliations')
    with open(ifile + '/2016KDDCupSelectedAffiliations.txt') as zf:            
        for line in zf:
            terms = line.decode('utf-8').strip().split('\t')

            ident = rawString(terms[0])
            name = rawString(terms[-1])
            
            affiliations.append(ident)
            affiliations_set.add(ident)
                    
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
             
            paper_id = rawString(terms[0])
            author_id = rawString(terms[1])
            affiliation_id = rawString(terms[2])
            
            if not paper_id in paa:
                paa[paper_id] = {}
            if not author_id in paa[paper_id]:
                paa[paper_id][author_id] = set()
            paa[paper_id][author_id].add(affiliation_id)
    
    
    print('\ncomputing scores')
    
    acytoscore = {} # (affiliation, conf_name, year) -> score
    
    for paper_id in paper_ids:
        per_author = 1.0 / len(paa[paper_id].keys())
        
        year = papertoyear[paper_id]
        conf = papertoconf[paper_id]
                
        for author_id in paa[paper_id].keys():
            per_affiliation = per_author / float(len(paa[paper_id][author_id]))
            # normalize
            per_affiliation /= float(len(yctopapers[year, conf])) 
            
            for affiliation_id in paa[paper_id][author_id].keys():
                
                if affiliation_id in affiliations_set:
                    if not (affiliation_id, conf, year) in acytoscore:
                        acytoscore[affiliation_id, conf, year] = 0.0
                    acytoscore[affiliation_id, conf, year] += per_affiliation
                    
    with open('./table.csv', 'w') as output:
        for (affiliation, conf_name, year), score in acytoscore:
            output.write('"{}","{}",{}, {}'.format(affiliation, conf_name, int(year), score))
    
def rawString(string):
    return re.sub('\s+', ' ', re.sub(r'\"', r'\\"', re.sub(r'\\', r'\\\\', string)))

if __name__ == "__main__":
    main(sys.argv[1:])