import re

def contig_to_vcf_chrom(contig_name):
    """
    Annotations may reference more complex contig names than the VCF does in its CHROM column.
    
    This function maps any given annotation's contig name to its corresponding VCF CHROM name.
    """
    return re.sub(r'\W.+$', '', contig_name)