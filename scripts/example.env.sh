#!/bin/bash

module unload ruby
module load ruby

# Defaults will probably work for these
export PERL5LIB="/usr/bin/perl5.10.1"
export TMP="/sc/orga/scratch/$USER/tmp"

# Ensures that the required module files are in MODULEPATH
if [[ ":$MODULEPATH:" != *":/hpc/packages/minerva-mothra/modulefiles:"* ]]; then
    export MODULEPATH="${MODULEPATH:+"$MODULEPATH:"}/hpc/packages/minerva-mothra/modulefiles"
fi
