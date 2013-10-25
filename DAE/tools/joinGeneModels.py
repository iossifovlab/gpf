#!/bin/env python

# Oct 23nd 2013
# written by Ewa


from GeneModelFiles import *
import os.path
import optparse


parser = optparse.OptionParser(version='%prog version 1.0 23/October/2013')
parser.add_option('--output', help='outfile path', type='string', action='store')
parser.add_option('--g1', help='gene models file path', type='string', action='store')
parser.add_option('--m1', help='gene mapping file', action='store')
parser.add_option('--f1', help='gene models format',  action='store')
parser.add_option('--g2', help='gene models file path', type='string', action='store')
parser.add_option('--m2', help='gene mapping file', action='store')
parser.add_option('--f2', help='gene models format', action='store')
parser.add_option('--g3', help='gene models file path', type='string', action='store')
parser.add_option('--m3', help='gene mapping file', action='store')
parser.add_option('--f3', help='gene models format',  action='store')
parser.add_option('--g4', help='gene models file path', type='string', action='store')
parser.add_option('--m4', help='gene mapping file', action='store')
parser.add_option('--f4', help='gene models format', action='store')
parser.add_option('--g5', help='gene models file path', type='string', action='store')
parser.add_option('--m5', help='gene mapping file', action='store')
parser.add_option('--f5', help='gene models format',  action='store')
parser.add_option('--g6', help='gene models file path', type='string', action='store')
parser.add_option('--m6', help='gene mapping file', action='store')
parser.add_option('--f6', help='gene models format', action='store')

(opts, args) = parser.parse_args()

if opts.output == None:
    raise Exception("The program needs an output file name")

if opts.g1 == None or opts.g2 == None:
    raise Exception("The program needs at least 2 parameters: --g1 and --g2")

gms = [opts.g1, opts.g2, opts.g3, opts.g4, opts.g5, opts.g6]
maps = [opts.m1, opts.m2, opts.m3, opts.m4, opts.m5, opts.m6]
formats = [opts.f1, opts.f2, opts.f3, opts.f4, opts.f5, opts.f6]

GMs = []
for file, gene_map, fmt in zip(gms,maps,formats):
    if file != None:
        if os.path.exists(file) == False:
            raise Exception("The given input - " + file + " file does not exist!")
        sys.stderr.write("Joining: " + file + " .................................\n")
        GMs.append(load_gene_models(file_name=file, gene_mapping_file=gene_map, format=fmt))

x = join_gene_models(*GMs)
x.relabel_chromosomes()
x.save(opts.output)


    
