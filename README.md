# PathogenDB genome comparison

## Requirements

As of now, this only runs on [Minerva](http://hpc.mssm.edu) because it uses modules and software found on that cluster.  In due time, it might be made portable to other systems.

Currently, you also need to be in the `pacbioUsers` group on Minerva and have access to the `premium` LSF queue and the `acc_PBG` LSF account.

## Usage

First, clone this repository to a directory and `cd` into it.  You'll want to configure your environment first using the included script:

    $ cp scripts/example.env.sh scripts/env.sh  

The defaults should work for any Minerva user.  Then, you can source the script into your shell and install required gems locally into the `vendor/bundle` directory as follows:

    $ source scripts/env.sh
    $ bundle install --deployment

When this is complete, you should be able to run rake to kick off the pipeline as follows. However, also read **[Environment variables](#environment-variables)** below, as certain tasks require more variables to be set before being invoked.

    $ rake -T                    # list the available tasks
    $ rake $TASK_NAME            # run the task named $TASK_NAME
    $ FOO="bar" rake $TASK_NAME  # run $TASK_NAME with FOO set to "bar"

When firing up the pipeline in a new shell, always remember to `source scripts/env.sh` before running `rake`.

### Environment variables

Certain tasks within the pipeline require you to specify some extra information as an environment variable.  You can do this by either editing them into `scripts/env.sh` and re-running `source scripts/env.sh`, or you can prepend them to the `rake` invocation, e.g.:

    $ IN_FOFN=LB_genomes.fofn rake mugsy

If a required environment variable isn't present when a task is run and there is no default value, rake will abort with an error message.

Variable             | Required by                           | Default | Purpose
---------------------|---------------------------------------|---------|-----------------------------------
`OUT`                | all tasks                             | ./out   | This is where your interim and completed files are saved
`IN_FOFN`            | `mugsy` `mauve`                       | (none)  | A file containing filenames that will be processed as input
`OUT_PREFIX`         | `mugsy` `mugsy_plot` `mauve`          | out     | This prefix will be prepended to output filenames (so you can track files generated for each invocation)
`OUTGROUP`           | `mugsy`                               | (none)  | The [outgroup][] to specify for `RAxML`
`SEED_WEIGHT`        | `mauve`                               | (none)  | Use this seed weight for calculating initial anchors
`LCB_WEIGHT`         | `mauve`                               | (none)  | Minimum pairwise LCB score

According to [Darling et al.](http://dx.doi.org/10.1371/journal.pone.0011147), a good default for both `SEED_WEIGHT` and `LCB_WEIGHT` typically chosen by Mauve is log2((avg genome size) / 1.5).

[outgroup]: http://en.wikipedia.org/wiki/Outgroup_%28cladistics%29

### Tasks

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

This pipeline downloads and installs the appropriate versions of Mugsy, Mauve, and RAxML into `vendor/`.
