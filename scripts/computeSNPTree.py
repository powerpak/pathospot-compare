#!/usr/bin/env python

# =====================
# = computeSNPTree.py =
# =====================
#
# Re-works a RAxML_nodeLabelledRootedTree into a tree with branch lengths
# based on the SNP distance between each node.
# SNP distances are calculated with nucmer.
# 
# Original by Oliver Attie,
# modified by Ted Pak.
#
#
# argv[1] should be the RAxML_nodeLabelledRootedTree
# argv[2] should be the RAxML_marginalAncestralStates
# argv[3] should be a FASTA file with the aligned genomes for strains (extracted from a Mugsy .maf)

from Bio import Phylo, SeqIO
import sys
import os
import subprocess
import re

########
#
# IMPORTANT: nucmer, delta-filter, and show-snps from MUMmer 3.23 must be on PATH before running this
# On Minerva, this should be as easy as module load mummer/3.23
#
########

def computeDistance(fileA, contig1, contig2):
    count=0
    extractContig(fileA, contig1, "Contig1.fa")
    extractContig(fileA, contig2, "Contig2.fa")
    os.system("nucmer -p "+str(contig1)+"_"+str(contig2)+" Contig1.fa Contig2.fa")
    os.system("delta-filter -lr "+str(contig1)+"_"+str(contig2)+".delta > "+str(contig1)+"_"+str(contig2)+"_df1.delta")
    nucmer_output=subprocess.check_output("show-snps -Clr "+str(contig1)+"_"+str(contig2)+"_df1.delta", shell=True)
    nucmer_snps=nucmer_output.split("\n")
    for snp in nucmer_snps:
        data=re.split("\s+",snp)
        if(len(data)>2):
            if(data[2] in ['A','C','G','T'] and data[3] in ['A','C','G','T'] and  data[2]!="." and data[3]!="."):
                count=count+1
    return count


def extractContig(fileA, contig, outfile):
    fh=open(outfile, 'w')
    for seq_record in SeqIO.parse(fileA, "fasta"):
        if(str(seq_record.id[0:10])==str(contig)):
            seq_id=str(">"+str(contig)+"\n")
            fh.write(seq_id)
            seq1=str(seq_record.seq+"\n")
            fh.write(seq1)


def recomputeBranchLengths(tree):
    for clade in tree.find_clades(order='level'):
        clade_depth = len(tree.get_path(clade))
    
        # Special cases for branches of the root node
        if clade_depth==1 and clade.name:
               print "ROOT_", clade.name
               clade.branch_length = computeDistance(filename2, "ROOT", clade.name)
        if clade_depth==1 and clade.confidence:
               print "ROOT_", clade.confidence
               clade.branch_length = computeDistance(filename2, "ROOT", clade.confidence)

        # For deeper branches
        if clade_depth > 1:
            ancestor = tree.get_path(clade)[clade_depth - 2]
        
            # This named strain branches from another named strain
            if(clade.name and ancestor.name):
                clade.branch_length = computeDistance(filename2, clade.name, ancestor.name) 

            # This marginal ancestral state branches from another marginal ancestral state
            if(clade.confidence and ancestor.confidence):
               clade.branch_length = computeDistance(filename2, clade.confidence, ancestor.confidence)

            # This named strain branches from a numbered marginal ancestral state
            if(clade.name and ancestor.confidence):
                print clade.name, "_", ancestor.confidence
                clade.branch_length = computeDistance(filename2, clade.name, ancestor.confidence)
                
    return tree


if __name__ == "__main__":
    raxml_nlrt_filename = sys.argv[1]
    filename2 = sys.argv[2]
    filename3 = sys.argv[3]
    
    # Open the original tree
    tree = Phylo.read(raxml_nlrt_filename, "newick")
    recomputeBranchLengths(tree)
    
    # Finally, rewrite the new tree with the modified branch_lengths to a new file
    Phylo.write(tree, raxml_nlrt_filename+"_SNP.txt", "newick")