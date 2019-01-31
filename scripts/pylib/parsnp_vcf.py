import re
import subprocess
import numpy as np
from tqdm import tqdm
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Alphabet import generic_dna
from collections import defaultdict

# For parsnp.vcf files produced by pathogendb-comparison, a CHROM field of 20 bytes would be 
# sufficient, but we'll add some extra room here just for safety.
# It's worth considering why we use bytestrings here instead of unicode; the reason is that none
# of these values should have anything but ASCII, and bytestrings offer >50% storage savings.
ALLELE_INFO_FIELDS = [
    ('chrom', 'S40'), 
    ('pos', np.uint64), 
    ('alt', 'S9')
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
                vcf_allele_info[i] = (cells[0], int(cells[1]), cells[4])
                i += 1

    # Trim the rows of numpy data to the actual number of lines read from the file
    vcf_mat = np.delete(vcf_mat, np.s_[i:], axis=1)
    vcf_allele_info = np.delete(vcf_allele_info, np.s_[i:])

    # Cleanup the names of sequences, which come with unnecessary suffixes from preprocessing steps
    seq_list = map(lambda x: re.sub(r'(\.\w+)+$', '', x), seq_list)
    
    # Return everything promised as a tuple.
    return seq_list, vcf_mat, vcf_allele_info


def enhance_allele_info(vcf_allele_info, fasta_path, bed_path, progress=True):
    """
    Takes the `vcf_allele_info` NumPy array produced by the above `load_parsnp_vcf()` function and
    enhances each row with `gene`, `nt_pos`, `aa_pos`, `aa_alt`, and `desc` information using the 
    reference genome sequence data at `fasta_path` and annotations at `bed_path`.
    
    TODO: could use more a systematic variant nomenclature, e.g. http://varnomen.hgvs.org/
    """
    vcf_alleles_extended = np.zeros(len(vcf_allele_info), dtype=ALLELE_INFO_EXTENDED_DTYPE)
    annots = defaultdict(list)
    
    # Load the reference genome's contigs as SeqRecords into their own dictionary.
    ref_contigs = SeqIO.to_dict(SeqIO.parse(open(fasta_path), "fasta"))
    
    # Load all genes in the BED file as SeqRecords, fetching their sequence data from the reference.
    # Caution: BED coordinates are 0-indexed, right-open.
    with open(bed_path) as f:
        for line in f:
            line = line.strip().split("\t")
            chrom, start, end, name, strand = line[0], int(line[1]), int(line[2]), line[3], line[5]
            id = line[12] if len(line) >= 13 else ""
            desc = line[13] if len(line) >= 14 else ""
            ref_contig = ref_contigs[chrom]
            gene_seq = Seq(str(ref_contig.seq)[start:end], generic_dna)
            if strand == '-':
                gene_seq = gene_seq.reverse_complement()
            gene_seq_record = SeqRecord(gene_seq, id=id, name=name, description=desc)
            annots[chrom].append((start, end, strand == '-', gene_seq_record))
    
    # Iterate through the VCF alleles, finding which genes they correspond to, and translating versions
    # of the gene for each allele to figure out the corresponding AA variants
    vcf_iter = tqdm(vcf_allele_info, desc="Annotating VCF alleles") if progress else vcf_allele_info
    for i, row in enumerate(vcf_iter):
        # VCF coordinates for the POS column are 1-indexed. This resets them to 0-indexed.
        chrom, pos, alt = (row['chrom'], int(row['pos'] - 1), row['alt'])
        gene, nt_pos, aa_pos, aa_alt, desc = ("", 0, 0, "", "")
        genes = annots[row['chrom']]
        genes = [g for g in genes if g[0] <= pos and g[1] > pos]
        # Any SNP mapping to multiple genes is annotated as such (no automatic resolution to one gene)
        if len(genes) > 1:
            gene = str(len(genes))
            desc = gene + " genes: " + ", ".join(map(lambda g: g[3].name, genes))
        # Annotate SNPs mapping to a single gene, unless the reference allele is "N" (possibly
        # indicating this part of the reference was masked out by parsnp? FIXME: investigate that)
        elif len(genes) == 1 and alt.split(",")[0].upper() != 'N':
            gene_match = genes[0]
            gene_seq_record = gene_match[3]
            gene = gene_seq_record.name
            desc = gene_seq_record.description
            nt_pos = int(gene_match[1] - pos - 1 if gene_match[2] else pos - gene_match[0])
            aa_pos = nt_pos // 3
            aa_alts = []
            for j, allele in enumerate(alt.split(",")):
                mut_seq = str(gene_seq_record.seq)
                if gene_match[2]:
                    allele = str(Seq(allele, generic_dna).reverse_complement())
                # pad partial codons for the rare off-length annotations to avoid a BiopythonWarning
                mut_seq_pad = "N" * (-len(mut_seq) % 3)
                mut_seq = mut_seq[0:nt_pos] + allele + mut_seq[nt_pos+1:None] + mut_seq_pad
                mut_seq_aa = str(Seq(mut_seq, generic_dna).translate(table=11))
                if len(mut_seq_aa) <= aa_pos:
                    print chrom, pos, alt, gene_seq_record.seq, mut_seq, mut_seq_aa, aa_pos
                aa_alts.append(mut_seq_aa[aa_pos])
            aa_alt = ",".join(aa_alts)
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
        chrom_sizes[i] = (contig.id, len(contig))
    return chrom_sizes