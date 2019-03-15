import sys
import re
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Alphabet import generic_dna
from collections import defaultdict

from .utils import contig_to_vcf_chrom

COMMA_DELIM_INTEGERS = r'^(\d+( *, *)?)+$'

class Annot:
    """
    A class representing a generic annotation of a gene with a coding sequence.
    Note that this class does not store the name of the contig that the gene is on.
    All positions within this class are ZERO-indexed and ranges are RIGHT-OPEN, like BED files.
    """
    
    def __init__(self, start, end, rev_strand, seq_record, coding_blocks=[]):
        self.start = start
        self.end = end
        self.rev_strand = rev_strand
        self.seq_record = seq_record
        self.coding_blocks = sorted(coding_blocks, key=lambda range: range[0])

    def nt_pos(self, pos):
        """
        Given a ZERO-indexed position `pos` on the contig, what is the relative ZERO-indexed 
        nucleotide position within this annotation's coding sequence?
        """
        seq_consumed = 0
        if self.coding_blocks is None or len(self.coding_blocks) == 0:
            return int(self.end - pos - 1 if self.rev_strand else pos - self.start)
        for block in (reversed(self.coding_blocks) if self.rev_strand else self.coding_blocks):
            if pos >= block[0] and pos < block[1]:
                if self.rev_strand: return (block[1] - pos - 1 + seq_consumed)
                else: return (pos - block[0] + seq_consumed)
            else: 
                seq_consumed += block[1] - block[0]
        raise RuntimeError("Position %d not within feature %s" % (pos, self.seq_record.name))

    def aa_pos(self, pos):
        """Same as above, but in amino acids."""
        return self.nt_pos(pos) // 3

    def aa_alts(self, alts, pos, transl_table=11):
        """
        Given an iterable `alts` of nucleotides to be substituted at contig position `pos`,
        return a list of the corresponding amino acid changes that would occur.
        `transl_table` is the NCBI genetic code to use when translating the coding sequence.
        """
        aa_alts = []
        nt_pos = self.nt_pos(pos)
        aa_pos = self.aa_pos(pos)
        for i, allele in enumerate(alts):
            mut_seq = str(self.seq_record.seq)
            if self.rev_strand:
                allele = str(Seq(allele, generic_dna).reverse_complement())
            if i == 0 and mut_seq[nt_pos].upper() != allele.upper():
                # Sanity check: the reference (first) allele should be the nucleotide at nt_pos!
                raise RuntimeError("Ref allele '%s' is incorrect for %s:c.%d" % (allele, 
                        self.seq_record.name, nt_pos + 1))
            # pad partial codons for the rare off-length annotations to avoid a BiopythonWarning
            mut_seq_pad = "N" * (-len(mut_seq) % 3)
            mut_seq = mut_seq[0:nt_pos] + allele + mut_seq[nt_pos+1:None] + mut_seq_pad
            mut_seq_aa = str(Seq(mut_seq, generic_dna).translate(table=transl_table))
            aa_alts.append(mut_seq_aa[aa_pos])
        return aa_alts


def get_bed_annots(bed_path, ref_contigs, quiet=False):
    """
    Load all genes in the BED file as SeqRecords, fetching their sequence data from the reference.
    ref_contigs is a dictionary of ref contig sequences created with BioPython's SeqIO.to_dict().
    
    For documentation on the BED format, see: https://genome.ucsc.edu/FAQ/FAQformat.html#format1
    
    Returns a dictionary with contig names as keys, and lists of (start, end, rev_strand, SeqRecord,
    coding_blocks) tuples for each contig in ref_contigs.
    """
    annots = defaultdict(list)
    with open(bed_path) as f:
        for line in f:
            line = line.strip().split("\t")
            # Note: BED coordinates are 0-indexed, right-open.
            chrom, start, end, name, strand = line[0], int(line[1]), int(line[2]), line[3], line[5]
            gene_id = line[12] if len(line) >= 13 else ""
            desc = line[13] if len(line) >= 14 else ""
            ref_contig = ref_contigs[chrom]
            gene_seq = Seq(str(ref_contig.seq)[start:end], generic_dna)
            if strand == '-':
                gene_seq = gene_seq.reverse_complement()
            gene_seq_record = SeqRecord(gene_seq, id=gene_id, name=name, description=desc)
            
            coding_blocks = []
            if (len(line) >= 12 and line[9].isdigit() and re.match(COMMA_DELIM_INTEGERS, line[10])
                    and re.match(COMMA_DELIM_INTEGERS, line[11])):
                # We have full blockCount, blockSizes, and blockStarts annotations
                block_starts = map(int, re.split(r'\s*,\s*', line[11]))
                thick_start = int(line[6]) if line[6].isdigit() else start
                thick_end = int(line[7]) if line[7].isdigit() else end
                for i, block_size in enumerate(re.split(r'\s*,\s*', line[10])[0:int(line[9])]):
                    if i >= len(block_starts): break
                    block_start = block_starts[i] + start
                    block_end = block_start + int(block_size)
                    if block_end <= thick_start: next
                    if block_start > thick_end: next
                    block_start = max(thick_start, block_start)
                    block_end = min(thick_end, block_end)
                    coding_blocks.append((block_start, block_end))
            elif len(line) >= 8 and line[6].isdigit() and line[7].isdigit():
                # Only thickStart and thickEnd are specified. In this case, there is one coding block.
                coding_blocks.append((int(line[6]), int(line[7])))
            else:
                coding_blocks.append((start, end))
            
            annot = Annot(start, end, strand == '-', gene_seq_record, coding_blocks)
            annots[contig_to_vcf_chrom(chrom)].append(annot)
    return annots


def get_sequin_annots(sequin_path, ref_contigs, quiet=False):
    """
    Load all genes in the Sequin table as SeqRecords, fetching their sequence data from the reference.
    ref_contigs is a dictionary of ref contig sequences created with BioPython's SeqIO.to_dict().
    
    For documentation on the Sequin table format, see: https://www.ncbi.nlm.nih.gov/Sequin/table.html
    
    Returns a dictionary with contig names as keys, and lists of (start, end, rev_strand, SeqRecord,
    coding_blocks) tuples for each contig in ref_contigs.
    """
    annots = defaultdict(list)
    
    # We need a dummy class to hold the current state while parsing
    # (otherwise the below private functions can't modify it; there's no "nonlocal" in python 2.x)
    class _:
        in_contig = None
        in_feature = None
        gene_name = None
        desc = None
        chrom_start = None
        chrom_end = None
        strand = None
        feature_seq_str = ""
        coding_blocks = []
    
    def _save_sequin_feature():
        # The only features we care about are the CDS features. Others get discarded during parsing.
        if _.in_feature == "CDS":
            if len(_.feature_seq_str) == 0:
                if not quiet: sys.stderr.write("WARN: 0-length CDS in contig %s" % _.in_contig)
            elif _.gene_name is None or _.strand is None or _.chrom_start is None or _.chrom_end is None:
                if not quiet: sys.stderr.write("WARN: invalid CDS feature in contig %s" % _.in_contig)
            else:
                gene_seq = Seq(_.feature_seq_str, generic_dna)
                if _.strand == '-':
                    gene_seq = gene_seq.reverse_complement()
                gene_seq_record = SeqRecord(gene_seq, id=_.gene_name, name=_.gene_name, description=_.desc)
                annot = Annot(_.chrom_start, _.chrom_end, _.strand == '-', gene_seq_record, 
                        _.coding_blocks)
                annots[contig_to_vcf_chrom(_.in_contig)].append(annot)
        _.in_feature = _.gene_name = _.desc = _.chrom_start = _.chrom_end = _.strand = None
        _.feature_seq_str = ""
        _.coding_blocks = []
        
    def _update_sequin_feature(fields):
        if fields[0] != "" and fields[1] != "":
            # If the first two fields are present, this specifies a sequence range
            if not (fields[0].isdigit() and fields[1].isdigit()):
                # We will only attempt to utilize *complete* CDS features
                # (None of the start or end positions can be qualified by ">" or "<")
                _.in_feature = "CDS-partial"
                return

            # Append the specified sequence to the `_.feature_seq_str`.
            # Note: Sequin table coordinates, like GenBank, are 1-indexed, right-closed.
            start = int(fields[0])
            end = int(fields[1])
            if _.strand is None: 
                _.strand = '+' if start <= end else '-'
            elif _.strand != ('+' if start <= end else '-'):
                sys.stderr.write("WARN: strand changed direction, invalid CDS")
                _.in_feature = "CDS-partial"
                return
            if _.strand == '-':
                start, end = end, start
            start -= 1
            ref_contig = ref_contigs[_.in_contig]
            seg = str(ref_contig.seq)[start:end]
            _.coding_blocks.append((start, end))
            _.feature_seq_str = seg + _.feature_seq_str if _.strand == '-' else _.feature_seq_str + seg
            _.chrom_start = min(start, _.chrom_start if _.chrom_start is not None else float('inf'))
            _.chrom_end = max(end, _.chrom_end if _.chrom_end is not None else float('-inf'))
            
        elif len(fields) >= 5:
            # If the first three fields are blank, this specifies a qualifier key + value
            if fields[3] == "gene":
                _.gene_name = fields[4]
            elif fields[3] == "product":
                _.desc = fields[4]
         
    with open(sequin_path) as f:
        for line in f:
            line = line.rstrip("\n")
            fields = line.split("\t", 4)
            if len(line.strip()) == 0:
                # Whitespace-only lines signal the end of feature data for a contig.
                # They may be followed by INFO: lines from the annotator, which we ignore.
                _save_sequin_feature()
                _.in_contig = None
            elif _.in_contig is None and line[0] == '>':
                # Lines that begin with ">Feature " signal the start of feature data for a contig
                # Fields are separated by spaces; the second field is the full contig ID
                _save_sequin_feature()
                sp_fields = line[1:].split(' ')
                if sp_fields[0] == 'Feature' and len(sp_fields) >= 2:
                    if ref_contigs.has_key(sp_fields[1]):
                        _.in_contig = sp_fields[1]
                    elif not quiet:
                        sys.stderr.write("WARN: unknown contig in Sequin file: %s" % sp_fields[1])
            elif _.in_contig is not None:
                if len(fields) < 3: 
                    if not quiet: sys.stderr.write("WARN: incomplete Sequin line: %s" % line)
                    next
                in_new_feature = fields[2].strip() != ""
                if _.in_feature is None or in_new_feature:
                    _save_sequin_feature()
                    _.in_feature = fields[2].strip()
                    if _.in_feature == "CDS":
                        _update_sequin_feature(fields)
                elif _.in_feature == "CDS":
                    _update_sequin_feature(fields)
            
    return annots