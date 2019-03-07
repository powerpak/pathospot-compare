Vagrant.configure("2") do |config|
  config.vm.box = "debian/stretch64"

  # Enable provisioning with a shell script.
  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get install -y ruby2.3 ruby2.3-dev curl build-essential 
    apt-get install -y default-libmysqlclient-dev
    apt-get install -y python-pip python-dev
    gem install bundler
    gem install rake
    
    # Install mummer
    cd /tmp
    curl -L -s -o mummer.tar.gz \
      'https://sourceforge.net/projects/mummer/files/mummer/3.23/MUMmer3.23.tar.gz/download'
    tar xvzf mummer.tar.gz
    cd MUMmer3.23
    make
    cp annotate combineMUMs delta-filter dnadiff exact-tandems gaps mapview \
      mgaps mummer mummerplot nucmer nucmer2xfig promer repeat-match run-mummer1 \
      run-mummer3 show-aligns show-coords show-diff show-snps show-tiling \
      /usr/local/bin
    cd /tmp
    rm -rf mummer.tar.gz MUMmer3.23
    
    # Fetch gems required by bundler
    cd /vagrant
    sudo -u vagrant bundle install --deployment
    
    # Fetch all the python modules required by the python scripts
    pip install -r requirements.txt
    
    # Install the essential dependencies for the pipeline
    sudo -u vagrant rake check
    
    # Modify the default user's ~/.profile to save a few steps upon `vagrant ssh`ing
    if [ ! -f scripts/env.sh ]; then
      sudo -u vagrant cp scripts/example.env.sh scripts/env.sh
    fi
    echo >> /home/vagrant/.profile
    echo "cd /vagrant" >> /home/vagrant/.profile
    echo "source /vagrant/scripts/env.sh" >> /home/vagrant/.profile
  SHELL
end
