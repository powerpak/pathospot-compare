#!/bin/bash

#Make the matrix: Need to start with a file ([motif_list]) formatted like this:
#ID, motifs comma separated
#20037,GATC,TCANNNNNGTC,GACNNNNNTGA,CAAAAA,RGAAAGR
#20079,TAAANNNNGTC,GACNNNNTTTA,GAANNNNNNNCTC,GAGNNNNNNNTTC,DGGCCANYR,GGCCBBVNY
#20265,CTTTANNNNNNNTG,CANNNNNNNTAAAG,CAAAAA
#20266,RGACNNNNNRCT,AGYNNNNNGTCY,CAAAAA,HNHAGYNNNNNGCC


#run: sh make_motif_heatmap.sh [motif_list]

module load py_packages
motif_file=$1

python make_motif_matrix.py ${motif_file}

#Remove brackets from the output file
sed 's/\[//g;s/\]//g' motif_matrix.csv > tmp
mv tmp motif_matrix.csv

#Make the heatmap
Rscript make_heatmap.R

