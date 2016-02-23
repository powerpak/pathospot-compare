#!/usr/bin/env python

import sys

try:
    infile = open(sys.argv[1])
    outfile = open(sys.argv[2], 'w')
    num_genomes = sys.argv[3]
except IndexError:
    sys.stderr.write('''maf2fasta.py
Takes a .maf alignment file and converts it into a concatonated FASTA
of alignments containing all genomes.

USAGE: maf2fasta.py input.maf output.fa number_of_genomes
''')


getit = False
seqDict = {}

for line in infile:
    if line.startswith('a '):
        if line.split()[3] == 'mult=' + sys.argv[3]:
            getit = True
        else:
            getit = False
    if line.startswith('s ') and getit:
        s, name, score, start, strand, size, seq = line.split()
        name = name.split('.')[0]
        if not name in seqDict:
            seqDict[name] = ''
        seqDict[name] += seq

if len(seqDict) != int(num_genomes):
    sys.stderr.write('No alignments found containing all genomes.\n')
    sys.exit()

for i in seqDict:
    outfile.write('>' + i + '\n')
    for j in range(0, len(seqDict[i]), 80):
        outfile.write(seqDict[i][j:j+80] + '\n')
