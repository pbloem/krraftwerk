import sys
import os
import re
import math
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
    ofile = ''
    conference_in = ''

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
        elif opt in ("-c", "--conference"):
            conference_in = str(arg).upper()
            
    print('using conference: {}'.format(conference_in))        
            
    if ifile == '':
        print('Missing required input -i.\nUse \'tabulate.py -h\' for help.')
        sys.exit(1)
        
    if ifile == '':
        print('Missing required input -c.\nUse \'tabulate.py -h\' for help.')
        sys.exit(1)

    if ofile == '' and ifile != '':
        ofile = os.getcwd() + '/' + re.sub(r'^(?:.*/)?(.*)\..*$', r'\1', ifile) + '-{}'.format(str(datetime.now()))
    else:
        ofile = os.getcwd() + '/' + 'output.{}.{}'.format(conference_in,str(datetime.now()))

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
            
    print(str(len(paper_ids)) + ' papers')

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

    models = []
    errors = []
    inputs = []
    
    test_year = -1
    
    # Find length of matrix  
    for conference in [None, conference_in]:
        for num_previous in range(1, 10):
    
            num_instances = 0;
            for (affiliation, conf_name, year), score in acytoscore.items():
                if int(year) != test_year:
                    if conference == None or conf_name == conference:
                        if exist_previous(num_previous, affiliation, conf_name, year, acytoscore):
                            num_instances += 1
                    
            print('dataset will have {} instances'.format(num_instances))
            if num_instances < 3:
               break 
                
            data = n.zeros((num_instances, num_previous + 2))
        
            instance = 0            
            for (affiliation, conf_name, year), score in acytoscore.items():
                if int(year) != test_year:
                    if conference == None or conf_name == conference:
                        if exist_previous(num_previous, affiliation, conf_name, year, acytoscore):
                            data[instance, 0] = float(int(year))
                            for i in range(1, num_previous + 1):
                                prevscore = acytoscore[affiliation, conf_name, str(int(year) - i)]
                                data[instance, i] = prevscore
                            data[instance, num_previous + 1] = score
                            instance += 1
                        
            n.set_printoptions(suppress=True)
            n.set_printoptions(threshold=50)
        
            x = data[:, 1:num_previous+1]
            y = data[:, num_previous+1]
            
            # print(data)
            # print(x)
            # print(y)
            
            # model = svm.SVR(kernel='linear', gamma=0.1, C=10)
            # model = linear_model.LinearRegression()
            model = kernel_ridge.KernelRidge(kernel='rbf', alpha=0.001)
            
            # scores have sign flipped
            scores = cross_validation.cross_val_score(model, x, y, scoring='mean_squared_error', cv=5)
            rmse = math.sqrt(-sum(scores)/len(scores))
            
                # make a plot
            if num_previous == 1 and conference == None:
                fig = plt.figure()
                ax = fig.add_subplot(111)
                ax.scatter(data[:,1], data[:,2], c=data[:,0], linewidth=0, alpha=0.1)
    
                res = 1000            
                xplot = n.linspace(0, 0.2, res).reshape(res, 1)
                yplot = model.fit(x, y).predict(xplot)
                ax.plot(xplot,yplot) 
                
                plt.savefig('plot.png')
            
            print('{}: {}'.format(num_previous, rmse))
            
            models.append(model.fit(x, y))
            errors.append(rmse)
            inputs.append(x.shape[1])
    
    for i in range(len(models)):        
        print('{}\t{}\t{}'.format(models[i], errors[i], inputs[i]))
    
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