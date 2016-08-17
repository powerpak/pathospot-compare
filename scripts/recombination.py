from operator import mul
from fractions import Fraction
import sys
import re
import string
'''n choose k, the binomial coefficient (n,k).'''
def nCk(n,k):
    return int(reduce(mul, (Fraction(n-i,i+1) for i in range(k)),1))
'''test using the binomial distribution. b is the size of the block, d is the average number of SNPs, N is the number of SNPs observed in the block.'''
def bin_cdf(b,d,N):
    sum=0
#Use Croucher's formula for the binary test of recombination
    for i in range(0,N-1):
        sum+=float(nCk(b,i)*(d**i)*(1-d)**(b-i))
    return float(1-sum)
vcf_file=sys.argv[1]
snp_list=[]
bin={}
fh=open(vcf_file, 'r')
for line in fh.readlines():
    if(not(re.match(r"^\#", line))):
        data_list=line.rstrip().split("\t")
#        print data_list
        snp_list.append(int(data_list[1]))
for i in range(0,2940):
#initialize the bins for the SNPs.
    bin[i]=0
    for j in range(0, len(snp_list)):
#if a SNP is in the ith block, increment the ith bin by 1
        if(snp_list[j]<=1000*(i+1) and snp_list[j]>=1000*i):
            bin[i]+=1

print 0.05/294
for i in range(0,294):
    print str(i)+":"+str(bin_cdf(1000,20/1000,bin[i]))
