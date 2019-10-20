# pathoSPOT-compare

This is the comparative genomics pipeline for PathoSPOT, the **Patho**gen **S**equencing **P**hylogenomic **O**utbreak **T**oolkit.

The pipeline is run on sequenced pathogen genomes, for which metadata (dates, locations, etc.) are kept in a relational database (either SQLite or MySQL), and it produces output files that can be interactively visualized with [pathoSPOT-visualize][].

[pathoSPOT-visualize]: (https://github.com/powerpak/pathospot-visualize)

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

You should see the bash prompt `admin@ip-...:/vagrant$`, and may proceed to [**Usage**](#usage) below.

The next time you want to use the pipeline in this VM, you won't need to start all over again; simply `logout` of your VM and `vagrant halt` to exit, and `vagrant up; vagrant ssh` to pick up where you left off. (To delete all traces of the VM from AWS, use `vagrant destroy`.)

### Minerva (Mount Sinai users only)

The pipeline can also access all required software using the module system on [Minerva](http://hpc.mssm.edu). Clone this repository to a directory and `cd` into it.  You'll want to configure your environment first using the included script:

    $ cp scripts/example.MINERVA.env.sh scripts/env.sh  

The defaults should work for any Minerva user.  Then, you can source the script into your shell and install required gems locally into the `vendor/bundle` directory as follows:

    $ source scripts/env.sh
    $ bundle install --deployment

When this is complete, you should be able to continue with the steps below.

### Installing directly on Linux (advanced users)

You may be able to install prerequisites directly on a Linux machine by editing `scripts/bootstrap.debian-stretch.sh` to fit your distro's needs. As the name suggests, it was designed for [Debian 9 "Stretch"][deb], but will likely run with minor changes on most Debian-based distros, including Ubuntu and Mint. Note that this script must be run as root, expects the pipeline will be run by `$DEFAULT_USER` i.e. `UID=1000`, and assumes this repo is already checked out into `/vagrant`.

## Usage

Rake, aka [ruby make][], is used to kick off the pipeline as follows. However, also read **[Environment variables](#environment-variables)** below, as certain tasks require more variables to be set before being invoked.

    $ rake -T                    # list the available tasks
    $ rake $TASK_NAME            # run the task named $TASK_NAME
    $ FOO="bar" rake $TASK_NAME  # run $TASK_NAME with FOO set to "bar"

**Important:** When firing up the pipeline in a new shell, always remember to `source scripts/env.sh` _before_ running `rake`. If you are using Vagrant, this is configured to happen automatically (in `~/.profile`).

[ruby make]: https://github.com/ruby/rake

### Environment variables

Certain tasks within the pipeline require you to specify some extra information as an environment variable.  You can do this by either editing them into `scripts/env.sh` and re-running `source scripts/env.sh`, or you can prepend them to the `rake` invocation, e.g.:

    $ IN_FOFN=LB_genomes.fofn rake mugsy

If a required environment variable isn't present when a task is run and there is no default value, rake will abort with an error message.

Variable             | Required by                           | Default | Purpose
---------------------|---------------------------------------|---------|-----------------------------------
`OUT`                | all tasks                             | ./out   | This is where your interim and completed files are saved
`IN_FOFN`            | `mugsy` `mauve` `sv_snv`              | (none)  | A file containing filenames that will be processed as input
`IN_QUERY`           | `heatmap` `parsnp`                    | (none)  | An SQL `WHERE` clause that dynamically selects FASTAs that were assembled and saved in `IGB_DIR` via a query to the `tAssemblies` table in PathogenDB's MySQL database. Requires `IGB_DIR` and `PATHOGENDB_URI` to be configured appropriately. An example usage that selects *C. difficile* assemblies would be `taxonomy_ID = 1496 AND assembly_data_link LIKE 'C_difficile_%'` **Important:** If set, this overrides `IN_FOFN`.
`OUT_PREFIX`         | all tasks                             | out     | This prefix will be prepended to output filenames (so you can track files generated for each invocation)
`OUTGROUP`           | `mugsy`                               | (none)  | The [outgroup][] to specify for `RAxML`
`SEED_WEIGHT`        | `mauve` `sv_snv`                      | (none)  | Use this seed weight for calculating initial anchors
`LCB_WEIGHT`         | `mauve` `sv_snv`                      | (none)  | Minimum pairwise LCB score
`REF`                | `parsnp`                              | (none)  | Specify a reference genome for parsnp. If not specified, the oldest genome by `order_date` within each mash cluster is used as the reference.
`GBK`                | `parsnp`                              | (none)  | Specify a reference genbank file for parsnp. Overrides `REF` above.
`MASH_CUTOFF`        | `parsnp`                              | 0.02    | Create clusters of this maximum diameter in mash distance units before running parsnp
`MAX_CLUSTER_SIZE`   | `parsnp`                              | 100     | Do not attempt to use parsnp on more than this number of input sequences
`DISTANCE_THRESHOLD` | `heatmap` `parsnp`                    | 10      | The default SNP threshold that will be used for clustering the heatmap in [pathoSPOT-visualize][]
`IGB_DIR`            | `heatmap` `parsnp`                    | (none)  | An IGB Quickload directory that contains assemblies saved into PathogenDB`
`PATHOGENDB_URI`     | `heatmap` `parsnp`                    | (none)  | How to connect to the PathogenDB database. Must be formatted as `sqlite://relative/path/to/pathogen.db` or `mysql2://user:pass@host/database`

According to [Darling et al.](http://dx.doi.org/10.1371/journal.pone.0011147), a good default for both `SEED_WEIGHT` and `LCB_WEIGHT` typically chosen by Mauve is log2((avg genome size) / 1.5).

[outgroup]: http://en.wikipedia.org/wiki/Outgroup_%28cladistics%29

#### Optional variables

The following are not required by any tasks, but may be helpful:

Variable             | Default | Purpose
---------------------|---------|-----------------------------------
`LSF_DISABLE`        | (none)  | Set this variable to anything to globally disable submission of long tasks to LSF. This is probably a good idea if you are running on a Minerva interactive node.
`BED_LINES_LIMIT`    | 1000    | Don't write data to BED files for the `snv` task that would contain more than this number of lines of data. (Saves disk space.)

### Tasks

#### sv_snv

`rake sv_snv` attempts to create annotation tracks in [BED format] that contain the likely structural variants (insertions, deletions, and rearrangements) and single nucleotide variants (SNVs) that differentiate each pair of genomes in your `IN_FOFN`.

To do this, for each pair of genomes a [Mauve] alignment is created, which is then parsed for [locally collinear blocks][lcbs] (LCBs) which are considered the "core genome" for the pair.  Blocks unique to one or the other genome ("islands" in Mauve terminology) are considered insertions and deletions, and then [GRIMM] is used to determine the minimal number of inversions, translocations, fusions and fissions that could reorder the LCBs in the first genome to produce the second.  These are all depicted as features in a BED track, using connected "exons" (fat blocks) to depict the pairs of LCBs involved in an inversion and shared color for the same in translocations, as BED features can't split over multiple contigs.

Single-nucleotide variants between each pair of genomes are generated using a [MUMmer][] pairwise alignment followed by use of the [`show-snps`][show-snps] utility from the MUMmer suite.

The output is created in the directory `$OUT/$OUT_PREFIX.sv_snv/`. A subdirectory is created for each genome file in `IN_FOFN`, and within these subdirectories, tracks in the form `{$GENOME1}_{$GENOME2}.sv.bed` are generated, which use `$GENOME1` as a reference and map upon it the insertions, deletions, and rearrangements that most likely occurred to produce `$GENOME2`. Similarly named tracks ending in `.snv.bed` contain the SNVs. Finally, the corresponding `.sv_snv.bed` files combine the BED features from the other two files for simple display in a genome browser.

*Caveats for structural variants.* (1) Depending on the actual ancestry of each genome, of course, this may not even be close to what happened biologically; consider these annotations to be more like a [diff] between the two genomes that can provide a rough distance metric and sense of where double stranded breaks and recombination likely occurred. (2) GRIMM implements the Hannenhalli-Pevzner algorithm, which is based on inversions only. In most situations, a [DCJ model] may be more appropriate (not yet implemented here). (3) The alignment and GRIMM analysis essentially consider each contig in your input files to be a separate chromosome in a multichromosomal genome, so if you have a low quality assembly, this analysis may deviate significantly from reality. (4) Because GRIMM only allows circular genomes to be compared with other circular genomes, and only for unichromosomal genomes, we have degraded its use to its multichromosomal mode only, which will not entirely correctly interpret contigs in your genomes that you have circularized.

This task requires you to set the `IN_FOFN`, `OUT_PREFIX`, `SEED_WEIGHT`, and `LCB_WEIGHT` environment variables. See [Environment variables](#environment-variables) for a description of each.

`IN_FOFN` is a file containing the full paths (one per line) to FASTA files containing contigs for whole genome sequences that you intend to compare with [Mauve].

[BED format]: https://genome.ucsc.edu/FAQ/FAQformat.html#format1
[lcbs]: http://darlinglab.org/mauve/user-guide/introduction.html
[GRIMM]: http://grimm.ucsd.edu/GRIMM/
[diff]: http://en.wikipedia.org/wiki/Diff_utility
[DCJ model]: http://bioinformatics.oxfordjournals.org/content/24/13/i114.abstract
[show-snps]: http://mummer.sourceforge.net/manual/#snps

#### heatmap

`rake heatmap` builds off of the SNV components of the `sv_snv` output by creating a node-link file with SNV distances between all of the input genomes.  This is then saved to a JSON file that can be used as the input for the heatmap visualization in [pathoSPOT-visualize][].

Note that this task requires use of `IN_QUERY` instead of the simpler `IN_FOFN` approach to selecting input genomes, because it expects metadata (date, location, MLST, etc.) to be queriable in PathogenDB for each of the genomes. This data is needed by [pathoSPOT-visualize][] in order to draw the corresponding parts of the visualization.

#### parsnp

FIXME: `rake parsnp` ... should be documented.

In brief, it produces similar output to `rake heatmap` for use with [pathoSPOT-visualize][], but uses parsnp instead of MUMmer to calculate SNV distances between the sequences.

In order for parsnp to complete in a reasonable amount of time and with acceptable core genome sizes (e.g., >50%), you may specify `MASH_CUTOFF` and `MAX_CLUSTER_SIZE`, which tune a preclustering step that is done with [mash][]. Clusters up to `MASH_CUTOFF` units in diameter are created, with the size of each cluster capped at `MAX_CLUSTER_SIZE`. Parsnp will be run separately on each cluster and distances remerged into the final output.

[mash]: https://mash.readthedocs.io/en/latest/

#### mugsy

`rake mugsy` requires you to set the `IN_FOFN`, `OUT_PREFIX`, and `OUTGROUP` environment variables. See [Environment variables](#environment-variables) for a description of each.

`IN_FOFN` is a file containing the full paths (one per line) to FASTA files containing contigs for whole genome sequences that you intend to compare with [Mugsy].  Mugsy will first align the whole genomes to each other, creating MAF alignment files that are converted back into a multisequence FASTA file with one fully aligned sequence per genome. [ClustalW][] is used to convert this into a PHYLIP file, which is then fed to [RAxML][] to produce a phylogenetic tree.

**Important:** in order for this task to succeed, the input FASTA files must have initial sequence IDs (the first line starting with ">") that are unique *after truncation to 10 characters* among all of the genomes being compared. This is due to the limitations of the [PHYLIP format][].

Output will be found as files starting with "RAxML_" in your `OUT` directory, with `RAxML_bestTree.$OUT_PREFIX` containing the tree with "evolutionary time" branch lengths in [Newick format][]. `$OUT_PREFIX_snp_tree.newick` will contain a similar tree, except the branch lengths are rescaled to the SNP distances between nodes in the tree, using the calculated marginal ancestral states.

[Mugsy]: http://mugsy.sourceforge.net/
[ClustalW]: http://www.clustal.org/clustal2/
[PHYLIP format]: http://www.bioperl.org/wiki/PHYLIP_multiple_alignment_format
[RAxML]: http://sco.h-its.org/exelixis/web/software/raxml/index.html
[Newick format]: http://en.wikipedia.org/wiki/Newick_format

#### mugsy_plot

`rake mugsy_plot` generates phylograms using R's `ape` library from the phylogenetic trees produced in the `rake mugsy` task. Remember to specify `OUT_PREFIX` if you have already run `rake mugsy` so it can find your tree files; if not, you'll need to specify *all* of the variables required for `rake mugsy`.  You will find the plots saved as PDF files in the `OUT` directory.

#### mauve

`rake mauve` requires you to set the `IN_FOFN`, `OUT_PREFIX`, `SEED_WEIGHT`, and `LCB_WEIGHT` environment variables. See [Environment variables](#environment-variables) for a description of each.

`IN_FOFN` is a file containing the full paths (one per line) to FASTA files containing contigs for whole genome sequences that you intend to compare with [Mauve].

[Mauve]: http://asap.genetics.wisc.edu/software/mauve/

### Dependency graph

This Rakefile is able to build a dependency graph of its intermediate files from itself.  Use the `rake graph` task for this; it will be generated at `$OUT/pathogendb-comparison.png`.

![Dependency graph](https://pakt01.u.hpc.mssm.edu/pathogendb-comparison.png)

## Other notes

This pipeline downloads and installs the appropriate versions of Mugsy, Mauve, CLUSTAW, RAxML, GRIMM, GBlocks, mash, and HarvestTools into `vendor/`.
