#!/bin/bash

# Load anaconda module
module purge all
unset PYTHONPATH
unset PERL5LIB
unset R_LIBS
module load anaconda2
module load zlib

# Add channels in this order; conda-forge must be at the top!
conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels r
conda config --add channels conda-forge

# Set up environment
conda create -n pathospot-compare \
   python=2.7 tqdm numpy ete3 biopython networkx MySQL-python mummer=3.23 graphviz r ruby

source activate pathospot-compare
