# ======================================================================================
# = These are helper functions for the `rake parsnp` pipeline in pathogendb-comparison =
# ======================================================================================

# Extracts the cluster number from a path in the form of `#{OUT_PREFIX}.(\d+).\w+/...`
# where the digits after OUT_PREFIX are the cluster number
def clust_num_from_path(path)
  abort "FATAL: OUT_PREFIX must be defined" unless OUT_PREFIX
  while path =~ %r{/}
    path = File.dirname(path)
  end
  path.sub(%r{\.\w+$}, "")[(OUT_PREFIX.size + 1)..-1].to_i
end

# Takes a path to a parsnp output, finds the corresponding `parsnpAligner.log`, and returns
# a hash of stats parsed out of log, including core genome size, cluster coverage range, etc.
def parsnp_statistics(path)
  path = File.dirname(path) + "/parsnpAligner.log"
  stats = {}
  coverages = []
  return nil unless File.exist?(path) and File.readable?(path)
  File.foreach(path, "\n") do |line|
    case line.strip
    when /^Cluster coverage in sequence \d+:\s+(\d+(.\d+)?)%$/
      coverages << $1.to_f
    when /^Total coverage among all sequences:\s+(\d+(.\d+)?)%$/
      stats[:core_genome_size] = $1.to_f
    when /^Total running time:\s+(\d+(.\d+)?)s$/
      stats[:walltime] = $1.to_f
    end
  end
  stats[:cluster_coverage_range] = [coverages.min, coverages.max]
  stats
end

# Given a filename for a hypothetical parsnp output and some mash clusters produced by 
# the `rake parsnp` pipeline, produce the single .fasta for this cluster corresponding to 
# the filename, and abort otherwise
def get_single_seq_name(filename, clusters)
  abort "FATAL: Can't write dummy parsnp outputs before clustering" unless clusters
  
  cluster_num = clust_num_from_path(filename)
  fastas = clusters[cluster_num]
  abort "FATAL: Should not write a dummy file for a cluster of size > 1" if fastas.size > 1
  
  seq_name = File.basename(fastas.first)
end

# Writes a dummy parsnp.vcf file for a hypothetical parsnp run on one genome
def write_null_parsnp_vcf(filename, clusters)
  seq_name = get_single_seq_name(filename, clusters)
  File.open(filename, "w") do |f|
    f.write "#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	#{seq_name}\n"
  end
end

# Writes a dummy parsnp.nwk file for a hypothetical parsnp run on one genome
def write_null_parsnp_clean_nwk(filename, clusters)
  seq_name = get_single_seq_name(filename, clusters)
  File.open(filename, "w") do |f|
    f.write "(#{seq_name}:0);\n"
  end
end