import sys


with open(sys.argv[1],'r') as vcf:
	with open(sys.argv[2], 'w') as out:
    		getit = False
    		for line in vcf:
        		if line.startswith('#CHROM'):
            			seq_list = line.split()[9:]
           			getit = True
            			var_count = [[0 for i in range(len(seq_list))] for i in range(len(seq_list))]
        		elif getit:
            			vars = line.split()[9:]
            			for num1, i in enumerate(vars):
                			for num2, j in enumerate(vars):
                    				if vars[num1] != vars[num2]:
                        				var_count[num1][num2] += 1
    		out.write('strains\t' + '\t'.join(seq_list) + '\n')
    		for num1, i in enumerate(seq_list):
       			out.write(i)
        		for num2 in range(len(seq_list)):
            			out.write('\t' + str(var_count[num1][num2]))
        		out.write('\n')
