#!/bin/bash

# NOTE: this script was  intended for use on the Minerva computing environment
# and will likely not function as intended outside that environment.
# For more info on Minerva, see https://labs.icahn.mssm.edu/minervalab/

# Load conda environment for comparison pipeline
module purge all
unset PYTHONPATH
unset PERL5LIB
unset R_LIBS
module load anaconda2
source activate pathospot-compare
export PATH=`echo $PATH | tr ":" "\n" | grep -vP "^${ANACONDAHOME}bin$" | tr "\n" ":"` # Remove path to anaconda bin at this point to avoid python issues

module load openssl/1.1.2-dev # Work around missing openssl library on chimera
module load libpng/12         # Work around missing libpng on chimera
module load ruby/2.2.0
module load mysql/5.1.72
module load zlib
module load sqlite3/3.8.3.1

# You need to configure this with a connection string for the PathogenDB database
export PATHOGENDB_URI="mysql2://user:pass@host/database"

# Defaults will probably work for these
export PERL5LIB="/usr/bin/perl5.10.1"
export TMP="/sc/hydra/scratch/$USER/tmp"
mkdir -p $TMP
export IGB_DIR="/sc/arion/projects/InfectiousDisease/igb"
