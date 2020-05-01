## Getting started on the AWS cloud with vagrant

Vagrant can also run this pipeline on the AWS cloud using your AWS credentials. First, install the `vagrant-aws` plugin and the dummy box that goes along with it.

    $ vagrant plugin install vagrant-aws
    $ vagrant box add aws-dummy https://github.com/mitchellh/vagrant-aws/raw/master/dummy.box

Then configure your AWS account on your machine using their command-line tool. It will prompt you for your AWS credentials, preferred region (e.g. `us-east-1`), and output format (e.g. `text`). For more information on creating an AWS account and obtaining credentials, [see this tutorial][aws].

[aws]: (https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html#cli-quick-configuration)

    $ pip install awscli
    $ aws configure

You must then create an SSH keypair for EC2...

    $ aws ec2 create-key-pair --key-name default > ~/.aws/default.pem
    $ chmod 0400 ~/.aws/default.pem
    $ sed -i -e $'/-----BEGIN/s/.*\t//' ~/.aws/default.pem
    $ sed -i -e $'/-----END/s/\t.*//' ~/.aws/default.pem

...and a security group—we'll call it `allow-ssh`—that allows inbound SSH traffic. Here, we allow traffic from any IP address, but you could choose a narrower range, if you know your public IP address.

    $ aws ec2 create-security-group --group-name allow-ssh \
        --description "allows all inbound SSH traffic"
    $ aws ec2 authorize-security-group-ingress --group-name allow-ssh \
        --protocol tcp --port 22 --cidr 0.0.0.0/0

Finally, you can boot and provision your AWS EC2 machine with Vagrant.

    $ vagrant up --provider=aws

Vagrant will spend a few minutes configuring and building the VM. Once it's done, run

    $ vagrant ssh

You should see the bash prompt `admin@ip-...:/vagrant$`, and may proceed to [**Usage** in the main README](https://github.com/powerpak/pathospot-compare#usage).

The next time you want to use the pipeline in this VM, you won't need to start all over again; simply `logout` of your VM and `vagrant halt` to exit, and `vagrant up; vagrant ssh` to pick up where you left off. (To delete all traces of the VM from AWS, use `vagrant destroy`.)