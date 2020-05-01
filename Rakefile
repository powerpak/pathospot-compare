require 'rubygems'
require 'bundler/setup'
require 'rake-multifile'
require 'pp'
require 'net/http'
require 'tmpdir'
require_relative 'lib/colors'
require_relative 'lib/lsf_client'
require_relative 'lib/pathogendb_client'
require_relative 'lib/filter_fasta'
require_relative 'lib/heatmap_json'
require_relative 'lib/parsnp_utils'
require 'set'
require 'shellwords'
require 'json'
require 'csv'
require 'tqdm'
include Colors

task :default => :check

LSF = LSFClient.new
LSF.disable! if ENV['LSF_DISABLE']

REPO_DIR = File.dirname(__FILE__)
HARVEST_DIR = "#{REPO_DIR}/vendor/harvest"
MASH_DIR = "#{REPO_DIR}/vendor/mash"

OUT     = File.expand_path(ENV['OUT'] || "#{REPO_DIR}/out")
IN_QUERY = ENV['IN_QUERY']
IN_FOFN = ENV['IN_FOFN'] && File.expand_path(ENV['IN_FOFN'])
if ENV['PATHOGENDB_MYSQL_URI']
  STDERR.puts "Please edit your scripts/env.sh to use PATHOGENDB_URI instead of PATHOGENDB_MYSQL_URI"
  ENV['PATHOGENDB_URI'] = ENV['PATHOGENDB_MYSQL_URI']
end
PATHOGENDB_URI = ENV['PATHOGENDB_URI'] == 'user:pass@host' ? nil : ENV['PATHOGENDB_URI']
PATHOGENDB_ADAPTER = ENV['PATHOGENDB_ADAPTER']
IGB_DIR = ENV['IGB_DIR']

if IN_QUERY
  abort "FATAL: IN_QUERY requires also specifying PATHOGENDB_URI" unless PATHOGENDB_URI
  abort "FATAL: IN_QUERY requires also specifying IGB_DIR" unless IGB_DIR
  pdb = PathogenDBClient.new(PATHOGENDB_URI, adapter: PATHOGENDB_ADAPTER)
  IN_PATHS = pdb.assembly_paths(IGB_DIR, IN_QUERY)
else
  begin
    IN_PATHS = IN_FOFN && File.new(IN_FOFN).readlines.map(&:strip).reject(&:empty?)
  rescue Errno::ENOENT
    abort "FATAL: Could not read the file you specified as IN_FOFN. Check the path and permissions?"
  end
end
if IN_PATHS && IN_PATHS.map{ |p| File.basename p }.uniq.size < IN_PATHS.size
  abort "FATAL: Some of the IN_PATHS do not have unique filenames. Every FASTA file needs a unique name."
end
if IN_PATHS && IN_PATHS.find{ |p| !p.match(%r{\.fa(sta)?$}) }
  abort "FATAL: All paths in IN_PATHS should end in .fa or .fasta"
end
IN_PATHS_PAIRS = IN_PATHS && IN_PATHS.permutation(2)

#######
# Other environment variables that may be set by the user for specific tasks (see README.md)
#######

DISTANCE_THRESHOLD = ENV['DISTANCE_THRESHOLD'] ? ENV['DISTANCE_THRESHOLD'].to_i : 10
OUT_PREFIX = ENV['OUT_PREFIX'] ? ENV['OUT_PREFIX'].gsub(/[^\w-]/, '') : "out"

#######
# Deprecated tasks are in a separate Rakefile and not loaded by default (see README-deprecated-tasks.md)
#######

DEPRECATED_TASKS = ENV['DEPRECATED_TASKS'] || false
if DEPRECATED_TASKS then import "#{REPO_DIR}/deprecated.rake"; end

#############################################################
#  IMPORTANT!
#  This Rakefile runs with the working directory set to OUT
#  All filenames from hereon are relative to that directory
#############################################################

mkdir_p OUT
Dir.chdir(OUT)

task :env do
  STDERR.puts "Output directory: #{OUT}"
  mkdir_p File.join(REPO_DIR, "vendor")

  ENV['TMP'] ||= "/tmp"
  ENV['PERL5LIB'] ||= "/usr/bin/perl5.10.1"
end

file "#{REPO_DIR}/scripts/env.sh" => "#{REPO_DIR}/scripts/example.env.sh" do
  cp "#{REPO_DIR}/scripts/example.env.sh", "#{REPO_DIR}/scripts/env.sh"
end

desc "Checks environment variables and requirements before running tasks"
task :check => [:env, "#{REPO_DIR}/scripts/env.sh", :harvest_install, :mash_install] do
  mkdir_p ENV['TMP'] or abort "FATAL: set TMP to a directory that can store scratch files"
end

# pulls down a precompiled version of Harvest Tools, used by the parsnp task
# see http://harvest.readthedocs.io/en/latest/index.html
task :harvest_install => [:env, HARVEST_DIR, "#{HARVEST_DIR}/parsnp"]
directory HARVEST_DIR 
file "#{HARVEST_DIR}/parsnp" do
  Dir.chdir(File.dirname(HARVEST_DIR)) do
    system <<-SH or abort
      curl -L -o Harvest-Linux64-v1.1.2.tar.gz 'https://github.com/marbl/harvest/releases/download/v1.1.2/Harvest-Linux64-v1.1.2.tar.gz'
      tar xvzf Harvest-Linux64-v1.1.2.tar.gz
      mv Harvest-Linux64-v1.1.2/* #{HARVEST_DIR.shellescape} && \
          rm -rf "#{REPO_DIR}/vendor/Harvest-Linux64-v1.1.2" "#{REPO_DIR}/vendor/Harvest-Linux64-v1.1.2.tar.gz"
    SH
  end
end

# pulls down a precompiled version of mash (fast genome/metagenome distance estimator), used by the parsnp task
# see https://mash.readthedocs.io/en/latest/
task :mash_install => [:env, MASH_DIR, "#{MASH_DIR}/mash"]
directory MASH_DIR
file "#{MASH_DIR}/mash" do
  Dir.chdir(File.dirname(MASH_DIR)) do
    system <<-SH or abort
      curl -L -o mash-Linux64-v2.1.tar 'https://github.com/marbl/Mash/releases/download/v2.1/mash-Linux64-v2.1.tar'
      tar xvf mash-Linux64-v2.1.tar
      mv mash-Linux64-v2.1/* #{MASH_DIR.shellescape} && \
          rm -rf mash-Linux64-v2.1.tar mash-Linux64-v2.1
    SH
  end
end


# ==========
# = parsnp =
# ==========

# The steps used to build a .parsnp.heatmap.json file are:
#  0. filter bad contigs out of the fastas into #{OUT_PREFIX}.contig_filter/*.filt.(fa|fasta), 
#     just as in the mummer SNV pathway
#  1. filter tandem repeats out of the genomes with mummer, as in calculate_snvs.py, and put 
#     the filtered fastas into a "#{OUT_PREFIX}.repeat_mask" directory as 
#     .repeat_mask.(fa|fasta) files
#  2. cluster them, roughly, by MASH or MUMi distance, and symlink them into
#     #{OUT_PREFIX}.0.clust, #{OUT_PREFIX}.1.clust, etc. directories
#  3. run parsnp on each cluster, outputting into #{OUT_PREFIX}.0.parsnp, #{OUT_PREFIX}.1.parsnp etc. 
#     directories
#  4. in each of the #{OUT_PREFIX}.*.parsnp directories, extract the .vcf and .nwk from the .ggr, and 
#     clean the sequence names in the .nwk producing a .clean.nwk tree file
#  5. in each of the #{OUT_PREFIX}.*.parsnp directories, create a parsnp.tsv file of SNV distances from 
#     the .vcf
#  6. create a "#{OUT_PREFIX}.#{Date.today.strftime('%Y-%m-%d')}.parsnp.vcfs.npz" that combines all of the
#     VCFs into quickly-indexable NumPy arrays, along with allele info and reference genome contig sizes
#  7. create a "#{OUT_PREFIX}.#{Date.today.strftime('%Y-%m-%d')}.parsnp.heatmap.json" that
#     recombines all the TSVs of distances into one big matrix (uncalculated distances are marked as nil
#     or infinitely large), and also includes the .clean.nwk trees

PARSNP_HEATMAP_JSON_FILE = "#{OUT_PREFIX}.#{Date.today.strftime('%Y-%m-%d')}.parsnp.heatmap.json"
PARSNP_CLUSTERS_TSV = "#{OUT_PREFIX}.repeat_mask.msh.clusters.tsv"
PARSNP_VCFS_NPZ_FILE = "#{OUT_PREFIX}.#{Date.today.strftime('%Y-%m-%d')}.parsnp.vcfs.npz"

desc "uses Parsnp to create *.xmfa, *.ggr, and *.tree files plus a SNV distance matrix"
task :parsnp => [:check, :parsnp_check, PARSNP_CLUSTERS_TSV, PARSNP_VCFS_NPZ_FILE, 
    PARSNP_HEATMAP_JSON_FILE]

task :parsnp_check do
  abort "FATAL: Task parsnp requires specifying IN_QUERY" unless IN_QUERY
  abort "FATAL: Task parsnp requires specifying OUT_PREFIX" unless OUT_PREFIX
  abort "FATAL: Task parsnp requires specifying PATHOGENDB_URI" unless PATHOGENDB_URI
end

def repeat_masked_prereqs(masked_path)
  name = File.basename(masked_path).sub(%r{\.repeat_mask\.(fa|fasta)$}, '.filt.\\1')
  "#{OUT_PREFIX}.contig_filter/#{name}"
end
rule %r{^#{OUT_PREFIX}.repeat_mask/.+\.(fa|fasta)$} => proc{ |n| repeat_masked_prereqs(n) } do |t|
  mkdir_p "#{OUT_PREFIX}.repeat_mask"
  fasta_mask_repeats(t.source, t.name)
end

REPEAT_MASKED_FILES = (IN_PATHS || []).map do |path|
  "#{OUT_PREFIX}.repeat_mask/" + File.basename(path).sub(%r{\.(fa|fasta)$}, '.repeat_mask.\\1')
end

file "#{OUT_PREFIX}.repeat_mask.msh" => REPEAT_MASKED_FILES do |t|
  fasta_files = REPEAT_MASKED_FILES.map(&:strip).map(&:shellescape).join(' ')
  system <<-SH or abort
    #{MASH_DIR}/mash sketch -o #{t.name.shellescape} #{fasta_files}
  SH
end

MASH_CUTOFF = ENV['MASH_CUTOFF']
MASH_CLUSTER_NOT_GREEDY = ENV['MASH_CLUSTER_NOT_GREEDY']
MAX_CLUSTER_SIZE = ENV['MAX_CLUSTER_SIZE']

file PARSNP_CLUSTERS_TSV => "#{OUT_PREFIX}.repeat_mask.msh" do |t|
  system <<-SH or abort
    python #{REPO_DIR}/scripts/mash_clusters.py \
        --path_to_mash #{MASH_DIR}/mash \
        #{MASH_CLUSTER_NOT_GREEDY && "--not_greedy"} \
        #{MASH_CUTOFF && "--max_cluster_diameter " + MASH_CUTOFF} \
        #{MAX_CLUSTER_SIZE &&  "--max_cluster_size " + MAX_CLUSTER_SIZE} \
        --output #{t.name.shellescape} \
        --output_diameters #{OUT_PREFIX}.repeat_mask.msh.cluster_diameters.txt \
        #{t.source.shellescape}
  SH
  
  # If we rebuild the clusters, we enhance all the upstream tasks with the new prereqs based on the
  # new clusters. Then, we re-invoke the final file task to ensure the new prereqs get built.
  abort "FATAL: Could not rebuild mash clusters" unless read_parsnp_clusters
  Rake::Task[PARSNP_VCFS_NPZ_FILE].enhance(parsnp_vcfs_npz_prereqs)
  Rake::Task[PARSNP_HEATMAP_JSON_FILE].enhance(parsnp_heatmap_json_prereqs)
  Rake::Task[:parsnp].enhance do
    STDERR.puts "WARN: re-invoking parsnp task since the mash clusters were rebuilt"
    Rake::Task[PARSNP_VCFS_NPZ_FILE].reenable
    Rake::Task[PARSNP_VCFS_NPZ_FILE].invoke
    Rake::Task[PARSNP_HEATMAP_JSON_FILE].reenable
    Rake::Task[PARSNP_HEATMAP_JSON_FILE].invoke
  end
end

def read_parsnp_clusters
  return nil if Rake::Task[PARSNP_CLUSTERS_TSV].needed?
  CSV.read(PARSNP_CLUSTERS_TSV, col_sep: "\t")
end

def clustered_fasta_prereqs(n)
  n.sub(%r{^#{OUT_PREFIX}\.\d+\.clust/}, "#{OUT_PREFIX}.repeat_mask/")
end
rule %r{^#{OUT_PREFIX}\.\d+\.clust/.+\.(fa|fasta)$} => proc{ |n| clustered_fasta_prereqs(n) } do |t|
  mkdir_p File.dirname(t.name)
  # We touch the source because if this link is being created for the first time, any old downstream
  # products should be rebuilt. Symlinks always show the same mtime as their source.
  touch t.source
  ln_s "../#{t.source}", t.name
end

def parsnp_ggr_to_parsnp_inputs(name)
  clust_dir = File.dirname(name).sub(%r{\.parsnp$}, ".clust")
  clust_num = clust_num_from_path(name)
  clusters = read_parsnp_clusters
  abort "FATAL: Tried to calculate prereqs for parsnp before clustering" unless clusters
  clusters[clust_num].map do |n|
    n.sub(%r{^#{OUT_PREFIX}.repeat_mask/}, clust_dir + "/")
  end
end

rule %r{/parsnp\.ggr$} => proc{ |n| parsnp_ggr_to_parsnp_inputs(n) } do |t|
  mkdir_p File.dirname(t.name)
  
  # Special case: If there is only one genome in the cluster, create an empty .ggr file
  next touch(t.name) if t.sources.size == 1
  
  # What reference should be used for this parsnp run? It can be set globally (with GBK or REF),
  # which will only work if there is one mash cluster; otherwise, the oldest fasta in this mash
  # cluster (by `order_date`) will be used as the reference genome
  if ENV['GBK']
    referenceOrGenbank = "-g #{ENV['GBK'].shellescape}"
  elsif ENV['REF']
    referenceOrGenbank = "-r #{ENV['REF'].shellescape}"
  else
    if ENV['PATHOGENDB_ADAPTER']
      referenceOrGenbank = "-r ! "
    else
      referenceOrGenbank = "-r " + get_first_order_date_fasta(t.sources, pdb).shellescape
    end
  end
  
  unless t.sources.map{ |f| File.dirname(f) }.uniq.size == 1
    abort "FATAL: parsnp inputs cannot be in different subdirectories"
  end
  input_dir = File.dirname(t.sources.first)
  if (Dir.glob("#{input_dir}/*") - t.sources).size > 0
    STDERR.puts "WARN: Deleting extraneous files/symlinks in #{input_dir} before running parsnp"
    rm (Dir.glob("#{input_dir}/*") - t.sources)
  end
  
  # Run parsnp on the `clust_dir` from above
  # See here for a parsnp FAQ: https://harvest.readthedocs.io/en/latest/content/parsnp/faq.html
  #   -c => curated genome directory: use *all* genomes in dir, ignore MUMi distances
  system <<-SH or abort
    #{HARVEST_DIR}/parsnp #{referenceOrGenbank} \
        -c \
        -o #{File.dirname(t.name).shellescape} \
        -d #{input_dir.shellescape}
  SH
end

rule %r{/parsnp\.vcf$} => proc{ |n| n.sub(%r{\.vcf$}, ".ggr") } do |t|
  # If the parsnp.ggr file is empty => this is a one-genome cluster => write a barebones .vcf
  next write_null_parsnp_vcf(t.name, read_parsnp_clusters) if File.size(t.source) == 0
  system <<-SH or abort
    #{HARVEST_DIR}/harvesttools -i #{t.source.shellescape} -V parsnp.complete.vcf
    awk -F '\t' '$7=="PASS" || $1~/^#/' parsnp.complete.vcf > #{t.name.shellescape}
  SH
end

# The .nwk tree is different from the .tree in that it uses distances scaled to SNVs/Mbp
# See harvesttools option " -u 0/1 (update the branch values to reflect genome length)"
rule %r{/parsnp\.clean\.nwk$} => proc{ |n| n.sub(%r{\.clean\.nwk$}, ".ggr") } do |t|
  # If the parsnp.ggr file is empty => this is a one-genome cluster => write a barebones .nwk
  next write_null_parsnp_clean_nwk(t.name, read_parsnp_clusters) if File.size(t.source) == 0
  nwk = t.name.sub(%r{\.clean\.nwk$}, ".nwk")
  unless File.exist?(nwk)
    system "#{HARVEST_DIR}/harvesttools -i #{t.source.shellescape} -N #{nwk.shellescape}" or abort
  end
  system <<-SH or abort
    python #{REPO_DIR}/scripts/cleanup_parsnp_newick.py \
      #{nwk.shellescape} \
      #{t.name.shellescape} \
      #{pdb.clean_genome_name_regex && pdb.clean_genome_name_regex.shellescape}
  SH
end

def parsnp_tsv_to_parsnp_outputs(name)
  [name.sub(%r{\.tsv$}, ".vcf"), name.sub(%r{\.tsv$}, ".clean.nwk")]
end
rule %r{/parsnp\.tsv$} => proc{ |n| parsnp_tsv_to_parsnp_outputs(n) } do |t|
  # Converts a parsnp VCF file into a tab-separated values table of SNV distances
  system <<-SH or abort
    python #{REPO_DIR}/scripts/parsnp2table.py \
      #{t.sources.first.shellescape} \
      #{t.name.shellescape} \
      #{pdb.clean_genome_name_regex && pdb.clean_genome_name_regex.shellescape}
  SH
end

def parsnp_vcfs_npz_prereqs
  prereqs = [PARSNP_CLUSTERS_TSV]
  clusters = read_parsnp_clusters || []
  (0...clusters.size).map { |i| prereqs << "#{OUT_PREFIX}.#{i}.parsnp/parsnp.vcf" }
  prereqs
end
file PARSNP_VCFS_NPZ_FILE => parsnp_vcfs_npz_prereqs do |t|
  input_parsnp_vcfs = t.sources.select{ |src| src =~ %r{/parsnp\.vcf$} }
  if input_parsnp_vcfs.size == 0
    STDERR.puts "WARN: can't build .parsnp.vcfs.npz with prereqs from before clustering; will re-invoke"
    next
  end

  Dir.mktmpdir do |tmp|
    open("#{tmp}/in_paths.txt", "w") { |f| f.write(IN_PATHS.join("\n")) }
    clean_name_regex = pdb.clean_genome_name_regex && pdb.clean_genome_name_regex.shellescape
    sequin_annots = pdb.genome_annotation_format == ".features_table.txt"
    transl_table = pdb.genetic_code_table && pdb.genetic_code_table.to_s.shellescape
    # NOTE: Because of NumPy <-> python 2.7.x bugs, this script uniquely requires python 2.7.14 !!!
    system <<-SH or abort
      python #{REPO_DIR}/scripts/parsnp_vcfs_to_npz.py \
          #{input_parsnp_vcfs.map(&:shellescape).join(' ')} \
          --fastas #{tmp}/in_paths.txt \
          #{clean_name_regex ? "--clean_genome_names " + clean_name_regex : ""} \
          #{sequin_annots ? "--sequin_annotations" : ""} \
          #{transl_table ? "--transl_table " + transl_table : ""} \
          --output #{t.name.shellescape}
    SH
  end
end

def parsnp_heatmap_json_prereqs
  prereqs = [PARSNP_CLUSTERS_TSV]
  clusters = read_parsnp_clusters || []
  (0...clusters.size).map do |i| 
    prereqs += ["#{OUT_PREFIX}.#{i}.parsnp/parsnp.tsv", "#{OUT_PREFIX}.#{i}.parsnp/parsnp.clean.nwk"]
  end
  prereqs
end
file PARSNP_HEATMAP_JSON_FILE => parsnp_heatmap_json_prereqs do |t|
  input_parsnp_tsvs = t.sources.select{ |src| src =~ %r{/parsnp\.tsv$} }
  snv_tsvs = {}
  which_tsv = {}
  tsv_keys = {}
  
  if input_parsnp_tsvs.size == 0
    STDERR.puts "WARN: can't build .parsnp.heatmap.json with prereqs from before preclustering; will re-invoke"
    next
  end
  input_parsnp_tsvs.each do |tsv|
    tsv_data = snv_tsvs[tsv] = CSV.read(tsv, col_sep: "\t")
    seqs = tsv_data.first.drop(1)
    seqs.each{ |seq| which_tsv[seq] = tsv }
    tsv_keys[tsv] = Hash[seqs.zip(1..tsv_data.size)]
  end

  opts = {in_query: IN_QUERY, distance_unit: "parsnp SNPs", distance_threshold: DISTANCE_THRESHOLD,
          adapter: PATHOGENDB_ADAPTER, trees: [], parsnp_stats: []}
  json = heatmap_json(IN_PATHS, PATHOGENDB_URI, opts) do |json, node_hash|
    (node_hash.keys - which_tsv.keys).each do |name|
      STDERR.puts "WARN: Assembly #{name} isn't in any of the parsnp alignments; skipping"
    end
    node_hash.each do |source_name, source|
      node_hash.each do |target_name, target|
        next unless source[:metadata] && target[:metadata]
        next unless which_tsv[source_name] && which_tsv[target_name]
        next unless which_tsv[source_name] == which_tsv[target_name]
        tsv = which_tsv[source_name]
        tsv_key = tsv_keys[tsv]
        snp_distance = snv_tsvs[tsv][tsv_key[source_name]][tsv_key[target_name]].to_i
        json[:links][source[:id]][target[:id]] = snp_distance
      end
    end
    t.sources.select{ |src| src =~ %r{/parsnp\.clean\.nwk$} }.each do |nwk| 
      json[:trees] << File.read(nwk).strip
      json[:parsnp_stats] << parsnp_statistics(nwk)
    end
  end

  File.open(t.name, "w") { |f| JSON.dump(json, f) }
end


# ==============
# = encounters =
# ==============

ENCOUNTERS_TSV_FILE = "#{OUT_PREFIX}.#{Date.today.strftime('%Y-%m-%d')}.encounters.tsv"
desc "Download encounters data for the dendro-timeline part of pathogendb-viz"
task :encounters => [:check, ENCOUNTERS_TSV_FILE]

file ENCOUNTERS_TSV_FILE do |t|
  abort "FATAL: Task encounters requires specifying IN_QUERY" unless IN_QUERY
  
  encounters = pdb.encounters(IN_QUERY)
  
  CSV.open(ENCOUNTERS_TSV_FILE, "wb", col_sep: "\t") do |tsv|
    tsv << encounters.columns.map(&:to_s)
    encounters.each do |row|
      tsv << pdb.stringify_times(row.values)
    end
  end
end


# =======
# = epi =
# =======

HEATMAP_EPI_JSON_FILE = "#{OUT_PREFIX}.#{Date.today.strftime('%Y-%m-%d')}.epi.heatmap.json"
desc "Download isolate spatiotemporal data for pathogendb-viz"
task :epi => [:check, HEATMAP_EPI_JSON_FILE]

file HEATMAP_EPI_JSON_FILE do |task|
  abort "FATAL: Task epi requires specifying IN_QUERY" unless IN_QUERY
  abort "FATAL: Task epi requires specifying OUT_PREFIX" unless OUT_PREFIX
  abort "FATAL: Task epi requires specifying PATHOGENDB_URI" unless PATHOGENDB_URI 
  
  ISOLATES_COLS = [:order_date, :hospital_abbreviation, :collection_unit]
  isolate_test_results = pdb.isolate_test_results(IN_QUERY)
  json = {
    generated: DateTime.now.to_s,
    in_query: IN_QUERY, 
    isolates: [ISOLATES_COLS.map{ |col| col.to_s }],
    isolate_test_results: [isolate_test_results.columns]
  }
  pdb.isolates(IN_QUERY).each do |row|
    json[:isolates] << pdb.stringify_times(row.values_at(*ISOLATES_COLS))
  end
  isolate_test_results.each do |row|
    json[:isolate_test_results] << pdb.stringify_times(row.values)
  end
 
  File.open(task.name, "w") { |f| JSON.dump(json, f) }
end
