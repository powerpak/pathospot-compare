# Workaround for vagrant-aws expecting an older version of i18n than in Vagrant <2.2.7
# See https://www.gitmemory.com/issue/mitchellh/vagrant-aws/566/580812210
class Hash
  def slice(*keep_keys)
    h = {}
    keep_keys.each { |key| h[key] = fetch(key) if has_key?(key) }
    h
  end unless Hash.method_defined?(:slice)
  def except(*less_keys)
    slice(*keys - less_keys)
  end unless Hash.method_defined?(:except)
end

# Configure Vagrant environments for virtualbox and AWS
# Note: Analyzing the example dataset requires at least 4GB of RAM
Vagrant.configure("2") do |config|
  config.vm.box = "debian/stretch64"
  
  config.vm.synced_folder ".", "/vagrant", type: "rsync",
      rsync__exclude: [".git/", ".bundle/", "out/", "vendor/", "example/", "scripts/env.sh"]

  config.vm.provision "shell", path: "scripts/bootstrap.debian-stretch.sh"
  
  config.vm.provider :virtualbox do |vbox, override|
    vbox.customize ["modifyvm", :id, "--memory", 4096]
    
    override.vm.network "forwarded_port", guest: 80, host: 8888, auto_correct: true
  end
  
  config.vm.provider :aws do |aws, override|
    override.vm.box = "aws-dummy"

    aws.region = "us-east-1"
    aws.ami = "ami-0f9e7e8867f55fd8e"
    aws.security_groups = ["allow-ssh-http"]
    aws.instance_type = "m5.large"

    override.ssh.username = "admin"
    aws.keypair_name = "default"
    override.ssh.private_key_path = "~/.aws/default.pem"
  end
end
