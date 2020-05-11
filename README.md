# pathoSPOT-compare

This is the comparative genomics pipeline for PathoSPOT, the **Patho**gen **S**equencing **P**hylogenomic **O**utbreak **T**oolkit.

The pipeline is run on sequenced pathogen genomes, for which metadata (dates, locations, etc.) are kept in a relational database (either SQLite or MySQL), and it produces output files that can be interactively visualized with [pathoSPOT-visualize][].

[pathoSPOT-visualize]: https://github.com/powerpak/pathospot-visualize

## Requirements

This pipeline runs on Linux; however, Mac and Windows users can use [Vagrant][] to rapidly build and launch a Linux virtual machine with the pipeline ready-to-use, either locally or on cloud providers (e.g., AWS). This bioinformatics pipeline requires ruby ≥2.2 with rake ≥10.5 and bundler, python 2.7 with the modules in `requirements.txt`, [MUMmer][] 3.23, the standard Linux build toolchain, and additional software that the pipeline will build and install itself. 

[MUMmer]: http://mummer.sourceforge.net/

### Using Vagrant

Download and install Vagrant using any of the [official installers][vagrant] for Mac, Windows, or Linux. Vagrant supports both local virtualization via VirtualBox and cloud hosts (e.g., AWS).

[vagrant]: https://www.vagrantup.com/downloads.html

The fastest way to get started with Vagrant is to [install VirtualBox][virtualbox]. Then, clone this repository to a directory, `cd` into it, and run the following:

    $ vagrant up

It will take a few minutes for Vagrant to download a vanilla [Debian 9 "Stretch"][deb] VM and configure it. Once it's done, to use your new VM, type

    $ vagrant ssh

You should see the bash prompt `vagrant@stretch:/vagrant$`, and may proceed to [**Usage**](#usage) below.

The next time you want to use the pipeline in this VM, you won't need to start all over again; simply `logout` of your VM and `vagrant suspend` to save its state, and `vagrant resume; vagrant ssh` to pick up where you left off.

[virtualbox]: https://www.virtualbox.org/wiki/Downloads
[deb]: https://www.debian.org/releases/stretch/

### Hosted on AWS

Vagrant can also run this pipeline on the AWS cloud using your AWS credentials. See [README-vagrant-aws.md](https://github.com/powerpak/pathospot-compare/blob/master/README-vagrant-aws.md).

### Minerva/Chimera (Mount Sinai users only)

Mount Sinai users getting started on the [Minerva computing environment][minerva] can use an included script to setup an appropriate environment on a Chimera node (Vagrant is unnecessary); for more information see [README-minerva.md](https://github.com/powerpak/pathospot-compare/blob/master/README-minerva.md).

[minerva]: https://labs.icahn.mssm.edu/minervalab/

### Installing directly on Linux (advanced users)

You may be able to install prerequisites directly on a Linux machine by editing `scripts/bootstrap.debian-stretch.sh` to fit your distro's needs. As the name suggests, this script was designed for [Debian 9 "Stretch"][deb], but will likely run with minor changes on most Debian-based distros, including Ubuntu and Mint. Note that this script must be run as root, expects the pipeline will be run by `$DEFAULT_USER` i.e. `UID=1000`, and assumes this repo is already checked out into `/vagrant`.

## Usage

Rake, aka [Ruby Make][rake], is used to kick off the pipeline. Some tasks require certain parameters, which are provided as environment variables (and detailed more below). A quick primer on how to use Rake:

    $ rake -T                    # list the available tasks
    $ rake $TASK_1 $TASK_2       # run the tasks named $TASK_1 and $TASK_2
    $ FOO="bar" rake $TASK_1     # run $TASK_1 with variable FOO set to "bar"

**Important:** If you are not using Vagrant, whenever firing up the pipeline in a new shell, you must always run `source scripts/env.sh` _before_ running `rake`. The Vagrant environment does this automatically via `~/.profile`.

[rake]: https://github.com/ruby/rake

### Quickstart

If you used Vagrant to get started, it automatically downloads an [example dataset (tar.gz)][mrsa.tar.gz] for MRSA isolates at Mount Sinai. The genomes are saved at `example/igb` and their metadata is in `example/mrsa.db`. Default environment variables in `scripts/env.sh` are configured so that the pipeline will run on the example data.

To run the full analysis, run the following, which invokes the three main tasks (`parsnp`, `epi`, and `encounters`, explained more below).

    $ rake all

When the analysis finishes, there will be four output files saved into `out/`, which include a YYYY-MM-DD formatted date in the filename and have the following extensions:

- `.parsnp.heatmap.json` → made by `parsnp`; contains the genomic SNP distance matrix
- `.parsnp.vcfs.npz` → made by `parsnp`; contains SNP variant data for each genome
- `.encounters.tsv` → made by `encounters`; contains spatiotemporal data for patients
- `.epi.heatmap.json` → made by `epi`; contains culture test data (positives and negatives)

These outputs can be visualized using [pathoSPOT-visualize][], which the Vagrant environment automatically installs and sets up for you. If you used VirtualBox, simply go to <http://localhost:8888>, which forwards to the virtual machine. For AWS, instead use your public IPv4 address, which you can obtain by running the following within the EC2 instance:

	$ curl http://169.254.169.254/latest/meta-data/public-ipv4

[mrsa.tar.gz]: https://pathospot.org/data/mrsa.tar.gz
[pathoSPOT-visualize]: https://github.com/powerpak/pathospot-visualize

### Rake tasks

#### parsnp

`rake parsnp` 

This task requires you to set the `IN_QUERY` and `OUT_PREFIX` environment variables, which are 

- `IN_QUERY`: An `SQL WHERE` clause ... FIXME

In brief, it produces similar output to `rake heatmap` for use with [pathoSPOT-visualize][], but uses parsnp instead of MUMmer to calculate SNV distances between the sequences.

In order for parsnp to complete in a reasonable amount of time and with acceptable core genome sizes (e.g., >50%), you may specify `MASH_CUTOFF` and `MAX_CLUSTER_SIZE`, which tune a preclustering step that is done with [mash][]. Clusters up to `MASH_CUTOFF` units in diameter are created, with the size of each cluster capped at `MAX_CLUSTER_SIZE`. Parsnp will be run separately on each cluster and distances remerged into the final output.

[mash]: https://mash.readthedocs.io/en/latest/

#### encounters

FIXME: `rake encounters` ... should be documented.

#### epi

FIXME: `rake epi` ... should be documented.

## Exporting data from Vagrant

If you want to copy the final outputs outside of the Vagrant environment, e.g. to serve them with [pathoSPOT-visualize][] from a different machine, use [vagrant-scp][] as follows from the _host_ machine:

	$ vagrant plugin install vagrant-scp
	$ vagrant scp default:/vagrant/out/*.json /destination/on/host
	$ vagrant scp default:/vagrant/out/*.npz /destination/on/host
	$ vagrant scp default:/vagrant/out/*.encounters.tsv /destination/on/host

[vagrant-scp]: https://github.com/invernizzi/vagrant-scp

## Other notes

This pipeline downloads and installs the appropriate versions of mash and HarvestTools into `vendor/`.
