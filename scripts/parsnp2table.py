import sys
import datetime
import os
import _mysql

# parsnp2table.py
# USE: creates a .tsv and .json of SNV differences between strains from a VCF file produced by parsnp
# USAGE: python parsnp2table.py parsnp.vcf output_prefix

# Note, as per https://harvest.readthedocs.io/en/latest/content/parsnp/quickstart.html
# "harvest-tools VCF outputs indels in non standard format.
#  Currently column based, not row based.
#  Excluding indel rows (default behavior) converts file into valid VCF format.
#  this will be updated in future version"

# Read in the VCF file
with open(sys.argv[1]) as vcf:
    getit = False
    for line in vcf:
        # Skip all lines until we get to the #CHROM line
        # The first 9 columns are standard VCF columns with allele info
        if line.startswith('#CHROM'):
            # Get the remaining column headers, which are the names of the input sequences
            seq_list = line.split()[9:]
            # Start reading rows
            getit = True
            # Create an empty NxN distance matrix for all N sequences
            var_count = [[0 for i in range(len(seq_list))] for i in range(len(seq_list))]
        elif getit:
            # Each cell is an allele for a particular sequence
            vars = line.split()[9:]
            # For every possible pair of sequences, if an allele was called differently, increment
            # the SNV distance in the matrix by one
            for num1, i in enumerate(vars):
                for num2, j in enumerate(vars):
                    if vars[num1] != vars[num2]:
                        var_count[num1][num2] += 1

# Open the output TSV file and dump the distance 
with open(sys.argv[2] + '.tsv', 'w') as out:
    out.write('strains\t' + '\t'.join(seq_list) + '\n')
    for num1, i in enumerate(seq_list):
        out.write(i)
        for num2 in range(len(seq_list)):
            out.write('\t' + str(var_count[num1][num2]))
        out.write('\n')

# The JSON file requires connecting to the PathogenDB MySQL database
# Connection details are currently pulled from the user's .my.cnf file
# TODO: should instead pull from the PATHOGENDB_MYSQL_URI environment variable
path = os.path.expanduser('~') + '/.my.cnf'
with open(path) as cnf_file:
    for line in cnf_file:
        if line.startswith('user='):
            user = line.rstrip()[5:]
        if line.startswith('password='):
            pw = line.rstrip()[9:]
        if line.startswith('host='):
            host = line.rstrip()[5:]
        if line.startswith('database='):
            database = line.rstrip()[9:]
db = _mysql.connect(host=host, user=user, passwd=pw, db=database)

rejected = []
out_list = []

# Pull metadata for all the isolates in the VCF file from PathogenDB
detail_dict = {}
for isolate in seq_list:
    try:
        ass_no = isolate.split('_')[-1].split('.')[0]
        isolate_id = isolate.split('_')[2]
        db.query("""select contig_N50, contig_count, contig_maxlength, mlst_subtype from tAssemblies where assembly_ID='""" + ass_no + "'")
        val = db.store_result()
        n50, contigs, max_contig, mlst = val.fetch_row()[0]
        db.query("""select collection_unit, eRAP_ID, order_date, procedure_desc from tIsolates where isolate_ID='""" + isolate_id + "'")
        val = db.store_result()
        unit, erap, order_date, procedure = val.fetch_row()[0]
        detail_dict[isolate.split('.')[0]] = (unit, n50, contigs, max_contig, erap, mlst, order_date)
    except IndexError:
        detail_dict[isolate.split('.')[0]] = (None, None, None, None, None, None, None)

# Spit out the JSON file in the pathogendb-viz heatmap format
with open(sys.argv[2] + '.json', 'w') as out:
    out.write('{\n'
    '    "distance_unit": "parsnp SNVs",\n'
    '    "generated": "' + str(datetime.datetime.now()) + '",\n'
    '    "in_query": "parsnp",\n'
    '    "nodes": [\n')
    for i in seq_list:
        name = i.split('.')[0]
        isolate_id = name.split('_')[2]
        assembly_id = name.split('_')[4]
        unit, n50, contigs, max_contig, erap, mlst, coll_date = detail_dict[name]
        out.write('        {\n'
        '            "assembly_ID": "' + str(assembly_id) + '",\n'
        '            "collection_unit": "' + str(unit) + '",\n'
        '            "contig_N50": ' + str(n50) + ',\n'
        '            "contig_count": ' + str(contigs) + ',\n'
        '            "contig_maxlength": ' + str(max_contig) + ',\n'
        '            "eRAP_ID": "' + str(erap) + '",\n'
        '            "isolate_ID": "' + str(isolate_id) + '",\n'
        '            "mlst_subtype": "' + str(mlst) + '",\n'
        '            "name": "' + str(name) + '",\n'
        '            "order_date": "' + str(coll_date) +'",\n'
        '            "procedure_desc": "Culture-blood"\n'
        '        }')
        if i != seq_list[-1]:
            out.write(',\n')

    out.write('],\n'
        '    "links": [\n')
    for num1, i in enumerate(seq_list):
        for num2 in range(len(seq_list)):
            if num1 != num2:
                out.write('        {\n'
                '            "source": ' + str(num1) + ',\n'
                '            "target": ' + str(num2) + ',\n'
                '            "value": ' + str(var_count[num1][num2]) + '\n'
                '        }')
                if not (num1 == len(seq_list) - 1 and num2 == len(seq_list) - 2):
                    out.write(',\n')
    out.write('    ],\n'
              '    "out_dir": "saureus.sv_snv"\n'
              '}')
