import sys
import os
import re
import math
import random
import getopt
import zipfile
from datetime import datetime
import rdflib
from dateutil import parser
import numpy as n

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from sklearn import cross_validation
from sklearn import datasets
from sklearn import svm
from sklearn import kernel_ridge
from sklearn import linear_model

def main(argv):
    ifile = ''

    try:
        opts, args = getopt.getopt(argv, "d:f:hi:", ["if=", "of=", "format=", "default_namespace="])
    except getopt.GetoptError, exc:
        print(exc.msg)
        print('make_prediction.py -i <input dir> [-d <default namespace> -o <outputfile> -f <serialization format>]')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(str('A first go at predictions for the KDD 2016 cup.\nUsage:\n\t' +
                      'make_predictions.py -i <inputdir> [-d <default namespace> -o <outputfile> -f <serialization format>]'))
            sys.exit(0)
        elif opt in ("-i", "--ifile"):
            ifile = arg
        elif opt in ("-o", "--ofile"):
            ofile = arg        
            
    if ifile == '':
        print('Missing required input -i.\nUse \'tabulate.py -h\' for help.')
        sys.exit(1)

    # Read relevant papers
    paper_ids = set()
    years = set()
    yctopapers = {}
    papertoyear = {}
    papertoconf = {}
    conftoyears = {}
    nametoid = {}

    
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
            
            nametoid[conf_name] = conf_id

    
    print(str(len(paper_ids)) + ' papers')
    print(nametoid['SIGIR'])

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
            # if progress % 10000 == 0:
            #    sys.stdout.write('\r ' + str(progress) + ' paper/author affiliations read.')
            progress = progress + 1
    
            terms = line.decode('utf-8').strip().split('\t')
             
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
            
            for affiliation_id in paa[paper_id][author_id]:
                
                if affiliation_id in affiliations_set:
                    if not (affiliation_id, conf, year) in acytoscore:
                        acytoscore[affiliation_id, conf, year] = 0.0
                    acytoscore[affiliation_id, conf, year] += per_affiliation

    print(str(len(acytoscore.keys())) + ' triples')
                    
#    with open('./table.csv', 'w') as output:
#        for (affiliation, conf_name, year), score in acytoscore.items():
#            output.write('"{}","{}",{}, {}\n'.format(affiliation, conf_name, int(year), score))
#            
#    output.close()
    
    output = open('./results.tsv', 'w')
    # Find length of matrix  
    for (conference, use_all, num_previous) in [('SIGIR', True, 1), ('SIGMOD', False, 3), ('SIGCOMM', True, 1)]:
    
        num_instances = 0;
        for (affiliation, conf_name, year), score in acytoscore.items():
            if use_all or conf_name == conference:
                if exist_previous(num_previous, affiliation, conf_name, year, acytoscore):
                    num_instances += 1
            
        print('dataset will have {} instances'.format(num_instances)) 
            
        data = n.zeros((num_instances, num_previous + 2))
    
        instance = 0            
        for (affiliation, conf_name, year), score in acytoscore.items():
            if conference == None or conf_name == conference:
                if exist_previous(num_previous, affiliation, conf_name, year, acytoscore):
                    for i in range(num_previous):
                        prevscore = acytoscore[affiliation, conf_name, str(int(year) - i - 1)]
                        data[instance, i] = prevscore
                    data[instance, num_previous + 1] = score
                    instance += 1
    
        x = data[:, 0:num_previous]
        y = data[:, num_previous+1]
        
        reg = kernel_ridge.KernelRidge(kernel='rbf', alpha=0.001)
        model = reg.fit(x, y)
        
        # print out predictions
        
        conf_id = nametoid[conference]
        target_year = 2015
        for affiliation_id in affiliations:
            x_line = n.zeros((1, num_previous))
            for i in range(num_previous):
                if (affiliation_id, conference, str(int(target_year) - i - 1)) in acytoscore:
                    prevscore = acytoscore[affiliation_id, conference, str(int(target_year) - i - 1)]
                else:
                    prevscore = 0.0
                x_line[0, i] = prevscore
                print(x_line)
                
            score = model.predict(x_line)[0] + random.uniform(0.0, 0.0000001)
            output.write('{}\t{}\t{}\n'.format(conf_id, affiliation_id, score))
    
    output.close()
    print('finished.')

def exist_previous(n, affiliation, conf_name, year, acytoscore):
    for i in range(1, n + 1):
        if not (affiliation, conf_name, str(int(year) - i)) in acytoscore:
            return False;
    return True;

def rawString(string):
    return re.sub('\s+', ' ', re.sub(r'\"', r'\\"', re.sub(r'\\', r'\\\\', string)))

if __name__ == "__main__":
    main(sys.argv[1:])