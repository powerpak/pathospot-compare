#!/bin/bash

# NOTE: this script was  intended for use on the Minerva computing environment
# and will likely not function as intended outside that environment.
# For more info on Minerva, see https://labs.icahn.mssm.edu/minervalab/

# Install Ruby gems first (cannot do this within conda, due to library linking problems)
module purge all
unset PYTHONPATH
unset PERL5LIB
unset R_LIBS
module load openssl/1.1.2-dev # Work around missing openssl library on chimera
module load libpng/12         # Work around missing libpng on chimera
module load ruby/2.2.0
module load mysql/5.1.72
module load zlib
module load sqlite3/3.8.3.1
bundle install --deployment

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
conda create --yes --name pathospot-compare \
   python=2.7 tqdm numpy ete3 biopython networkx MySQL-python mummer=3.23 graphviz r ruby=2.2

source activate pathospot-compare
