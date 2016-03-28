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

#
#
#

def main(argv):
    ifile = ''
    ofile = ''
    conference = ''

    try:
        opts, args = getopt.getopt(argv, "d:f:hi:o:", ["if=", "of=", "format=", "default_namespace="])
    except getopt.GetoptError as error:
        print(error.strerror)
        print('tabulate.py -c <conference-name> -i <inputfile> [-d <default namespace> -o <outputfile> -f <serialization format>]')
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
    
    print('reading relevant papers')
    with zipfile.ZipFile(ifile, 'r') as zfile:
        with zfile.open('2016KDDCupSelectedPapers.txt') as zf:            
            for line in zf:
                terms = line.decode('utf-8').strip().split('\t')

                ident = rawString(terms[0])
                title = rawString(terms[1])
                year = rawString(terms[2])
                confID = rawString(terms[3])
                confShortName = rawString(terms[4])
            
                if confShortName == conference:
                    if not yeartopapers[year]:
                        yeartopapers[year] = set()
                    yeartopapers[year].add(ident)
                
    for year in yeartopapers.keys():
        print(year + ' has ' + len(yeartopapers[year]) + ' papers.')          
        
              
    # Read paper auth affiliations and tabulate scores
    
    
    
def rawString(string):
    return re.sub('\s+', ' ', re.sub(r'\"', r'\\"', re.sub(r'\\', r'\\\\', string)))

if __name__ == "__main__":
    main(sys.argv[1:])