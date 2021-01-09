## Getting started on the AWS cloud with vagrant

Vagrant can run this pipeline on the AWS cloud using your AWS credentials. First, [install Vagrant][vagrant] if you haven't already. Then clone this repository to a directory on your development machine and `cd` into it.

Note: you need to have Vagrant version ≥2.2.9 in order for the following to work, because of a [bug when installing vagrant-aws][fixvagrant] on earlier versions. To check your version, run `vagrant --version`.

[vagrant]: https://www.vagrantup.com/downloads.html
[fixvagrant]: https://github.com/hashicorp/vagrant/issues/11518

To get started install the `vagrant-aws` plugin and the dummy box that goes along with it. 

	$ vagrant plugin install vagrant-aws
    $ vagrant box add aws-dummy https://github.com/mitchellh/vagrant-aws/raw/master/dummy.box

[Download and install][awsinstall] the `aws` command-line tool. Run the following to set it up; it will prompt you for your AWS credentials, preferred region (e.g. `us-east-1`), and output format (e.g. `text`). For more information on creating an AWS account and obtaining credentials, [see this tutorial][aws].

[awsinstall]: https://aws.amazon.com/cli/
[aws]: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html#cli-quick-configuration

    $ aws configure

You must then create an SSH keypair for EC2...

    $ aws ec2 create-key-pair --key-name default > ~/.aws/default.pem
    $ chmod 0400 ~/.aws/default.pem
    $ sed -i -e $'/-----BEGIN/s/.*\t//' ~/.aws/default.pem
    $ sed -i -e $'/-----END/s/\t.*//' ~/.aws/default.pem

...and a security group—we'll call it `allow-ssh-http`—that allows inbound SSH and HTTP traffic. Here, we allow traffic from any IP address (`0.0.0.0/0`), but you can (and should) specify a narrower range, if you know your public IP address.

    $ aws ec2 create-security-group --group-name allow-ssh-http \
        --description "allows all inbound SSH and HTTP traffic"
    $ aws ec2 authorize-security-group-ingress --group-name allow-ssh-http \
        --protocol tcp --port 22 --cidr 0.0.0.0/0
    $ aws ec2 authorize-security-group-ingress --group-name allow-ssh-http \
        --protocol tcp --port 80 --cidr 0.0.0.0/0

Finally, you can boot and provision your AWS EC2 machine with Vagrant.

    $ vagrant up --provider=aws

Vagrant will spend a few minutes configuring and building the VM. Once it's done, run

    $ vagrant ssh

You should see the bash prompt `admin@ip-...:/vagrant$`, and may proceed to [**Usage** in the main README](https://github.com/powerpak/pathospot-compare#usage).

The next time you want to use the pipeline in this VM, you won't need to start all over again; simply `logout` of your VM and `vagrant halt` to exit, and `vagrant up; vagrant ssh` to pick up where you left off. (To delete all traces of the VM from AWS, use `vagrant destroy`.)

### Finding your public IP

Once the pipeline has completed, you will likely want to view the results in [pathospot-visualize][], which is automatically installed to your EC2 instance and served over HTTP. You will need to find out your public IP address, which you can do by running the following on the VM:

    $ curl http://169.254.169.254/latest/meta-data/public-ipv4; echo

Paste this IP address into your web browser's address bar to open [pathospot-visualize][].

[pathospot-visualize]: https://github.com/powerpak/pathospot-visualize
