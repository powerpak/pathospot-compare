#!/usr/bin/env python
"""
parsnp2table.py
Creates a .tsv of SNV differences between strains from a VCF file produced by parsnp

USAGE: python parsnp2table.py parsnp.vcf output.tsv
"""

import sys
from tqdm import tqdm
import numpy as np
import re

from pylib.parsnp_vcf import load_parsnp_vcf

# Note, as per https://harvest.readthedocs.io/en/latest/content/parsnp/quickstart.html
# "harvest-tools VCF outputs indels in non standard format.
#  Currently column based, not row based.
#  Excluding indel rows (default behavior) converts file into valid VCF format.
#  this will be updated in future version"

if len(sys.argv) < 3:
    print __doc__
    sys.exit(1)

seq_list, vcf_mat, _ = load_parsnp_vcf(sys.argv[1], progress=True)

# Create the distance matrix. `np.count_nonzero` quickly counts nonzero elements in an np.array
dist_mat = np.zeros((len(seq_list), len(seq_list)))
for i, seq1 in tqdm(enumerate(seq_list), total=len(seq_list), desc="Calculating SNV distances"):
    for j, seq2 in enumerate(seq_list):
        dist_mat[i, j] = np.count_nonzero(vcf_mat[i, :] - vcf_mat[j, :])

# Open the output TSV file and dump the distance 
with open(sys.argv[2], 'w') as out:
    out.write('strains\t' + '\t'.join(seq_list) + '\n')
    for i, seq1 in enumerate(seq_list):
        out.write(seq1 + '\t')
        out.write('\t'.join(map(str, dist_mat[i, :])))
        out.write('\n')
