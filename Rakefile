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
MUGSY_DIR = "#{REPO_DIR}/vendor/mugsy"
CLUSTALW_DIR = "#{REPO_DIR}/vendor/clustalw"
RAXML_DIR = "#{REPO_DIR}/vendor/raxml"
MAUVE_DIR = "#{REPO_DIR}/vendor/mauve"
GRIMM_DIR = "#{REPO_DIR}/vendor/grimm"
GBLOCKS_DIR = "#{REPO_DIR}/vendor/gblocks"
HARVEST_DIR = "#{REPO_DIR}/vendor/harvest"
MASH_DIR = "#{REPO_DIR}/vendor/mash"

OUT     = File.expand_path(ENV['OUT'] || "#{REPO_DIR}/out")
IN_QUERY = ENV['IN_QUERY']
IN_FOFN = ENV['IN_FOFN'] && File.expand_path(ENV['IN_FOFN'])
BED_LINES_LIMIT = ENV['BED_LINES_LIMIT'] ? ENV['BED_LINES_LIMIT'].to_i : 1000
PATHOGENDB_MYSQL_URI = ENV['PATHOGENDB_MYSQL_URI']
PATHOGENDB_MYSQL_URI = nil if PATHOGENDB_MYSQL_URI =~ /user:pass@host/ # ignore the example value
PATHOGENDB_ADAPTER = ENV['PATHOGENDB_ADAPTER']
IGB_DIR = ENV['IGB_DIR']

if IN_QUERY
  abort "FATAL: IN_QUERY requires also specifying PATHOGENDB_MYSQL_URI" unless PATHOGENDB_MYSQL_URI
  abort "FATAL: IN_QUERY requires also specifying IGB_DIR" unless IGB_DIR
  pdb = PathogenDBClient.new(PATHOGENDB_MYSQL_URI, adapter: PATHOGENDB_ADAPTER)
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

OUT_PREFIX = ENV['OUT_PREFIX'] ? ENV['OUT_PREFIX'].gsub(/[^\w-]/, '') : "out"

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
  
  sc_orga_scratch = "/sc/orga/scratch/#{ENV['USER']}"
  ENV['TMP'] ||= Dir.exists?(sc_orga_scratch) ? sc_orga_scratch : "/tmp"
  ENV['PERL5LIB'] ||= "/usr/bin/perl5.10.1"
end

file "#{REPO_DIR}/scripts/env.sh" => "#{REPO_DIR}/scripts/example.env.sh" do
  cp "#{REPO_DIR}/scripts/example.env.sh", "#{REPO_DIR}/scripts/env.sh"
end

ENV_ERROR = "Configure this in scripts/env.sh and run `source scripts/env.sh` before running rake."

desc "Checks environment variables and requirements before running tasks"
task :check => [:env, "#{REPO_DIR}/scripts/env.sh", :mugsy_install, :clustalw, :raxml, 
    :mauve_install, :grimm, :gblocks, :harvest_install, :mash_install] do
  mkdir_p ENV['TMP'] or abort "FATAL: set TMP to a directory that can store scratch files"
end

# pulls down a precompiled static binary for mugsy v1 r2.2, which is used by the mugsy task
# see http://mugsy.sourceforge.net/
task :mugsy_install => [:env, MUGSY_DIR, "#{MUGSY_DIR}/mugsy"]
directory MUGSY_DIR
file "#{MUGSY_DIR}/mugsy" do
  Dir.chdir(File.dirname(MUGSY_DIR)) do
    system <<-SH or abort
      curl -L -o mugsy.tar.gz 'http://sourceforge.net/projects/mugsy/files/mugsy_x86-64-v1r2.2.tgz/download'
      tar xvzf mugsy.tar.gz
      mv mugsy_x86-64-v1r2.2/* '#{MUGSY_DIR}' && \
          rm -rf mugsy_x86-64-v1r2.2 mugsy.tar.gz
    SH
  end
end

# pulls down a precompiled static binary for ClustalW2.1, which is used by the mugsy task
# see http://www.clustal.org/
task :clustalw => [:env, CLUSTALW_DIR, "#{CLUSTALW_DIR}/clustalw2"]
directory CLUSTALW_DIR
file "#{CLUSTALW_DIR}/clustalw2" do
  Dir.chdir(File.dirname(CLUSTALW_DIR)) do
    system <<-SH or abort
      curl -L -o clustalw.tar.gz 'http://www.clustal.org/download/current/clustalw-2.1-linux-x86_64-libcppstatic.tar.gz'
      tar xvzf clustalw.tar.gz
      mv clustalw-2.1-linux-x86_64-libcppstatic/* #{CLUSTALW_DIR.shellescape} && \
          rm -rf clustalw-2.1-linux-x86_64-libcppstatic clustalw.tar.gz
    SH
  end
end

# pulls down and compiles RAxML 8.0.2, which is used by the mugsy task
# see http://sco.h-its.org/exelixis/web/software/raxml/index.html
task :raxml => [:env, RAXML_DIR, "#{RAXML_DIR}/raxmlHPC"]
directory RAXML_DIR
file "#{RAXML_DIR}/raxmlHPC" do
  Dir.chdir(File.dirname(CLUSTALW_DIR)) do
    system <<-SH or abort
      curl -L -o raxml.tar.gz 'https://github.com/stamatak/standard-RAxML/archive/v8.0.2.tar.gz'
      tar xvzf raxml.tar.gz && \
          rm raxml.tar.gz
    SH
  end
  Dir.chdir("#{File.dirname(CLUSTALW_DIR)}/standard-RAxML-8.0.2") do
    (system "make -f Makefile.gcc" and cp("raxmlHPC", "#{RAXML_DIR}/raxmlHPC")) or abort
  end
  rm_rf "#{File.dirname(CLUSTALW_DIR)}/standard-RAxML-8.0.2"
end

# pulls down precompiled static binaries and JAR files for Mauve 2.3.1, which is used by the mauve task
# see http://asap.genetics.wisc.edu/software/mauve/
task :mauve_install => [:env, MAUVE_DIR, "#{MAUVE_DIR}/linux-x64/progressiveMauve"]
directory MAUVE_DIR
file "#{MAUVE_DIR}/linux-x64/progressiveMauve" do
  Dir.chdir(File.dirname(MAUVE_DIR)) do
    system <<-SH or abort
      curl -L -o mauve.tar.gz 'http://darlinglab.org/mauve/downloads/mauve_linux_2.4.0.tar.gz'
      tar xvzf mauve.tar.gz
      mv mauve_2.4.0/* #{MAUVE_DIR.shellescape} && \
          rm -rf mauve.tar.gz mauve_linux_2.4.0.tar.gz
    SH
  end
end

# pulls down and compiles grimm, which is used by the sv_snv track to calculate rearrangement distance
task :grimm => [:env, GRIMM_DIR, "#{GRIMM_DIR}/grimm"]
directory GRIMM_DIR
file "#{GRIMM_DIR}/grimm" do
  Dir.chdir(File.dirname(GRIMM_DIR)) do
    system <<-SH or abort
      curl -L -o grimm.tar.gz 'http://grimm.ucsd.edu/DIST/GRIMM-2.01.tar.gz'
      tar xvzf grimm.tar.gz
      mv GRIMM-2.01/* #{GRIMM_DIR.shellescape} && \
          rm -rf GRIMM-2.01 grimm.tar.gz && \
          sed -i.bak 's/-march=pentiumpro//g' #{GRIMM_DIR.shellescape}/Makefile
    SH
  end
  Dir.chdir(GRIMM_DIR){ system "make" or abort }
end

# pulls down and compiles Gblocks, which is used by the mugsy task
task :gblocks => [:env, GBLOCKS_DIR, "#{GBLOCKS_DIR}/Gblocks"]
directory GBLOCKS_DIR
file "#{GBLOCKS_DIR}/Gblocks" do
  Dir.chdir(File.dirname(GBLOCKS_DIR)) do
    system <<-SH or abort
      curl -L -o gblocks.tar.gz 'http://molevol.cmima.csic.es/castresana/Gblocks/Gblocks_Linux64_0.91b.tar.Z'
      tar xvzf gblocks.tar.gz
      mv Gblocks_0.91b/* #{GBLOCKS_DIR.shellescape} && \
          rm -rf gblocks.tar.gz Gblocks_0.91b
    SH
  end
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


file "pathogendb-comparison.png" => [:graph]
desc "Generates a graph of tasks, intermediate files and their dependencies from this Rakefile"
task :graph do
  # The unflatten step helps with layout; see http://www.graphviz.org/pdf/unflatten.1.pdf
  system <<-SH
    module load graphviz
    OUT_PREFIX=OUT_PREFIX rake -f #{Shellwords.escape(__FILE__)} -P \
        | #{REPO_DIR}/scripts/rake-prereqs-dot.rb --prune #{REPO_DIR} --replace-with REPO_DIR \
        | unflatten -f -l5 -c 3 \
        | dot -Tpng -o pathogendb-comparison.png
  SH
end


# =========
# = mugsy =
# =========

desc "Produces a phylogenetic tree using Mugsy, ClustalW, and RAxML"
task :mugsy => [:check, "RAxML_bestTree.#{OUT_PREFIX}", "RAxML_marginalAncestralStates.#{OUT_PREFIX}_mas","#{OUT_PREFIX}_snp_tree.newick"]

file "#{OUT_PREFIX}.fa" do |t|
  # First, performs whole genome alignment with Mugsy, producing a .maf file that we convert to .fa
  abort "FATAL: Task mugsy requires specifying IN_FOFN" unless IN_PATHS
  abort "FATAL: Task mugsy requires specifying OUT_PREFIX" unless OUT_PREFIX
  abort "FATAL: Task mugsy requires specifying OUTGROUP" unless ENV['OUTGROUP']
  
  mkdir_p "#{OUT}/log"
  
  paths = IN_PATHS.map{ |f| f.strip.shellescape }.join(' ')
  
  LSF.set_out_err("log/mugsy.log", "log/mugsy.err.log")
  LSF.job_name "#{OUT_PREFIX}.fa"
  LSF.bsub_interactive <<-SH
    export MUGSY_INSTALL=#{MUGSY_DIR} &&
    #{MUGSY_DIR}/mugsy -p #{OUT_PREFIX} --directory #{OUT} #{paths} &&
    python #{REPO_DIR}/scripts/maf2fasta.py #{OUT_PREFIX}.maf #{OUT_PREFIX}.fa `sort '#{IN_FOFN}' | uniq | wc -l`
  SH
end

file "#{OUT_PREFIX}_1.fa" => "#{OUT_PREFIX}.fa" do |t|
  abort "FATAL: Task mugsy requires specifying OUT_PREFIX" unless OUT_PREFIX
  
  system <<-SH
    # Replace all hyphens (non-matches) with 'N' in sequence lines in this FASTA file
    # Also replace the first period in sequence IDs with a stretch of 10 spaces
    # This squelches the subsequent contig IDs or accession numbers when converting to PHYLIP
    sed '/^[^>]/s/\-/N/g' #{OUT_PREFIX}.fa | sed '/^>/s/\\./          /' > #{OUT_PREFIX}_1.fa
    perl  #{REPO_DIR}/scripts/coreGenomeSize.pl -f #{OUT_PREFIX}.maf -n `sort '#{IN_FOFN}' | uniq | wc -l` > #{OUT_PREFIX}_Lengths.txt
    sh #{REPO_DIR}/scripts/make_html.sh #{OUT_PREFIX}
  SH
end

file "#{OUT_PREFIX}_1.fa-gb.phy" => "#{OUT_PREFIX}_1.fa" do |t|
  abort "FATAL: Task mugsy requires specifying OUT_PREFIX" unless OUT_PREFIX
  
  mkdir_p "#{OUT}/log"
  LSF.set_out_err("log/mugsy_phy.log", "log/mugsy_phy.err.log")
  LSF.job_name "#{OUT_PREFIX}_1.fa-gb.phy"
  LSF.bsub_interactive <<-SH
  #{GBLOCKS_DIR}/Gblocks #{OUT_PREFIX}_1.fa -t=d -b5=a -b4=1000
  mv #{OUT_PREFIX}_1.fa-gb #{OUT_PREFIX}_1.fa-gb.fasta
    # Convert the FASTA file to a PHYLIP multi-sequence alignment file with ClustalW
    #{CLUSTALW_DIR}/clustalw2 -convert -infile=#{OUT_PREFIX}_1.fa-gb.fasta -output=phylip
  SH
end

file "RAxML_bestTree.#{OUT_PREFIX}" => "#{OUT_PREFIX}_1.fa-gb.phy" do |t|
  abort "FATAL: Task mugsy requires specifying OUT_PREFIX" unless OUT_PREFIX
  outgroup = ENV['OUTGROUP']
  abort "FATAL: Task mugsy requires specifying OUTGROUP" unless outgroup
  
  mkdir_p "#{OUT}/log"
  LSF.set_out_err("log/mugsy_raxml.log", "log/mugsy_raxml.err.log")
  LSF.job_name "#{OUT_PREFIX}_raxml"
  LSF.bsub_interactive <<-SH
    # Use RAxML to create a maximum likelihood phylogenetic tree
    # 1) Bootstrapping step that creates a tree to base marginal ancestral state analysis upon
    #{RAXML_DIR}/raxmlHPC -s #{OUT_PREFIX}_1.fa-gb.phy -#20 -m GTRGAMMA -n #{OUT_PREFIX} -p 12345 \
        -o #{outgroup.slice(0,10)}
  SH
end

file "RAxML_marginalAncestralStates.#{OUT_PREFIX}_mas" => "RAxML_bestTree.#{OUT_PREFIX}" do |t|
  abort "FATAL: Task mugsy requires specifying OUT_PREFIX" unless OUT_PREFIX
  
  mkdir_p "#{OUT}/log"
  LSF.set_out_err("log/mugsy_raxml_mas.log", "log/mugsy_raxml_mas.err.log")
  LSF.job_name "#{OUT_PREFIX}_raxml_mas"
  LSF.bsub_interactive <<-SH
    # 2) Full analysis
    #{RAXML_DIR}/raxmlHPC -f A -s #{OUT_PREFIX}_1.fa-gb.phy -m GTRGAMMA -p 12345 \
        -t RAxML_bestTree.#{OUT_PREFIX} -n #{OUT_PREFIX}_mas
    #{RAXML_DIR}/raxmlHPC -m GTRGAMMA -p 12345 -b 12345 -# 100 -s #{OUT_PREFIX}_1.fa-gb.phy -n T14
    #{RAXML_DIR}/raxmlHPC -m GTRCAT -p 12345 -f b -t RAxML_bestTree.#{OUT_PREFIX}  -z RAxML_bootstrap.T14 -n T15
  SH
end

file "RAxML_nodeLabelledRootedTree.#{OUT_PREFIX}_mas" => "RAxML_marginalAncestralStates.#{OUT_PREFIX}_mas"

file "#{OUT_PREFIX}_snp_tree.newick" => ["RAxML_marginalAncestralStates.#{OUT_PREFIX}_mas",
    "RAxML_nodeLabelledRootedTree.#{OUT_PREFIX}_mas", "#{OUT_PREFIX}_1.fa-gb.fasta"] do |t|
  abort "FATAL: Task mugsy requires specifying OUT_PREFIX" unless OUT_PREFIX
  mas_file = "RAxML_marginalAncestralStates.#{OUT_PREFIX}_mas"
  nlr_tree = "RAxML_nodeLabelledRootedTree.#{OUT_PREFIX}_mas"
  
  system <<-SH
    # Convert RAxML's marginalAncestralStates file into a FASTA file
    sed 's/^\\([[:alnum:]]\\+\\) \\+/>\\1\\n/g' "#{mas_file}" \
        | sed 's/?/N/g' \
        > "#{mas_file}.fa"
  SH
  mkdir_p "#{OUT}/log"
  LSF.set_out_err("log/mugsy_snp_tree.log", "log/mugsy_snp_tree.err.log")
  LSF.job_name "#{OUT_PREFIX}_snp_tree"
  LSF.bsub_interactive <<-SH
    module load python/2.7.6
    module load py_packages/2.7
    module load mummer/3.23
    #{REPO_DIR}/scripts/computeSNPTree.py "#{nlr_tree}" "#{mas_file}.fa" "#{OUT_PREFIX}_1.fa-gb.fasta" \
        > "#{OUT_PREFIX}_snp_tree.newick"
    sed 's/ROOT\:1.00000//' "#{OUT_PREFIX}_snp_tree.newick" > "#{OUT_PREFIX}_snp_tree.newick1"
    xvfb-run python #{REPO_DIR}/scripts/buildTree.py "RAxML_bestTree.#{OUT_PREFIX}" "#{OUT_PREFIX}_snp_tree.newick1" "#{OUT_PREFIX}_ete_tree.pdf"
    xvfb-run python #{REPO_DIR}/scripts/buildTree.py "RAxML_bestTree.#{OUT_PREFIX}" "#{OUT_PREFIX}_snp_tree.newick1" "#{OUT_PREFIX}_ete_tree.png"

  SH
end


# system <<-SH
#   #Chuck mugsy.err.log for errors, if found, abort
#   grep "User defined signal 2" "#{OUT}/log/mugsy.err.log" > "#{OUT}/log/mugsy_error.txt"
#   grep "No alignments found containing all genomes." "#{OUT}/log/mugsy.err.log" > "#{OUT}/log/mugsy_error.txt"
#   grep "Invalid input file." "#{OUT}/log/mugsy.err.log" > "#{OUT}/log/mugsy_error.txt"
# SH


file "#{OUT}/log/mugsy_error.txt" do
    abort "FATAL: Task mugsy fail, see mugsy_error.txt" if File.zero?("#{OUT}/log/mugsy_error.txt")
end 

# ==============
# = mugsy_plot =
# ==============

desc "Produces plots of the phylogenetic trees created by `rake mugsy`"
task :mugsy_plot => [:check, "RAxML_bestTree.#{OUT_PREFIX}.pdf", "#{OUT_PREFIX}_snp_tree.newick.pdf"]

file "RAxML_bestTree.#{OUT_PREFIX}.pdf" => "RAxML_bestTree.#{OUT_PREFIX}" do |t|
  abort "FATAL: Task mugsy_plot requires specifying OUT_PREFIX" unless OUT_PREFIX
  
  tree_file = "RAxML_bestTree.#{OUT_PREFIX}".shellescape
  system <<-SH
    module load R/3.1.0
    R --no-save -f #{REPO_DIR}/scripts/plot_phylogram.R --args #{tree_file}
  SH
end

file "#{OUT_PREFIX}_snp_tree.newick.pdf" => "#{OUT_PREFIX}_snp_tree.newick" do |t|
  abort "FATAL: Task mugsy_plot requires specifying OUT_PREFIX" unless OUT_PREFIX
  
  tree_file = "#{OUT_PREFIX}_snp_tree.newick".shellescape
  system <<-SH
    module load R/3.1.0
    R --no-save -f #{REPO_DIR}/scripts/plot_phylogram.R --args #{tree_file}
  SH
end

# =========
# = mauve =
# =========

desc "Produces a Mauve alignment"
task :mauve => [:check, "#{OUT_PREFIX}.xmfa", "#{OUT_PREFIX}.xmfa.backbone", "#{OUT_PREFIX}.xmfa.bbcols"]
file "#{OUT_PREFIX}.xmfa.backbone" => "#{OUT_PREFIX}.xmfa"
file "#{OUT_PREFIX}.xmfa.bbcols" => "#{OUT_PREFIX}.xmfa"
file "#{OUT_PREFIX}.xmfa" do |t|
  abort "FATAL: Task mauve requires specifying IN_FOFN" unless IN_PATHS
  abort "FATAL: Task mauve requires specifying OUT_PREFIX" unless OUT_PREFIX
  seed_weight = ENV['SEED_WEIGHT']
  abort "FATAL: Task mauve requires specifying SEED_WEIGHT" unless seed_weight
  lcb_weight = ENV['LCB_WEIGHT']
  abort "FATAL: Task mauve requires specifying LCB_WEIGHT" unless lcb_weight
  
  tree_directory = OUT
  mkdir_p "#{OUT}/log"
  
  paths = IN_PATHS.map{ |f| f.strip.shellescape }.join(' ')
  
  LSF.set_out_err("log/mauve.log", "log/mauve.err.log")
  LSF.job_name "#{OUT_PREFIX}.xmfa"
  LSF.bsub_interactive <<-SH
    #{MAUVE_DIR}/linux-x64/progressiveMauve --output=#{OUT_PREFIX}.xmfa --seed-weight=#{seed_weight} \
         --weight=#{lcb_weight} #{paths}
  SH
end


# ==========
# = sv_snv =
# ==========

desc "Pairwise analysis of structural variants between genomes"
task :sv => [:check, :sv_check, :sv_snv_dirs, :sv_files]

desc "Pairwise analysis of single nucleotide changes between genomes"
task :snv => [:check, :snv_check, :sv_snv_dirs, :snv_files]

desc "Pairwise analysis of both structural + single nucleotide changes between genomes"
task :sv_snv => [:check, :sv_snv_check, :sv_snv_dirs, :sv_snv_files]

task :sv_check      do sv_snv_check('sv');      end
task :snv_check     do sv_snv_check('snv');     end
task :sv_snv_check  do sv_snv_check('sv_snv');  end
task :sv_snv_dirs => ["#{OUT_PREFIX}.sv_snv", "#{OUT_PREFIX}.contig_filter"]
  
def sv_snv_check(task_name='sv_snv')
  task_name = task_name.to_s
  abort "FATAL: Task #{task_name} requires specifying IN_FOFN" unless IN_PATHS
  if ['sv', 'sv_snv'].include? task_name
    abort "FATAL: Task #{task_name} requires specifying SEED_WEIGHT" unless ENV['SEED_WEIGHT']
    abort "FATAL: Task #{task_name} requires specifying LCB_WEIGHT" unless ENV['LCB_WEIGHT']
  end

  genome_names = IN_PATHS.map{ |path| File.basename(path).sub(/\.\w+$/, '') }
  unless genome_names.uniq.size == genome_names.size
    abort "FATAL: Task #{task_name} requires that all IN_FOFN filenames (with the extension removed) are unique"
  end
end

SV_FILES = []
SNV_FILES = []
SV_SNV_FILES = []
# Setup, as dependencies for this task, all permutations of IN_FOFN genome names
directory "#{OUT_PREFIX}.sv_snv"
directory "#{OUT_PREFIX}.contig_filter"

IN_PATHS && IN_PATHS.map{ |path| File.basename(path).sub(/\.\w+$/, '') }.each do |genome_name|
  directory "#{OUT_PREFIX}.sv_snv/#{genome_name}"
  Rake::Task[:sv_snv_dirs].enhance ["#{OUT_PREFIX}.sv_snv/#{genome_name}"]
end
IN_PATHS_PAIRS && IN_PATHS_PAIRS.each do |pair|
  genome_names = pair.map{ |path| File.basename(path).sub(/\.\w+$/, '') }
  SV_FILES << "#{OUT_PREFIX}.sv_snv/#{genome_names[0]}/#{genome_names.join '_'}.sv.bed"
  SNV_FILES << "#{OUT_PREFIX}.sv_snv/#{genome_names[0]}/#{genome_names.join '_'}.snv.bed"
  SV_SNV_FILES << "#{OUT_PREFIX}.sv_snv/#{genome_names[0]}/#{genome_names.join '_'}.sv_snv.bed"
end

multitask :sv_files => SV_FILES
multitask :snv_files => SNV_FILES
multitask :sv_snv_files => SV_SNV_FILES

def genomes_from_task_name(task_name)
  genomes = [{:name => task_name.sub("#{OUT_PREFIX}.sv_snv/", '').split(/\//).first}]
  genomes << {:name => task_name.sub("#{OUT_PREFIX}.sv_snv/#{genomes[0][:name]}/#{genomes[0][:name]}_", '').split(/\./).first}
  genomes.each do |g|
    g[:out_dir] = File.dirname(task_name)
    g[:path] = IN_PATHS.find{ |path| path =~ /#{g[:name]}\.\w+$/ }
    filename = File.basename(g[:path])
    g[:filt_path] = "#{OUT_PREFIX}.contig_filter/#{filename.sub(%r{\.(fa|fasta)$}, '.filt.\\1')}"
  end
  genomes
end

def filtered_to_unfiltered(filtered_path)
  name = File.basename(filtered_path).sub(%r{\.filt\.(fa|fasta)$}, '.\\1')
  IN_PATHS.find{ |path| path =~ /#{name}$/ }
end

###
# Creating .sv.bed files from pairwise Mauve alignments
###

# Mauve backbones show large-scale, structural variants between two genomes
rule '.xmfa.backbone' do |task|
  genomes = genomes_from_task_name(task.name)
  output = task.name.sub(/\.backbone$/, '')
  
  LSF.set_out_err("log/sv_snv.log", "log/sv_snv.err.log")
  LSF.job_name File.basename(output)
  
  # TODO: progressiveMauve segfaults (signal 11) all the time. Seems to do it more often within bsub environment.
  # have to figure out why? Isn't fatal, because it doesn't create the .backbone file if it fails like this, and so can simply re-run rake
  system <<-SH
    #{MAUVE_DIR}/linux-x64/progressiveMauve --output=#{output} --seed-weight=#{ENV['SEED_WEIGHT']} \
         --weight=#{ENV['LCB_WEIGHT']} #{genomes[0][:path].shellescape} #{genomes[1][:path].shellescape}
  SH
end

# We create BED files that can visually depict these structural variants
rule %r{\.sv\.bed$} => proc{ |n| n.sub(%r{\.sv\.bed$}, '.xmfa.backbone') } do |task|
  genomes = genomes_from_task_name(task.name)
  backbone_file = task.name.sub(/\.sv\.bed$/, '.xmfa.backbone')
  grimm_file = task.name.sub(/\.sv\.bed$/, '.grimm')
  
  system <<-SH or abort
    #{REPO_DIR}/scripts/backbone-to-grimm.rb #{backbone_file.shellescape} \
        --ref #{genomes[0][:path].shellescape} \
        --query #{genomes[1][:path].shellescape} \
        --grimm #{GRIMM_DIR}/grimm \
        --bed #{task.name.shellescape} \
        #{grimm_file.shellescape}
  SH
end


###
# Creating .snv.bed files from pairwise MUMmer (nucmer) alignments
###

# This rule creates a filtered FASTA file from the original that drops any contigs flagged as "merged" or "garbage"
rule %r{\.filt\.(fa|fasta)$} => proc{ |n| filtered_to_unfiltered(n) } do |task|
  mkdir_p File.dirname(task.name)
  filter_fasta_by_entry_id(task.source, task.name, /_[mg]_/, :invert => true)
end

rule '.delta' => proc{ |n| genomes_from_task_name(n).map{ |g| [g[:filt_path], g[:out_dir]] }.flatten.uniq } do |task|
  genomes = genomes_from_task_name(task.name)
  output = task.name.sub(/\.delta$/, '')
  
  system <<-SH
    module load mummer/3.23
    nucmer -p #{output} #{genomes[0][:filt_path].shellescape} #{genomes[1][:filt_path].shellescape}
  SH
end

rule '.filtered-delta' => '.delta' do |task|  
  system <<-SH
    module load mummer/3.23
    delta-filter -r -q #{task.source.shellescape} > #{task.name.shellescape}
  SH
end

rule %r{(\.snv\.bed|\.snps\.count)$} => proc{ |n| n.sub(%r{(\.snv\.bed|\.snps\.count)$}, '.filtered-delta') } do |task|
  snps_file = task.name.sub(/(\.snv\.bed|\.snps\.count)$/, '.snps')
  # necessary because the .snps.count can also trigger this task
  bed_file = task.name.sub(/(\.snv\.bed|\.snps\.count)$/, '.snv.bed')
  
  system <<-SH or abort
    module load mummer/3.23
    show-snps -IHTClr #{task.source.shellescape} > #{snps_file.shellescape}
  SH
  
  File.open("#{snps_file}.count", "w") { |f| f.write(`wc -l #{snps_file.shellescape}`.strip.split(' ')[0]) }
  
  system <<-SH
    #{REPO_DIR}/scripts/mummer-snps-to-bed.rb #{snps_file.shellescape} \
      --limit #{BED_LINES_LIMIT} \
      #{bed_file.shellescape}
  SH
  
  verbose(false) { rm snps_file }  # because these are typically huge, and redundant w/ the BED files
end

###
# The summary BED track (for :sv_snv) is just a concatenation of both the .sv.bed and .snv.bed tracks
###
rule %r{\.sv_snv\.bed$} => proc{ |n| [n.sub(%r{\.sv_snv\.bed$}, '.snv.bed'), 
    n.sub(%r{\.sv_snv\.bed$}, '.sv.bed')] } do |task|
  system <<-SH or abort
    cat #{task.sources[0].shellescape} #{task.sources[1].shellescape} > #{task.name.shellescape}
  SH
end


# ===========
# = heatmap =
# ===========

HEATMAP_SNV_JSON_FILE = "#{OUT_PREFIX}.#{Date.today.strftime('%Y-%m-%d')}.snv.heatmap.json"
desc "Generate assembly distances for heatmap in pathogendb-viz"
task :heatmap => [:check, HEATMAP_SNV_JSON_FILE]
SNV_COUNT_FILES = SNV_FILES.map{ |path| path.sub(%r{\.snv\.bed$}, '.snps.count') }

multifile HEATMAP_SNV_JSON_FILE => SNV_COUNT_FILES do |task|
  abort "FATAL: Task heatmap requires specifying IN_FOFN or IN_QUERY" unless IN_PATHS
  abort "FATAL: Task heatmap requires specifying OUT_PREFIX" unless OUT_PREFIX
  abort "FATAL: Task heatmap requires specifying PATHOGENDB_MYSQL_URI" unless PATHOGENDB_MYSQL_URI 
  
  opts = {out_dir: "#{OUT_PREFIX}.sv_snv", in_query: IN_QUERY, adapter: PATHOGENDB_ADAPTER}
  json = heatmap_json(IN_PATHS, PATHOGENDB_MYSQL_URI, opts) do |json, node_hash|
    SNV_COUNT_FILES.tqdm.each do |count_file|
      snp_distance = File.read(count_file).strip.to_i
      genomes = genomes_from_task_name(count_file)
      source = node_hash[genomes[0][:name]]
      target = node_hash[genomes[1][:name]]
      next unless source[:metadata] && target[:metadata]
      json[:links][source[:id]][target[:id]] = snp_distance
    end
  end
 
  File.open(task.name, "w") { |f| JSON.dump(json, f) }
end


# ============
# = heatmap3 =
# ============

HEATMAP3_SNV_JSON_FILE = "#{OUT_PREFIX}.#{Date.today.strftime('%Y-%m-%d')}.snv.heatmap3.json"
desc "Generate assembly distances for heatmap in pathogendb-viz (mode 3)"
task :heatmap3 => [:check, HEATMAP_SNV_JSON_FILE]

file HEATMAP3_SNV_JSON_FILE do |task| #=> SNV_COUNT_FILES do |task| #FIXME
  abort "FATAL: Task heatmap requires specifying OUT_PREFIX" unless OUT_PREFIX
  mkdir_p "#{OUT}/heatmap_wd"
  paths = IN_PATHS.map{ |f| f.strip.shellescape }.join(' ')
  system <<-SH or abort
    module load python/2.7.6
    module load py_packages/2.7
    module load mummer/3.23
    python #{REPO_DIR}/scripts/calculate_snvs.py --path_to_mash #{MASH_DIR}/mash --path_to_parsnp #{HARVEST_DIR}/parsnp --path_to_harvest #{HARVEST_DIR}/harvesttools --working_dir #{OUT}/heatmap_wd --output #{HEATMAP_SNV_JSON_FILE} #{paths}
  SH
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
task :parsnp => [:check, PARSNP_CLUSTERS_TSV, PARSNP_VCFS_NPZ_FILE, PARSNP_HEATMAP_JSON_FILE]

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
    module load python/2.7.6
    module load py_packages/2.7
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
  
  referenceOrGenbank = ENV['REF'] ? "-r #{ENV['REF'].shellescape}" : "-r !"
  referenceOrGenbank = "-g #{ENV['GBK'].shellescape}" if ENV['GBK']
  
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
  system "#{HARVEST_DIR}/harvesttools -i #{t.source.shellescape} -V #{t.name.shellescape}" or abort
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
    module load python/2.7.6
    module load py_packages/2.7
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
    module load python/2.7.6
    module load py_packages/2.7
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
    # NOTE: Because of NumPy <-> python 2.7.x bugs, this script uniquely requires python 2.7.14 !!!
    system <<-SH or abort
      module load python/2.7.14
      module load py_packages/2.7
      python #{REPO_DIR}/scripts/parsnp_vcfs_to_npz.py \
          #{input_parsnp_vcfs.map(&:shellescape).join(' ')} \
          --fastas #{tmp}/in_paths.txt \
          #{clean_name_regex ? "--clean_genome_names " + clean_name_regex : ''} \
          --output #{t.name}
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
  abort "FATAL: Task parsnp requires specifying IN_QUERY" unless IN_QUERY
  abort "FATAL: Task parsnp requires specifying OUT_PREFIX" unless OUT_PREFIX
  abort "FATAL: Task parsnp requires specifying PATHOGENDB_MYSQL_URI" unless PATHOGENDB_MYSQL_URI
  
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

  opts = {in_query: IN_QUERY, distance_unit: "parsnp SNPs", trees: [], parsnp_stats: [], 
          adapter: PATHOGENDB_ADAPTER}
  json = heatmap_json(IN_PATHS, PATHOGENDB_MYSQL_URI, opts) do |json, node_hash|
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
      tsv << row.values.map{ |v| v.is_a?(Time) ? v.strftime("%FT%T%:z") : v.to_s }
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
  abort "FATAL: Task epi requires specifying PATHOGENDB_MYSQL_URI" unless PATHOGENDB_MYSQL_URI 
  
  json = {generated: DateTime.now.to_s, in_query: IN_QUERY, isolates:[]}
  pdb.isolates(IN_QUERY).each do |row|
    json[:isolates] << [row[:order_date], row[:collection_unit]]
  end
 
  File.open(task.name, "w") { |f| JSON.dump(json, f) }
end
