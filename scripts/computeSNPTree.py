from Bio import Phylo, SeqIO
import sys
import os
import subprocess
import re

filename1=sys.argv[1]
filename2=sys.argv[2]
def computeDistance(fileA, contig1, contig2):
#    os.system("perl /sc/orga/work/attieo02/extractContig.pl "+fileA+" "+str(contig1)+" > Contig1.fa")
#    os.system("perl /sc/orga/work/attieo02/extractContig.pl "+fileA+" "+str(contig2)+" > Contig2.fa")
#    print "perl /sc/orga/work/attieo02/extractContig.pl "+fileA+" "+str(contig1)+" > Contig1.fa"
    count=0
    extractContig(fileA, contig1, "Contig1.fa")
    extractContig(fileA, contig2, "Contig2.fa")
    os.system("/sc/orga/work/attieo02/MUMmer3.23/nucmer -p "+str(contig1)+"_"+str(contig2)+" Contig1.fa Contig2.fa")
    os.system("/sc/orga/work/attieo02/MUMmer3.23/delta-filter -lr "+str(contig1)+"_"+str(contig2)+".delta > "+str(contig1)+"_"+str(contig2)+"_df1.delta")
    nucmer_output=subprocess.check_output("/sc/orga/work/attieo02/MUMmer3.23/show-snps -Clr "+str(contig1)+"_"+str(contig2)+"_df1.delta", shell=True)
#    print nucmer_output
    nucmer_snps=nucmer_output.split("\n")
#    print nucmer_snps
    for snp in nucmer_snps:
#        print snp
        data=re.split("\s+",snp)
#        print data
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


tree=Phylo.read(filename1, 'newick')
print tree
#for clade in tree.find_clades(order='level'):
#    print clade," ",tree.get_path(clade)
for clade in tree.find_clades(order='level'):
    if(len(tree.get_path(clade))==1 and clade.name):
           print "ROOT_", clade.name
           clade.branch_length=computeDistance(filename2,"ROOT", clade.name)
    if(len(tree.get_path(clade))==1 and clade.confidence):
           print "ROOT_", clade.confidence
           clade.branch_length=computeDistance(filename2,"ROOT", clade.confidence)
    if(len(tree.get_path(clade))>1):
        if(tree.get_path(clade)[len(tree.get_path(clade))-1].name and tree.get_path(clade)[len(tree.get_path(clade))-2].name):
            tree.get_path(clade)[len(tree.get_path(clade))-1].branch_length=computeDistance(filename2, tree.get_path(clade)[len(tree.get_path(clade))-1].name, tree.get_path(clade)[len(tree.get_path(clade))-2].name) 
#            print tree.get_path(clade)[len(tree.get_path(clade))-1].name,"_",tree.get_path(clade)[len(tree.get_path(clade))-2].name
        if(tree.get_path(clade)[len(tree.get_path(clade))-1].confidence and tree.get_path(clade)[len(tree.get_path(clade))-2].confidence):
           tree.get_path(clade)[len(tree.get_path(clade))-1].branch_length=computeDistance(filename2, tree.get_path(clade)[len(tree.get_path(clade))-1].confidence, tree.get_path(clade)[len(tree.get_path(clade))-2].confidence)
#              print tree.get_path(clade)[len(tree.get_path(clade))-1].confidence,"_",tree.get_path(clade)[len(tree.get_path(clade))-2].confidence
        if(tree.get_path(clade)[len(tree.get_path(clade))-1].name and tree.get_path(clade)[len(tree.get_path(clade))-2].confidence):
            print tree.get_path(clade)[len(tree.get_path(clade))-1].name,"_",tree.get_path(clade)[len(tree.get_path(clade))-2].confidence
            tree.get_path(clade)[len(tree.get_path(clade))-1].branch_length=computeDistance(filename2, tree.get_path(clade)[len(tree.get_path(clade))-1].name, tree.get_path(clade)[len(tree.get_path(clade))-2].confidence)
Phylo.write(tree, filename1+"_SNP.txt", "newick")
