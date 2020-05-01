# pathoSPOT-compare

This is the comparative genomics pipeline for PathoSPOT, the **Patho**gen **S**equencing **P**hylogenomic **O**utbreak **T**oolkit.

The pipeline is run on sequenced pathogen genomes, for which metadata (dates, locations, etc.) are kept in a relational database (either SQLite or MySQL), and it produces output files that can be interactively visualized with [pathoSPOT-visualize][].

[pathoSPOT-visualize]: https://github.com/powerpak/pathospot-visualize

## Requirements

Although designed for Linux, users of other operating systems can use [Vagrant][] to rapidly build and launch a Linux virtual machine with the pipeline ready-to-use, either locally or on cloud providers (e.g., AWS). This bioinformatics pipeline requires ruby ≥2.2 with rake ≥10.5 and bundler, python 2.7 with the modules in `requirements.txt`, [MUMmer][] 3.23, the standard Linux build toolchain, and additional software that the pipeline will build and install itself. 

[MUMmer]: http://mummer.sourceforge.net/

### Using vagrant

Download and install Vagrant using any of the [official installers][vagrant] for Mac, Windows, or Linux. Vagrant supports both local virtualization via VirtualBox and cloud hosts (e.g., AWS).

[vagrant]: https://www.vagrantup.com/downloads.html

#### Local virtual machine on VirtualBox

The fastest way to get started with Vagrant is to [install VirtualBox][virtualbox]. Then, clone this repository to a directory, `cd` into it, and run the following:

    $ vagrant up

It will take a few minutes for Vagrant to download a vanilla [Debian 9 "Stretch"][deb] VM and configure it. Once it's done, to use your new VM, type

    $ vagrant ssh

You should see the bash prompt `vagrant@stretch:/vagrant$`, and may proceed to [**Usage**](#usage) below.

The next time you want to use the pipeline in this VM, you won't need to start all over again; simply `logout` of your VM and `vagrant suspend` to save its state, and `vagrant resume; vagrant ssh` to pick up where you left off.

[virtualbox]: https://www.virtualbox.org/wiki/Downloads
[deb]: https://www.debian.org/releases/stretch/

#### Hosted on AWS

Vagrant can also run this pipeline on the AWS cloud using your AWS credentials. See [README-vagrant-aws.md](https://github.com/powerpak/pathospot-compare/blob/master/README-vagrant-aws.md).

### Minerva/Chimera (Mount Sinai users only)

For particular instructions for getting started on the Chimera nodes of the Minerva computing environment, see [README-minerva.md](https://github.com/powerpak/pathospot-compare/blob/master/README-minerva.md).

### Installing directly on Linux (advanced users)

You may be able to install prerequisites directly on a Linux machine by editing `scripts/bootstrap.debian-stretch.sh` to fit your distro's needs. As the name suggests, it was designed for [Debian 9 "Stretch"][deb], but will likely run with minor changes on most Debian-based distros, including Ubuntu and Mint. Note that this script must be run as root, expects the pipeline will be run by `$DEFAULT_USER` i.e. `UID=1000`, and assumes this repo is already checked out into `/vagrant`.

## Usage

Rake, aka [ruby make][], is used to kick off the pipeline as follows. Certain tasks require more variables to be set before being invoked, which is done via [environment variables](#environment-variables) detailed more below. 

    $ rake -T                    # list the available tasks
    $ rake $TASK_1 $TASK_2       # run tasks named $TASK_1 and $TASK_2
    $ FOO="bar" rake $TASK_1     # run $TASK_1 with variable FOO set to "bar"

**Important:** When firing up the pipeline in a new shell, always remember to `source scripts/env.sh` _before_ running `rake`. If you are using Vagrant, this is configured to happen automatically (in `~/.profile`).

[ruby make]: https://github.com/ruby/rake

### Example dataset

If you are using Vagrant, running the pipeline on the example dataset is as simple as:

    $ IN_QUERY="1=1" rake parsnp epi encounters

### Environment variables

Certain tasks within the pipeline require you to specify some extra information as an environment variable.  You can do this by either editing them into `scripts/env.sh` and re-running `source scripts/env.sh`, or you can prepend them to the `rake` invocation, e.g.:

    $ IN_FOFN=LB_genomes.fofn rake mugsy

If a required environment variable isn't present when a task is run and there is no default value, rake will abort with an error message.

Variable             | Required by                           | Default | Purpose
---------------------|---------------------------------------|---------|-----------------------------------
`OUT`                | all tasks                             | ./out   | This is where your interim and completed files are saved
`IN_QUERY`           | `parsnp`                              | (none)  | An SQL `WHERE` clause that dynamically selects FASTAs that were assembled and saved in `IGB_DIR` via a query to the `tAssemblies` table in PathogenDB's MySQL database. Requires `IGB_DIR` and `PATHOGENDB_URI` to be configured appropriately. An example usage that selects *C. difficile* assemblies would be `taxonomy_ID = 1496 AND assembly_data_link LIKE 'C_difficile_%'` **Important:** If set, this overrides `IN_FOFN`.
`OUT_PREFIX`         | all tasks                             | out     | This prefix will be prepended to output filenames (so you can track files generated for each invocation)
`REF`                | `parsnp`                              | (none)  | Specify a reference genome for parsnp. If not specified, the oldest genome by `order_date` within each mash cluster is used as the reference.
`GBK`                | `parsnp`                              | (none)  | Specify a reference genbank file for parsnp. Overrides `REF` above.
`MASH_CUTOFF`        | `parsnp`                              | 0.02    | Create clusters of this maximum diameter in mash distance units before running parsnp
`MAX_CLUSTER_SIZE`   | `parsnp`                              | 100     | Do not attempt to use parsnp on more than this number of input sequences
`DISTANCE_THRESHOLD` | `parsnp`                              | 10      | The default SNP threshold that will be used for clustering the heatmap in [pathoSPOT-visualize][]
`IGB_DIR`            | `parsnp`                              | (none)  | An IGB Quickload directory that contains assemblies saved into PathogenDB`
`PATHOGENDB_URI`     | `parsnp`                              | (none)  | How to connect to the PathogenDB database. Must be formatted as `sqlite://relative/path/to/pathogen.db` or `mysql2://user:pass@host/database`

### Tasks

#### parsnp

FIXME: `rake parsnp` ... should be documented.

In brief, it produces similar output to `rake heatmap` for use with [pathoSPOT-visualize][], but uses parsnp instead of MUMmer to calculate SNV distances between the sequences.

In order for parsnp to complete in a reasonable amount of time and with acceptable core genome sizes (e.g., >50%), you may specify `MASH_CUTOFF` and `MAX_CLUSTER_SIZE`, which tune a preclustering step that is done with [mash][]. Clusters up to `MASH_CUTOFF` units in diameter are created, with the size of each cluster capped at `MAX_CLUSTER_SIZE`. Parsnp will be run separately on each cluster and distances remerged into the final output.

[mash]: https://mash.readthedocs.io/en/latest/

#### encounters

FIXME: `rake encounters` ... should be documented.

#### epi

FIXME: `rake epi` ... should be documented.

## Other notes

This pipeline downloads and installs the appropriate versions of mash and HarvestTools into `vendor/`.
