#!/usr/bin/env python
"""
Creates an .npz file with NumPy arrays extracted from a series of parsnp.vcf files. Saving
the data as NumPy arrays allows for fast loading and subsetting, e.g. by pathogendb-viz pages.

For each parsnp.vcf file, the .npz will contain three or four arrays (# is an integer index):
- 'vcf_mat_#' => A two-dimensional int16 array (.shape = (A, B)) of the allele calls
- 'vcf_allele_info_#' => A one-dimensional <str, uint64, str> array (.size = B) that contains 
   the allele info from the leftmost VCF columns, specifically CHROM, POS, and ALT. 
   **If `--fastas` is provided,** the .fasta and .bed for the reference are consulted to add 
   more columns: <str, uint64, uint64, str, str> for gene, nt_pos, aa_pos, aa_alt, and desc.
   `--sequin_annotations` may be used to look for .features_table.txt annotations instead.
- 'seq_list_#' => A one-dimensional str array (.size = A) of the sequence names
- 'ref_chrom_sizes_#' => **If `--fastas` is provided,** this is a one-dimensional 
   <str, uint64> array of contig names and sizes for the reference .fasta file.
"""

import sys
from os import access, R_OK
from os.path import splitext, basename, isfile
from tqdm import tqdm
import numpy as np
import re
import argparse

from pylib.parsnp_vcf import load_parsnp_vcf, enhance_allele_info, fasta_chrom_sizes

BED_EXTENSION = '.bed'
SEQUIN_EXTENSION = '.features_table.txt'
DEFAULT_GENETIC_CODE = 11


def read_vcfs(parsnp_vcfs, in_paths=None, sequin_format=False, transl_table=DEFAULT_GENETIC_CODE, 
        clean_names=None, quiet=False):
    vcf_data = {}
    opts = {"progress": not quiet}
    annots_ext = SEQUIN_EXTENSION if sequin_format else BED_EXTENSION
    
    if not quiet:
        sys.stderr.write("INFO: %d VCF files will be processed.\n" % len(parsnp_vcfs))
    
    for i, vcf_file in enumerate(parsnp_vcfs):
        seq_list, vcf_mat, vcf_allele_info = load_parsnp_vcf(vcf_file, **opts)
        clean_seq_list = seq_list
        if clean_names is not None and len(clean_names) > 0:
            clean_seq_list = map(lambda seq: re.sub(clean_names, '', seq), seq_list)
        vcf_data['seq_list_%d' % i] = np.array(clean_seq_list)
        vcf_data['vcf_mat_%d' % i] = vcf_mat
        if in_paths is not None:
            ref_seq = seq_list[0]
            ref_fasta = next((x for x in in_paths if splitext(basename(x))[0] == ref_seq), None)
            ref_annots = re.sub(r'\.fa(sta)?$', annots_ext, ref_fasta)
            if (isfile(ref_fasta) and access(ref_fasta, R_OK) and 
                    isfile(ref_annots) and access(ref_annots, R_OK)):
                vcf_allele_info = enhance_allele_info(vcf_allele_info, ref_fasta, ref_annots, 
                        sequin_format, transl_table, **opts)
                vcf_data['ref_chrom_sizes_%d' % i] = fasta_chrom_sizes(ref_fasta)
            elif not quiet:
                sys.stderr.write("WARN: Couldn't find .fasta + %s annotations for %s\n" % 
                        (annots_ext, ref_seq))
        vcf_data['vcf_allele_info_%d' % i] = vcf_allele_info
    
    return vcf_data


def write_npz(output, vcf_data):
    if output is None or output == '-':
        if sys.stdout.isatty():
            raise IOError("Can't print .npz data to a terminal. Please use -o or pipe to file.")
        output = sys.stdout
    np.savez(output, **vcf_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parsnp_vcfs', metavar='PARSNP_VCF_FILE', type=str, nargs='*', 
            help='Path to the .vcf files (created with `harvesttools -i parsnp.ggr -V ...`).')
    parser.add_argument("-o", "--output", default=None, 
            help="Output numpy arrays to this file if set, otherwise will use STDOUT.")
    parser.add_argument("-f", "--fastas", default=None, 
            help="A file-of-filenames listing paths to the original fasta files for these " +
            "genomes. If given, they and corresponding annotation files (default: <filename>.bed) " +
            "will be consulted to annotate VCF alleles with gene names and predicted AA variants.")
    parser.add_argument("-s", "--sequin_annotations", default=False, action='store_true',
            help="If used, will search for annotations in Sequin feature table format, with the " +
            "extension .features_table.txt (instead of .bed) for each genome in --fastas.")
    parser.add_argument("-c", "--clean_genome_names", default=None, 
            help="A python regex, that if given, will be scrubbed out of genome names in the .vcf.")
    parser.add_argument("-t", "--transl_table", type=int, default=DEFAULT_GENETIC_CODE, 
            help="Which NCBI Genetic Code table to use for AA translations; default=11 (bacterial)." +
            " For a full list see: https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi")
    parser.add_argument("-q", "--quiet", default=False, action='store_true',
            help="Don't show progress bars while processing files.")
    args = parser.parse_args()
    
    if len(args.parsnp_vcfs) == 0:
        parser.print_help(file=sys.stderr)
        sys.exit(1)
    
    in_paths = None
    if args.fastas is not None:
        with open(args.fastas, "r") as f:
            in_paths = map(lambda line: line.strip(), f.readlines())
    
    vcf_data = read_vcfs(args.parsnp_vcfs, in_paths, args.sequin_annotations, args.transl_table,
            args.clean_genome_names, args.quiet)
    
    try:
        write_npz(args.output, vcf_data)
    except IOError as e:
        sys.stderr.write("FATAL: " + e.message + "\n")
        parser.print_help(file=sys.stderr)
        sys.exit(2)