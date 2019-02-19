#!/usr/bin/env python
"""
Clusters the sequences in a Mash sketch file until the clusters reach a given diameter (in Mash distance units) or size.

Outputs clusters as sequence names separated by tabs, with each cluster separated by newlines.
"""

import sys
import os
import subprocess
import argparse
import pickle
from itertools import permutations, chain
from tqdm import tqdm


DEFAULT_MAX_DIAMETER = 0.02
DEFAULT_MAX_CLUSTER_SIZE = 100
SUBPROCESS_KWARGS = {"shell": False, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE}


def get_fasta_list(mash_sketch_file, path_to_mash='mash'):
    process = subprocess.Popen([path_to_mash, 'info', '-t', mash_sketch_file], **SUBPROCESS_KWARGS)
    fasta_list = []
    for line in process.stdout:
        fields = line.split("\t")
        if line[0] == '#' or len(fields) < 3: continue
        fasta_list.append(fields[2])
    return fasta_list


def find_node_in_clusters(node, clusters):
    try:
        return next(i for i, cluster in enumerate(clusters) if node in cluster)
    except StopIteration: 
        return None
        

def diameter(cluster, distances, merging_into=None, diameter_cache=None):
    # Use list() to copy and avoid ever modifying the original cluster
    cluster = list(cluster)
    have_cache = isinstance(diameter_cache, dict)
    cached = None
    
    if have_cache: cached = diameter_cache.get(tuple(sorted(cluster)), None)
        
    if merging_into is not None:
        if cached is not None and len(merging_into) == 1:
            # As an optimization, when considering adding ONE node to an existing cluster,
            # only the distances between the new node and all previous nodes in the cluster
            # plus the cluster's current diameter need to be compared
            new_distances = [distances[merging_into[0], node] for node in cluster]
            new_diameter = max(new_distances + [cached])
            cluster.extend(merging_into)
            diameter_cache[tuple(sorted(cluster))] = new_diameter
            return new_diameter
        else:
            cluster.extend(merging_into)
            if have_cache: cached = diameter_cache.get(tuple(sorted(cluster)), None)
    
    if cached is not None: return cached
    if len(cluster) < 2: return 0
    
    new_diameter = max([distances[(pair[0], pair[1])] for pair in permutations(cluster, 2)])
    if have_cache: diameter_cache[tuple(sorted(cluster))] = new_diameter
    return new_diameter


def mash_distances_edges(mash_sketch_file, fasta_list, max_diameter=DEFAULT_MAX_DIAMETER, 
        path_to_mash='mash', allow_caching=True):
    """Calculates sketched Mash distances between all fastas in `fasta_list`.
    
    Returns a hash of all distances indexed by (from, to) tuples, and a list of the edges
    that are below `max_diameter`, consisting of (from, to, dist) tuples and sorted from 
    shortest to longest."""
    edges = []
    distances = {}
    cached_path = mash_sketch_file + ".distances_edges"
    
    if (os.access(cached_path, os.R_OK) and os.access(mash_sketch_file, os.R_OK) and
            os.path.getmtime(cached_path) > os.path.getmtime(mash_sketch_file) and allow_caching):
        sys.stderr.write("Loading cached Mash distances & edges from %s\n" % cached_path)
        with open(cached_path, 'rb') as f:
            return pickle.load(f)

    for fasta in tqdm(fasta_list, desc="Calculating Mash distance matrix"):
        if not os.path.isfile(fasta) or not os.access(fasta, os.R_OK):
            raise RuntimeError("File {} doesn't exist or isn't readable".format(fasta))
        process = subprocess.Popen([path_to_mash, 'dist', mash_sketch_file, fasta], 
                **SUBPROCESS_KWARGS)
        for line in process.stdout:
            fasta_a, fasta_b, dist = line.split()[:3]
            if fasta_a == fasta_b: continue
            dist = float(dist)
            distances[(fasta_a, fasta_b)] = dist
            edges.append((fasta_a, fasta_b, dist))
                
    edges.sort(key=lambda edge: edge[2])
    
    if allow_caching:
        with open(cached_path, 'wb') as f:
            pickle.dump((distances, edges), f)
            
    return distances, edges


def mash_clusters(mash_sketch_file, fasta_list, distances, edges, max_diameter=DEFAULT_MAX_DIAMETER, 
        greedy=True, max_cluster_size=DEFAULT_MAX_CLUSTER_SIZE, path_to_mash='mash'):
    
    nodes = set(fasta_list)
    clusters = []
    cache = {}
    
    # Starting from the smallest length edges, start merging nodes into clusters
    for edge in tqdm(edges, desc="Constructing clusters"):
        first_already_in = find_node_in_clusters(edge[0], clusters)
        second_already_in = find_node_in_clusters(edge[1], clusters)
        if first_already_in is not None:
            if second_already_in is not None:
                if first_already_in == second_already_in: continue
                new_clust_size = len(clusters[first_already_in]) + len(clusters[second_already_in])
                new_diameter = diameter(clusters[first_already_in], distances, 
                        clusters[second_already_in], cache)
                if new_clust_size > max_cluster_size or new_diameter > max_diameter: 
                    if greedy: continue
                    else: break
                clusters[first_already_in].extend(clusters[second_already_in])
                del clusters[second_already_in]
            else:
                if (len(clusters[first_already_in]) >= max_cluster_size or diameter(
                        clusters[first_already_in], distances, [edge[1]], cache) > max_diameter):
                    if greedy: continue
                    else: break
                clusters[first_already_in].append(edge[1])
        elif second_already_in is not None:
            if (len(clusters[second_already_in]) >= max_cluster_size or diameter(
                    clusters[second_already_in], distances, [edge[0]], cache) > max_diameter):
                if greedy: continue
                else: break
            clusters[second_already_in].append(edge[0])
        else:
            if edge[2] > max_diameter: continue
            clusters.append([edge[0], edge[1]])

    # Reverse-sort clusters by size, then append the unclustered nodes as single-node clusters
    clusters.sort(key=lambda cluster: len(cluster), reverse=True)
    flattened = list(chain.from_iterable(clusters))
    unclustered = nodes - set(flattened)
    clusters.extend([[node] for node in unclustered])
    return clusters


def write_clusters(clusters, filename=None):
    f = open(filename, "w") if filename else sys.stdout
    for cluster in clusters:
        f.write("\t".join(cluster) + "\n")
    f.close()


def write_cluster_diameters(clusters, distances, filename=None):
    f = open(filename, "w") if filename else sys.stderr
    for cluster in clusters:
        f.write(str(diameter(cluster, distances)) + "\n")
    f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mash_sketch_file', metavar='MSH_SKETCH_FILE', type=str, nargs='?', 
            help='Path to the .msh file (created with `mash sketch`).')
    parser.add_argument("-o", "--output", default=None, 
            help="Output clusters to this file if set, otherwise will use STDOUT.")
    parser.add_argument("-d", "--output_diameters", default=None,
            help="Outputs cluster diameters to this file if set, otherwise will be discarded.")
    parser.add_argument("-p", "--path_to_mash", default='mash',
            help="Path to the mash executable")
    parser.add_argument("-G", "--not_greedy", dest='greedy', default=True, action='store_false', 
            help="Don't add to smaller clusters after one cluster reaches the size/diameter limit")
    parser.add_argument("-C", "--no_edges_cache", dest='edges_cache', default=True, action='store_false', 
            help="Don't cache or reuse any Mash distances & edges, saved in a .distances_edges file")
    parser.add_argument("-m", "--max_cluster_diameter", type=float, default=DEFAULT_MAX_DIAMETER, 
            help="Maximum diameter of a cluster in Mash units. For no limit, set to 0. " + 
                 ("Default is: %f" % DEFAULT_MAX_DIAMETER))
    parser.add_argument("-s", "--max_cluster_size", type=int, default=DEFAULT_MAX_CLUSTER_SIZE, 
            help="Maximum number of genomes to include in a cluster. For no limit, set to 0. " +
                 ("Default is: %d" % DEFAULT_MAX_CLUSTER_SIZE))
    args = parser.parse_args()
    
    if args.mash_sketch_file is None:
        parser.print_help(file=sys.stderr)
        sys.exit(1)
    
    if not os.access(args.path_to_mash, os.X_OK):
        parser.error("Unable to find Mash. Please check the --path_to_mash argument.")
    
    if args.max_cluster_diameter == 0: args.max_cluster_diameter = float("inf")
    if args.max_cluster_size == 0: args.max_cluster_size = float("inf")
    
    fasta_list = get_fasta_list(args.mash_sketch_file, path_to_mash=args.path_to_mash)
    
    distances, edges = mash_distances_edges(args.mash_sketch_file, fasta_list, 
            max_diameter=args.max_cluster_diameter, path_to_mash=args.path_to_mash, 
            allow_caching=args.edges_cache)
    
    clusters = mash_clusters(args.mash_sketch_file, fasta_list, distances, edges, 
            max_diameter=args.max_cluster_diameter, max_cluster_size=args.max_cluster_size, 
            path_to_mash=args.path_to_mash, greedy=args.greedy)
    
    write_clusters(clusters, args.output)
    
    if args.output_diameters is not None:
        write_cluster_diameters(clusters, distances, args.output_diameters)
