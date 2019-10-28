#!/bin/bash

module unload ruby
module load ruby/2.2.0

# You need to configure this with a connection string for the PathogenDB database
export PATHOGENDB_URI="mysql2://user:pass@host/database"

# Defaults will probably work for these
export PERL5LIB="/usr/bin/perl5.10.1"
export TMP="/sc/orga/scratch/$USER/tmp"
export IGB_DIR="/sc/orga/projects/InfectiousDisease/igb"

# Ensures that the required module files are in MODULEPATH
if [[ ":$MODULEPATH:" != *":/hpc/packages/minerva-mothra/modulefiles:"* ]]; then
    export MODULEPATH="${MODULEPATH:+"$MODULEPATH:"}/hpc/packages/minerva-mothra/modulefiles"
fi
