Vagrant.configure("2") do |config|
  config.vm.box = "debian/stretch64"
  
  config.vm.synced_folder ".", "/vagrant", type: "rsync",
      rsync__exclude: [".git/", ".bundle/", "out/", "vendor/", "scripts/env.sh"]

  config.vm.provision "shell", path: "scripts/bootstrap.debian-stretch.sh"
  config.vm.network "forwarded_port", guest: 80, host: 8888, auto_correct: true
  
  config.vm.provider :virtualbox do |vbox, override|
    vbox.customize ["modifyvm", :id, "--memory", 4096]
  end
  
  config.vm.provider :aws do |aws, override|
    override.vm.box = "aws-dummy"

    aws.region = "us-east-1"
    aws.ami = "ami-0f9e7e8867f55fd8e"
    aws.security_groups = ["allow-ssh"]
    aws.instance_type = "m3.medium"  # => m3 is being phased out; could be upgraded to m5.large

    override.ssh.username = "admin"
    aws.keypair_name = "default"
    override.ssh.private_key_path = "~/.aws/default.pem"
  end
end
