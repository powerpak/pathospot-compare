import sys
import datetime
import os
from tqdm import tqdm
import subprocess
import numpy as np
import re

USAGE = """
parsnp2table.py
Creates a .tsv of SNV differences between strains from a VCF file produced by parsnp

USAGE: python parsnp2table.py parsnp.vcf output.tsv
"""

# Note, as per https://harvest.readthedocs.io/en/latest/content/parsnp/quickstart.html
# "harvest-tools VCF outputs indels in non standard format.
#  Currently column based, not row based.
#  Excluding indel rows (default behavior) converts file into valid VCF format.
#  this will be updated in future version"

if len(sys.argv) < 3:
    print USAGE
    sys.exit(1)

# Read in the VCF file
with open(sys.argv[1]) as vcf:
    start_reading = False
    total_lines = int(subprocess.check_output(['wc', '-l', sys.argv[1]]).split()[0])
    i = 0
    for line in tqdm(vcf, total=total_lines, desc="Reading VCF file"):
        # Skip all lines until we get to the #CHROM line
        # The first 9 columns are standard VCF columns with allele info
        if line.startswith('#CHROM'):
            # Get the remaining column headers, which are the names of the input sequences
            seq_list = line.split()[9:]
            # Initialize a matrix that can hold all variants for all sequences
            vcf_mat = np.zeros((len(seq_list), total_lines), dtype=np.int16)
            # Start reading rows
            start_reading = True
        elif start_reading:
            # Each cell is an allele for a particular sequence
            vcf_mat[:, i] = map(int, line.split()[9:])
            i += 1
    
dist_mat = np.zeros((len(seq_list), len(seq_list)))
for i, seq1 in tqdm(enumerate(seq_list), total=len(seq_list), desc="Calculating SNV distances"):
    for j, seq2 in enumerate(seq_list):
        dist_mat[i, j] = np.count_nonzero(vcf_mat[i, :] - vcf_mat[j, :])

# Cleanup the names of sequences, which come with unnecessary suffixes from preprocessing steps
seq_list = map(lambda x: re.sub(r'(\.\w+)+$', '', x), seq_list)

# Open the output TSV file and dump the distance 
with open(sys.argv[2], 'w') as out:
    out.write('strains\t' + '\t'.join(seq_list) + '\n')
    for i, seq1 in enumerate(seq_list):
        out.write(seq1 + '\t')
        out.write('\t'.join(map(str, dist_mat[i, :])))
        out.write('\n')
