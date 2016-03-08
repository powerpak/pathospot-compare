#!/bin/bash

# Must be configured by the end user
export REPO_DIR=""

# Reset module system for node architecture
module purge
unset MODULEPATH
source /etc/profile.d/modules.sh

# Load required modules
module load intel/parallel_studio_xe_2015
module load python/2.7.6
module load py_packages
module load openmpi/1.6.5
module load boost/1.55.0-gcc
module load java/1.7.0_60
module load ruby/2.2.0

# Defaults will probably work for these
export PERL5LIB="/usr/bin/perl5.10.1"
export TMP="/sc/orga/scratch/$USER/tmp"

# Ensures that the required module files are in MODULEPATH
if [[ ":$MODULEPATH:" != *":/hpc/packages/minerva-mothra/modulefiles:"* ]]; then
    export MODULEPATH="${MODULEPATH:+"$MODULEPATH:"}/hpc/packages/minerva-mothra/modulefiles"
fi

# If running from interactive1/interactive2, need to run requests through internal HTTP proxy
export HTTP_PROXY="http://proxy.mgmt.hpc.mssm.edu:8123"

# Run rake
rake -f $REPO_DIR/Rakefile "$@"
