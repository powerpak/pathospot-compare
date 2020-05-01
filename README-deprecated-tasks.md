## Deprecated tasks

These are tasks that were used in past versions of this pipeline, for alternative comparative genomics analyses. By default, they aren't loaded when running `rake`. If you want to re-activate them, add the following to your `scripts/env.sh`:

    export DEPRECATED_TASKS=1

Then, when you run `rake -T`, you will see the following new tasks:

    rake sv_snv
	rake heatmap
	rake mugsy
	rake mugsy_plot
	rake mauve

### Environment variables

Certain tasks within the pipeline require you to specify some extra information as an environment variable. 

If a required environment variable isn't present when a task is run and there is no default value, rake will abort with an error message.

Variable             | Required by                           | Default | Purpose
---------------------|---------------------------------------|---------|-----------------------------------
`IN_FOFN`            | `mugsy` `mauve` `sv_snv`              | (none)  | A file containing filenames that will be processed as input
`OUTGROUP`           | `mugsy`                               | (none)  | The [outgroup][] to specify for `RAxML`
`SEED_WEIGHT`        | `mauve` `sv_snv`                      | (none)  | Use this seed weight for calculating initial anchors
`LCB_WEIGHT`         | `mauve` `sv_snv`                      | (none)  | Minimum pairwise LCB score
`DISTANCE_THRESHOLD` | `heatmap`                             | 10      | The default SNP threshold that will be used for clustering the heatmap in [pathoSPOT-visualize][]
`IGB_DIR`            | `heatmap`                             | (none)  | An IGB Quickload directory that contains assemblies saved into PathogenDB`
`PATHOGENDB_URI`     | `heatmap`                             | (none)  | How to connect to the PathogenDB database. Must be formatted as `sqlite://relative/path/to/pathogen.db` or `mysql2://user:pass@host/database`

According to [Darling et al.](http://dx.doi.org/10.1371/journal.pone.0011147), a good default for both `SEED_WEIGHT` and `LCB_WEIGHT` typically chosen by Mauve is log2((avg genome size) / 1.5).

[outgroup]: http://en.wikipedia.org/wiki/Outgroup_%28cladistics%29

#### Optional variables

The following are not required by any tasks, but may be helpful:

Variable             | Default | Purpose
---------------------|---------|-----------------------------------
`LSF_DISABLE`        | (none)  | Set this variable to anything to globally disable submission of long tasks to LSF. This is probably a good idea if you are running on a Minerva interactive node.
`BED_LINES_LIMIT`    | 1000    | Don't write data to BED files for the `snv` task that would contain more than this number of lines of data. (Saves disk space.)

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

This Rakefile is able to build a dependency graph of its intermediate files from itself.  Use the `rake graph` task for this; it will be generated at `$OUT/pathospot-compare.png`.

### Other notes

If deprecated tasks are activated, the pipeline downloads and installs the appropriate versions of Mugsy, Mauve, CLUSTALW, RAxML, GRIMM and GBlocks into `vendor/`.