import sys
import datetime
import os
import _mysql

# parsnp2table.py
# USE: creates a .tsv and .json of SNV differences between strains from a vcf file produced by parsnp
# USAGE: python parsnp2table.py parsnp.vcf output_prefix

with open(sys.argv[1]) as vcf:
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
with open(sys.argv[2] + '.tsv', 'w') as out:
    out.write('strains\t' + '\t'.join(seq_list) + '\n')
    for num1, i in enumerate(seq_list):
        out.write(i)
        for num2 in range(len(seq_list)):
            out.write('\t' + str(var_count[num1][num2]))
        out.write('\n')
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
