#!/bin/bash

# The Rakefile includes `module load` and `module unload` statements for 
# multiuser computing environments like Minerva, which are unnecessary
# for boxes provisioned with Vagrant. This makes `module` into a no-op
mkdir -p "$HOME/bin"
if [ ! -f $HOME/bin/module ]; then
  echo "#!/bin/sh" >> $HOME/bin/module
  chmod +x $HOME/bin/module
fi
PATH="$HOME/bin:$PATH"

# Configure this with a connection string for your PathogenDB database
# Here, we provide a URI to the example included SQLite database
export PATHOGENDB_URI="sqlite://example/mrsa.db"

export TMP="/tmp"
export IGB_DIR="/vagrant/example/igb"
