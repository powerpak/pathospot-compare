import sys
import subprocess
import os
import argparse
import shutil
import _mysql
import datetime
import networkx as nx
from itertools import groupby



def get_fasta_list(fasta_name):
    """
    given a fasta file. yield dict of header, sequence
    """
    out_list = []
    with open(fasta_name) as fh:
        faiter = (x[1] for x in groupby(fh, lambda line: line[0] == ">"))
        for header in faiter:
            header = header.next()[1:].strip()
            seq = "".join(s.strip() for s in faiter.next())
            if not header.split('_')[1] in ['g', 'm']:
                out_list.append((header, seq))
    return out_list

def group_snvs(fasta_list, mash, working_dir, max_cluster_size):
    G = nx.Graph()
    subprocess.Popen(mash + ' sketch -o ' + working_dir + '/reference.msh ' + ' '.join(fasta_list), shell=True).wait()
    edge_list = []
    cutoff = 0.75
    for file in fasta_list:
        process = subprocess.Popen(mash + ' dist ' + working_dir + '/reference.msh ' + file, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in process.stdout:
            fasta_a, fasta_b, dist = line.split()[:3]
            if float(dist) <= cutoff:
                G.add_node(fasta_a)
                G.add_node(fasta_b)
                edge_list.append((float(dist), fasta_a, fasta_b))
    edge_list.sort()
    for i in edge_list:
        print i
        G.add_edge(i[1], i[2])
        new_out_groups = []
        subgraphs = nx.connected_component_subgraphs(G)
        for sg in subgraphs:
            group = []
            for node in sg.nodes():
                group.append(node)
            if len(group) > max_cluster_size:
                return out_groups
            new_out_groups.append(group)
        out_groups = new_out_groups
    return out_groups


def get_repeats(infile, working_dir):
    subprocess.Popen('nucmer --maxmatch --nosimplify --prefix ' + working_dir + '/repeats ' + infile + ' ' + infile, stderr=subprocess.PIPE, shell=True).wait()
    subprocess.Popen('show-coords ' + working_dir + '/repeats.delta > ' + working_dir + '/repeats.coords', shell=True).wait()
    with open(working_dir + '/repeats.coords') as f:
        repeat_dict = {}
        get_coords = False
        for line in f:
            if line.startswith('=========='):
                get_coords = True
            elif get_coords:
                s1, e1, bar, s2, e2 = line.split()[:5]
                s1, e1, s2, e2 = map(int, (s1, e1, s2, e2))
                query, subject = line.split()[11:]
                if not query in repeat_dict:
                    repeat_dict[query] = set()
                if not subject in repeat_dict:
                    repeat_dict[subject] = set()
                if (s1 != s2 or e1 != e2) and query == subject:
                    for i in range(s1-1, e1):
                        repeat_dict[query].add(i)
                    for i in range(s2-1, e2):
                        repeat_dict[subject].add(i)
    repeat_count = 0
    for i in repeat_dict:
        repeat_count += len(repeat_dict[i])
    return repeat_dict


def run_parsnp(out_groups, working_dir, parsnp, harvesttools, min_length):
    fastas = []
    filtered = []
    snv_count = {}
    group_stats = []
    for num, i in enumerate(out_groups):
        if len(i) > 1:
            parsnpdir = working_dir + '/group_' + str(num)
            try:
                os.makedirs(parsnpdir)
            except OSError:
                shutil.rmtree(parsnpdir)
                os.makedirs(parsnpdir)
            for j in i:
                contig_list = get_fasta_list(j)
                repeat_dict = get_repeats(j, working_dir)
                new_contig_list = []
                length = 0
                for k in contig_list:
                    new_seq = ''
                    for pos, l in enumerate(k[1]):
                        if k[0] in repeat_dict and pos in repeat_dict[k[0]]:
                            new_seq += 'n'
                        else:
                            new_seq += l
                            length += 1
                    new_contig_list.append((k[0], new_seq))
                contig_list = new_contig_list
                print j, length
                if length >= 2000000:
                    ref_fasta = j
                    with open(parsnpdir + '/' + j.split('/')[-1], 'w') as out_fasta:
                        for k in contig_list:
                            out_fasta.write('>' + k[0] + '\n')
                            for l in range(0, len(k[1]), 60):
                                out_fasta.write(k[1][l:l+60] + '\n')
                else:
                    filtered.append(j)
            vcf_file = working_dir + '/parsnp_' + str(num) + '.vcf'
            subprocess.Popen(parsnp + ' -o ' + working_dir + '/parsnp_' + str(num) + ' -d ' + parsnpdir + ' -r ' + parsnpdir + '/' + ref_fasta.split('/')[-1] + ' -c -x True -P 20000000', shell=True).wait()
            subprocess.Popen(harvesttools + ' -i ' + working_dir + '/parsnp_' + str(num) + '/parsnp.ggr -V ' + vcf_file, shell=True).wait()
            with open(working_dir + '/parsnp_' + str(num) + '/parsnpAligner.log') as log:
                for line in log:
                    if line.startswith('Number of sequences analyzed:'):
                        num_gen = line.split()[4]
                    elif line.startswith('Total coverage among all sequences:'):
                        percent_aligned = line.split()[5]
                    elif line.startswith('Number of clusters created:'):
                        num_clusters = float(line.split()[4])
                    elif line.startswith('Average cluster length:'):
                        ave_cluster_length = float(line.split()[3])
                core_genome_size = num_clusters * ave_cluster_length
                group_stats.append((num_gen, percent_aligned, core_genome_size))
            with open(vcf_file) as vcf:
                getit = False
                for line in vcf:
                    if line.startswith('#CHROM'):
                        seq_list = line.split()[9:]
                        getit = True
                        var_count = [[0 for x in range(len(seq_list))] for y in range(len(seq_list))]
                    elif getit:
                        vars = line.split()[9:]
                        for num1, x in enumerate(vars):
                            for num2, y in enumerate(vars):
                                if vars[num1] != vars[num2]:
                                    var_count[num1][num2] += 1
            for num1, fasta1 in enumerate(seq_list):
                if num1 == 0:
                    fasta1 = fasta1[:-4]
                snv_count[fasta1] = {}
                for num2, fasta2 in enumerate(seq_list):
                    if num2 == 0:
                        fasta2 = fasta2[:-4]
                    snv_count[fasta1][fasta2] = var_count[num1][num2] / core_genome_size * 1000000
        else:
            group_stats.append(None)
        for j in i:
            fastas.append(j.split('/')[-1])
    with open(working_dir + '/snv_counts.tsv', 'w') as o:
        o.write('\t' + '\t'.join(fastas) + '\n')
        for i in fastas:
            o.write(i)
            for j in fastas:
                if i in snv_count and j in snv_count[i]:
                    o.write('\t' + str(snv_count[i][j]))
                else:
                    o.write('\t1000000')
            o.write('\n')
    return filtered, group_stats



def create_json(working_dir, json):
    snv_count = {}
    with open(working_dir + '/snv_counts.tsv') as f:
        fastas = f.readline().rstrip().split('\t')[1:]
        for line in f:
            fasta = line.split('\t')[0]
            snv_count[fasta] = {}
            counts = map(float, line.rstrip().split('\t')[1:])
            for i in range(len(counts)):
                snv_count[fasta][fastas[i]] = counts[i]
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
    detail_dict = {}
    for isolate in fastas:
        try:
            db = _mysql.connect(host=host, user=user, passwd=pw, db=database)
            ass_no = isolate.split('_')[-1].split('.')[0]
            isolate_id = isolate.split('_')[2]
            db.query(
                """select contig_N50, contig_count, contig_maxlength, mlst_subtype from tAssemblies where assembly_ID='""" + ass_no + "'")
            val = db.store_result()
            n50, contigs, max_contig, mlst = val.fetch_row()[0]
            db.query(
                """select collection_unit, eRAP_ID, order_date, procedure_desc from tIsolates where isolate_ID='""" + isolate_id + "'")
            val = db.store_result()
            unit, erap, order_date, procedure = val.fetch_row()[0]
            detail_dict[isolate.split('.')[0]] = (unit, n50, contigs, max_contig, erap, mlst, order_date)
        except:
            detail_dict[isolate.split('.')[0]] = (None, None, None, None, None, None, None)
    with open(json + '.json', 'w') as out:
        out.write('{\n'
                  '    "distance_unit": "parsnp SNVs",\n'
                  '    "generated": "' + str(datetime.datetime.now()) + '",\n'
                                                                        '    "in_query": "parsnp",\n'
                                                                        '    "nodes": [\n')
        for i in fastas:
            name = i.split('.')[0]
            try:
                isolate_id = name.split('_')[2]
                if len(isolate_id) != 7:
                    isolate_id = name.split('_')[0]
                else:
                    assembly_id = name.split('_')[4]
                if len(isolate_id) != 7:
                    isolate_id = 'na'
            except:
                isolate_id = 'na'
                assembly_id = 'na'
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
                      '            "order_date": "' + str(coll_date) + '",\n'
                      '            "procedure_desc": "Culture-blood"\n'
                      '        }')
            if i != fastas[-1]:
                out.write(',\n')
        out.write('],\n'
                  '    "links": [\n')
        for num1, i in enumerate(fastas):
            for num2, j in enumerate(fastas):
                if num1 != num2 and i in snv_count and j in snv_count[i]:
                    out.write('        {\n'
                              '            "source": ' + str(num1) + ',\n'
                              '            "target": ' + str(num2) + ',\n'
                              '            "value": ' + str(snv_count[i][j]) + '\n'
                              '        },\n')
                elif num1 != num2:
                    out.write('        {\n'
                              '            "source": ' + str(num1) + ',\n'
                              '            "target": ' + str(num2) + ',\n'
                              '            "value": 50000\n'
                              '        },\n')
        out.seek(-2, 2)
        out.write('\n    ],\n'
                  '    "out_dir": "saureus.sv_snv"\n'
                  '}')



parser = argparse.ArgumentParser()
parser.add_argument("-f", "--fofn", help='fofn of input fastas')
parser.add_argument("-o", "--output", help="tsv/json of snv distances")
parser.add_argument("-m", "--path_to_mash", default='mash', help="Path to mash binary")
parser.add_argument("-p", "--path_to_parsnp", default='parsnp', help="Path to parsnp binary")
parser.add_argument("-t", "--path_to_harvest", default='harvesttools', help="Path to harvesttools binary")
parser.add_argument("-d", "--working_dir", help="working directory")
parser.add_argument("-x", "--database_only", default=False, action='store_true', help="when given an existing directory calculate mumi can update the snv count with information from pathogendb")
parser.add_argument("-c", "--max_cluster_size", default=100, help="maximum number of genomes to include in a cluster to be run through parsnp")
parser.add_argument("-l", "--min_length", default=2000000, help="minimum length of the genome after repeat filtering for inclusion in a cluster")
args = parser.parse_args()


if not os.path.exists(args.working_dir):
    os.makedirs(args.working_dir)
if args.database_only:
    create_json(args.working_dir, args.output)
else:
    fasta_list = []
    with open(args.fofn) as f:
        for line in f:
            fasta_list.append(line.rstrip())
    out_groups = group_snvs(fasta_list, args.path_to_mash, args.working_dir, args.max_cluster_size)
    filtered, stats = run_parsnp(out_groups, args.working_dir, args.path_to_parsnp, args.path_to_harvest, args.min_length)
    create_json(args.working_dir, args.output)
    for num, i in enumerate(out_groups):
        if len(i) > 1:
            sys.stdout.write('Group ' + str(num) + ': aligned ' + str(stats[num][0]) + ' genomes, core size=' + str(stats[num][2]) + ' (' + str(stats[num][1]) + ')\n')
        else:
            sys.stdout.write(i[0] + ' not aligned.\n')
    for i in filtered:
        sys.stdout.write(i + ' was filtered as it was too short.\n')
