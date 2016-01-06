#Read in a csv of motifs mrn,motif1,motif2 etc. and output a matrix
#Output: mrn as rows, motifs as columns
import os 
import sys
import numpy as np
import re


motifs=sys.argv[1]
id_mots = {}
all_mots = []
motset = set()
with open(motifs) as f:
	for l in f:
		ll = l.strip().split(',')
		id = ll[0]
		mot = ll[1:]
		for motif in mot:
			all_mots.append(motif)	
			motset.add(motif)
		id_mots.setdefault(id,[]).append(mot)

motset_list = list(motset)
motif_matrix=open("motif_matrix.csv","w")
motif_matrix.write("%s %s\n" % ("id,",motset_list))
for id in id_mots:
	binary = [0] * len(motset)
	motifs = id_mots[id]
	motif1=motifs[0]
	for pos in range(len(motif1)):
		index_of_motif = motset_list.index(motif1[pos])
		binary[index_of_motif]=1
	motif_matrix.write("%s, %s\n" % (id,binary))
