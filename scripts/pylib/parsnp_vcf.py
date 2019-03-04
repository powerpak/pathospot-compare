import re
import subprocess
import numpy as np
from tqdm import tqdm
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.Alphabet import generic_dna

from .get_annots import get_bed_annots, get_sequin_annots
from .utils import contig_to_vcf_chrom

# For parsnp.vcf files produced by pathogendb-comparison, a CHROM field of 20 bytes would be 
# sufficient, but we'll add some extra room here just for safety.
# It's worth considering why we use bytestrings here instead of unicode; the reason is that none
# of these values should have anything but ASCII, and bytestrings offer >50% storage savings.
ALLELE_INFO_FIELDS = [
    ('chrom', 'S40'), 
    ('pos', np.uint64), 
    ('alt', 'S11')  # 1 REF + 4 possible ALTs + "N" + five commas
]
ALLELE_INFO_DTYPE = np.dtype(ALLELE_INFO_FIELDS)
ALLELE_INFO_EXTENDED_DTYPE = np.dtype(ALLELE_INFO_FIELDS + [
    ('gene', 'S20'),
    ('nt_pos', np.uint64),
    ('aa_pos', np.uint64),
    ('aa_alt', 'S20'),
    ('desc', 'S40')
])
CHROM_SIZES_DTYPE = np.dtype([('chrom', 'S40'), ('size', np.uint64)])
DEFAULT_GENETIC_CODE = 11


def load_parsnp_vcf(filename, progress=True):
    """
    Loads a parsnp.vcf file produced by parsnp into a NumPy matrix of alleles, along with another
    NumPy array of allele info which contains the CHROM, POS, and ALT fields.
    
    Returns the list of sequences in the VCF, the matrix of alleles, and the array of allele info
    as a tuple.
    """
    # Read in the VCF file
    with open(filename) as vcf:
        start_reading = False
        total_lines = int(subprocess.check_output(['wc', '-l', filename]).split()[0])
        i = 0
        vcf_iter = tqdm(vcf, total=total_lines, desc="Reading VCF file") if progress else vcf
        for line in vcf_iter:
            # Skip all lines until we get to the #CHROM line
            # The first 9 columns are standard VCF columns with allele info
            if line.startswith('#CHROM'):
                # Get the remaining column headers, which are the names of the input sequences
                seq_list = line.split()[9:]
                # Initialize a matrix that can hold all variants for all sequences
                # Conservatively, allocate enough rows for the total number of lines in the file
                # Because of lines skipped above for the VCF header, this is a slight overestimate
                vcf_mat = np.zeros((len(seq_list), total_lines), dtype=np.int16)
                vcf_allele_info = np.zeros(total_lines, dtype=ALLELE_INFO_DTYPE)
                # Start reading rows
                start_reading = True
            elif start_reading:
                # Each cell is an allele for a particular sequence
                cells = line.split()
                vcf_mat[:, i] = map(int, line.split()[9:])
                # VCF columns are 
                # We prepend the REF to the ALT, because some VCFs use allele 0, which is the REF
                vcf_allele_info[i] = (cells[0], int(cells[1]), cells[3] + ',' + cells[4])
                i += 1

    # Trim the rows of numpy data to the actual number of lines read from the file
    vcf_mat = np.delete(vcf_mat, np.s_[i:], axis=1)
    vcf_allele_info = np.delete(vcf_allele_info, np.s_[i:])

    # Cleanup the names of sequences, which come with unnecessary suffixes from preprocessing steps
    seq_list = map(lambda x: re.sub(r'(\.\w+)+$', '', x), seq_list)
    
    # Return everything promised as a tuple.
    return seq_list, vcf_mat, vcf_allele_info


def enhance_allele_info(vcf_allele_info, fasta_path, annots_path, sequin_format=False, 
        transl_table=DEFAULT_GENETIC_CODE, progress=True):
    """
    Takes the `vcf_allele_info` NumPy array produced by the above `load_parsnp_vcf()` function and
    enhances each row with `gene`, `nt_pos`, `aa_pos`, `aa_alt`, and `desc` information using the 
    reference genome sequence data at `fasta_path` and annotations at `annots_path`.
    
    TODO: could use more a systematic variant nomenclature, e.g. http://varnomen.hgvs.org/
    """
    vcf_alleles_extended = np.zeros(len(vcf_allele_info), dtype=ALLELE_INFO_EXTENDED_DTYPE)
    
    # Load the reference genome's contigs as SeqRecords into their own dictionary.
    ref_contigs = SeqIO.to_dict(SeqIO.parse(open(fasta_path), "fasta"))
    
    # Load annotations from the `annots_path`.
    get_annots = get_sequin_annots if sequin_format else get_bed_annots
    annots = get_annots(annots_path, ref_contigs, quiet=not progress)
    
    # Iterate through the VCF alleles, finding which genes they correspond to, and translating versions
    # of the gene for each allele to figure out the corresponding AA variants
    vcf_iter = tqdm(vcf_allele_info, desc="Annotating VCF alleles") if progress else vcf_allele_info
    for i, row in enumerate(vcf_iter):
        # VCF coordinates for the POS column are 1-indexed. This resets them to 0-indexed.
        chrom, pos, alt = (row['chrom'], int(row['pos'] - 1), row['alt'])
        gene, nt_pos, aa_pos, aa_alt, desc = ("", 0, 0, "", "")
        genes = annots.get(row['chrom'], [])
        genes = [g for g in genes if g.start <= pos and g.end > pos]
        # Any SNP mapping to multiple genes is annotated as such (no automatic resolution to one gene)
        if len(genes) > 1:
            gene = str(len(genes))
            desc = gene + " genes: " + ", ".join(map(lambda g: g.seq_record.name, genes))
        # Annotate SNPs mapping to a single gene, unless the reference allele is "N" (possibly
        # indicating this part of the reference was masked out by parsnp? FIXME: investigate that)
        elif len(genes) == 1 and alt.split(",")[0].upper() != 'N':
            gene_match = genes[0]
            gene = gene_match.seq_record.name
            desc = gene_match.seq_record.description
            nt_pos = gene_match.nt_pos(pos)
            aa_pos = gene_match.aa_pos(pos)
            aa_alts = gene_match.aa_alts(alt.split(","), pos, transl_table)
            aa_alt = ",".join(aa_alts)
        # Convert POS back to 1-indexed for parity with VCF. NOTE: nt_pos and aa_pos are ZERO-indexed!
        vcf_alleles_extended[i] = (chrom, pos + 1, alt, gene, nt_pos, aa_pos, aa_alt, desc)

    return vcf_alleles_extended


def fasta_chrom_sizes(fasta_path):
    """
    Given the path to a fasta file, return a NumPy array of (sequence name, size) tuples.
    """
    # Load the fasta's contigs as SeqRecords into their own dictionary.
    fasta_contigs = list(SeqIO.parse(open(fasta_path), "fasta"))
    chrom_sizes = np.zeros(len(fasta_contigs), dtype=CHROM_SIZES_DTYPE)
    for i, contig in enumerate(fasta_contigs):
        chrom_sizes[i] = (contig_to_vcf_chrom(contig.id), len(contig))
    return chrom_sizes