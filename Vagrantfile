Vagrant.configure("2") do |config|
  config.vm.box = "debian/stretch64"
  
  config.vm.synced_folder ".", "/vagrant", type: "rsync",
      rsync__exclude: [".git/", "vendor/"]

  config.vm.provision "shell", path: "scripts/bootstrap.debian-stretch.sh"
  
  config.vm.provider :aws do |aws, override|
    override.vm.box = "aws-dummy"

    aws.region = "us-east-1"
    aws.ami = "ami-0f9e7e8867f55fd8e"
    aws.security_groups = ["allow-ssh"]

    override.ssh.username = "admin"
    aws.keypair_name = "default"
    override.ssh.private_key_path = "~/.aws/default.pem"
  end
end
