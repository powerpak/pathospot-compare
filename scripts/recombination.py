from operator import mul
from fractions import Fraction
import sys
import re
import string
'''N choose K function, for binomial distribution'''
def nCk(n,k):
    return int(reduce(mul, (Fraction(n-i,i+1) for i in range(k)),1))
'''Binomial Distribution for Recombination test, b is the size of the block,
d is the density of SNPs, and N is the observed number of SNPs'''
def bin_cdf(b,d,N):
    sum=0
    for i in range(0,N-1):
        sum+=float(nCk(b,i)*(d**i)*(1-d)**(b-i))
    return float(1-sum)
vcf_file=sys.argv[1]
snp_list=[]
bin={}
#Read lines from VCF file and put the positions of the SNPs into an array
fh=open(vcf_file, 'r')
for line in fh.readlines():
    if(not(re.match(r"^\#", line))):
        data_list=line.rstrip().split("\t")
#        print data_list
        snp_list.append(int(data_list[1]))
#Bin the SNP positions for each 1000 bp block.
for i in range(0,2940):
    bin[i]=0
    for j in range(0, len(snp_list)):
        if(snp_list[j]<=1000*(i+1) and snp_list[j]>=1000*i):
            bin[i]+=1
#Recombination if this is larger than the binomial statistic
print 0.05/2940
for i in range(0,2940):
    #binomial statistic for each bin
    print str(i)+":"+str(bin_cdf(1000,20/1000,bin[i]))
