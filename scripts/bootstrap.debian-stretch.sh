#!/usr/bin/env bash
# Intended to be run as root by Vagrant when provisioning a vanilla Debian Stretch box
# (although it could be modified by an advanced user for other scenarios)
# Optionally, provide the VM's login username as the 1st argument (default is "vagrant")

# This detects the home directory for the default user (uid 1000), which is given a 
# different name on different vagrant providers (e.g. admin, vagrant)
DEFAULT_UID="1000"
DEFAULT_HOME="$(getent passwd $DEFAULT_UID | cut -d: -f6)"

apt-get update
apt-get install -y ruby2.3 ruby2.3-dev curl build-essential 
apt-get install -y default-libmysqlclient-dev
apt-get install -y python-pip python-dev
apt-get install -y graphviz
apt-get install -y libsqlite3-dev
apt-get install -y git
gem install bundler
gem install rake

# Install mummer
cd /opt
curl -L -s -o mummer.tar.gz \
  'https://sourceforge.net/projects/mummer/files/mummer/3.23/MUMmer3.23.tar.gz/download'
tar xvzf mummer.tar.gz
cd MUMmer3.23
make
cp annotate combineMUMs delta-filter dnadiff exact-tandems gaps mapview \
  mgaps mummer mummerplot nucmer nucmer2xfig promer repeat-match run-mummer1 \
  run-mummer3 show-aligns show-coords show-diff show-snps show-tiling \
  /usr/local/bin

# Fetch gems required by bundler
cd /vagrant
sudo -u \#$DEFAULT_UID bundle install --deployment

# Fetch all the python modules required by the python scripts
pip install -r requirements.txt``

# Install the essential dependencies for the pipeline
sudo -u \#$DEFAULT_UID rake check

# Download and decompress the example dataset
sudo -u \#$DEFAULT_UID rake example_data

# Modify the default user's ~/.profile to save a few steps upon `vagrant ssh`ing
echo >> "$DEFAULT_HOME/.profile"
echo "cd /vagrant" >> "$DEFAULT_HOME/.profile"
echo "if [ ! -f scripts/env.sh ]; then cp scripts/example.env.sh scripts/env.sh; fi" \
  >> "$DEFAULT_HOME/.profile"
echo "source scripts/env.sh" >> "$DEFAULT_HOME/.profile"

# Download and install pathoSPOT-visualize
mkdir -p /var/www
git clone https://github.com/powerpak/pathospot-visualize.git /var/www/html
cd /var/www/html
source scripts/bootstrap.debian-stretch.sh
# Symlink its input data directory directly to this pipeline's default output directory
rm -rf data
ln -s /vagrant/out data