#!/usr/bin/env python
"""
Usage: computeSNPTree.py newick_tree fasta_1 fasta_2 ...

Re-works a maximum-likelihood phylogenetic tree in Newick format
into a new tree with branch lengths based on the SNP distance 
between each node. SNP distances are calculated with nucmer,
searching the FASTA files in order for the corresponding sequence.
The nodes of the input tree must be labeled.

IMPORTANT: nucmer, delta-filter, and show-snps from MUMmer 3.23 must be 
on PATH before running this. On Minerva, this should be as easy as:

    $ module load mummer/3.23

When using this script to resize branches in a RAxML_nodeLabelledRootedTree,

argv[1] should be the RAxML_nodeLabelledRootedTree
argv[2] should be the RAxML_marginalAncestralStates, converted to FASTA
argv[3] should be a FASTA file with the aligned leaf node sequences 
            (e.g., extracted from a Mugsy .maf)
            
You can convert RAxML_marginalAncestralStates to FASTA with:

    $ sed 's/^\([[:alnum:]]\+\) \+/>\1\n/g' input > output.fasta
"""

##
# Original by Oliver Attie
# Modified by Ted Pak
##

from Bio import Phylo, SeqIO
import sys
import os
import subprocess
import re
import tempfile

def computeDistance(fasta_seqs, contig1, contig2):
    count = 0
    temp_dir = tempfile.mkdtemp()
    initial_cwd = os.getcwd()
    os.chdir(temp_dir)
    extractContig(fasta_seqs, contig1, "Contig1.fa")
    extractContig(fasta_seqs, contig2, "Contig2.fa")
    os.system("nucmer -p "+str(contig1)+"_"+str(contig2)+" Contig1.fa Contig2.fa")
    os.system("delta-filter -lr "+str(contig1)+"_"+str(contig2)+".delta > "+str(contig1)+"_"+str(contig2)+"_df1.delta")
    nucmer_output = subprocess.check_output("show-snps -Clr "+str(contig1)+"_"+str(contig2)+"_df1.delta", shell=True)
    nucmer_snps = nucmer_output.split("\n")
    for snp in nucmer_snps:
        data = re.split("\s+", snp)
        if len(data) > 2:
            if data[2] in ['A','C','G','T'] and data[3] in ['A','C','G','T'] and data[2] != "." and data[3] != ".":
                count += 1
    os.chdir(initial_cwd)
    return count


def extractContig(fasta_seqs, contig, outfile):
    fh = open(outfile, 'w')
    for seq_file in fasta_seqs:
        for seq_record in seq_file:
            if str(seq_record.id[0:10]).strip() == str(contig).strip():
                seq_id = str(">"+str(contig)+"\n")
                fh.write(seq_id)
                fh.write(str(seq_record.seq+"\n"))
                fh.close()
                return
    raise RuntimeError("Could not find a sequence in the given fasta_files for %s" % contig)


def recomputeBranchLengths(tree, fasta_files):
    fasta_seqs = map(lambda file: list(SeqIO.parse(file, "fasta")), fasta_files)
    
    for clade in tree.find_clades(order='level'):
        clade_depth = len(tree.get_path(clade))
    
        # Special cases for branches of the root node
        if clade_depth==1 and clade.name:
               print "ROOT_", clade.name
               clade.branch_length = computeDistance(fasta_seqs, "ROOT", clade.name)
        if clade_depth==1 and clade.confidence:
               print "ROOT_", clade.confidence
               clade.branch_length = computeDistance(fasta_seqs, "ROOT", clade.confidence)

        # For deeper branches
        if clade_depth > 1:
            ancestor = tree.get_path(clade)[clade_depth - 2]
        
            # This named strain branches from another named strain
            if(clade.name and ancestor.name):
                clade.branch_length = computeDistance(fasta_seqs, clade.name, ancestor.name) 

            # This marginal ancestral state branches from another marginal ancestral state
            if(clade.confidence and ancestor.confidence):
               clade.branch_length = computeDistance(fasta_seqs, clade.confidence, ancestor.confidence)

            # This named strain branches from a numbered marginal ancestral state
            if(clade.name and ancestor.confidence):
                print clade.name, "_", ancestor.confidence
                clade.branch_length = computeDistance(fasta_seqs, clade.name, ancestor.confidence)
                
    return tree


if __name__ == "__main__":
    
    if len(sys.argv) < 3:
        print __doc__
        sys.exit(1)
        
    raxml_nlrt_filename = sys.argv[1]
    fasta_files = sys.argv[2:]
    
    # Open the original tree
    tree = Phylo.read(raxml_nlrt_filename, "newick")
    recomputeBranchLengths(tree, fasta_files)
    
    # Finally, write the new tree with the modified branch_lengths to stdout
    Phylo.write(tree, sys.stdout, "newick")