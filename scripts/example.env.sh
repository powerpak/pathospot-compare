#!/bin/bash

# The Rakefile includes `module load` and `module unload` statements for 
# multiuser computing environments like Minerva, which are unnecessary
# for vanilla boxes provisioned with Vagrant
alias module=:

# Configure this with a connection string for your PathogenDB database
# Here, we provide a URI to the example included SQLite database
export PATHOGENDB_MYSQL_URI="mysql2://user:pass@host/database"

export TMP="/tmp"
export IGB_DIR="/vagrant/examples/igb"
