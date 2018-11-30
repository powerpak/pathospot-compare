require 'rubygems'
require 'bundler/setup'
require 'rake-multifile'
require 'pp'
require 'net/http'
require_relative 'lib/colors'
require_relative 'lib/lsf_client'
require_relative 'lib/pathogendb_client'
require_relative 'lib/filter_fasta'
require_relative 'lib/heatmap_json'
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
PATHOGENDB_MYSQL_URI = nil if PATHOGENDB_MYSQL_URI =~ /user:host@pass/ # ignore the example value
IGB_DIR = ENV['IGB_DIR']

if IN_QUERY
  abort "FATAL: IN_QUERY requires also specifying PATHOGENDB_MYSQL_URI" unless PATHOGENDB_MYSQL_URI
  abort "FATAL: IN_QUERY requires also specifying IGB_DIR" unless IGB_DIR
  pdb = PathogenDBClient.new(PATHOGENDB_MYSQL_URI)
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
  puts "Output directory: #{OUT}"
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
    system <<-SH
      curl -L -o mugsy.tar.gz 'http://sourceforge.net/projects/mugsy/files/mugsy_x86-64-v1r2.2.tgz/download'
      tar xvzf mugsy.tar.gz
      mv mugsy_x86-64-v1r2.2/* '#{MUGSY_DIR}'
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
    system <<-SH
      curl -L -o clustalw.tar.gz 'http://www.clustal.org/download/current/clustalw-2.1-linux-x86_64-libcppstatic.tar.gz'
      tar xvzf clustalw.tar.gz
      mv clustalw-2.1-linux-x86_64-libcppstatic/* #{Shellwords.escape(CLUSTALW_DIR)}
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
    system <<-SH
      curl -L -o raxml.tar.gz 'https://github.com/stamatak/standard-RAxML/archive/v8.0.2.tar.gz'
      tar xvzf raxml.tar.gz
      rm raxml.tar.gz
    SH
  end
  Dir.chdir("#{File.dirname(CLUSTALW_DIR)}/standard-RAxML-8.0.2") do
    system "make -f Makefile.gcc" and cp("raxmlHPC", "#{RAXML_DIR}/raxmlHPC")
  end
  rm_rf "#{File.dirname(CLUSTALW_DIR)}/standard-RAxML-8.0.2"
end

# pulls down precompiled static binaries and JAR files for Mauve 2.3.1, which is used by the mauve task
# see http://asap.genetics.wisc.edu/software/mauve/
task :mauve_install => [:env, MAUVE_DIR, "#{MAUVE_DIR}/linux-x64/progressiveMauve"]
directory MAUVE_DIR
file "#{MAUVE_DIR}/linux-x64/progressiveMauve" do
  Dir.chdir(File.dirname(MAUVE_DIR)) do
    system <<-SH
      curl -L -o mauve.tar.gz 'http://darlinglab.org/mauve/downloads/mauve_linux_2.4.0.tar.gz'
      tar xvzf mauve.tar.gz
      mv mauve_2.4.0/* #{Shellwords.escape(MAUVE_DIR)}
      rm -rf mauve.tar.gz mauve_linux_2.4.0.tar.gz
    SH
  end
end

# pulls down and compiles grimm, which is used by the sv_snv track to calculate rearrangement distance
task :grimm => [:env, GRIMM_DIR, "#{GRIMM_DIR}/grimm"]
directory GRIMM_DIR
file "#{GRIMM_DIR}/grimm" do
  Dir.chdir(File.dirname(GRIMM_DIR)) do
    system <<-SH
      curl -L -o grimm.tar.gz 'http://grimm.ucsd.edu/DIST/GRIMM-2.01.tar.gz'
      tar xvzf grimm.tar.gz
      mv GRIMM-2.01/* #{Shellwords.escape(GRIMM_DIR)}
      rm -rf GRIMM-2.01 grimm.tar.gz
      sed -i.bak 's/-march=pentiumpro//g' #{Shellwords.escape(GRIMM_DIR)}/Makefile
    SH
  end
  Dir.chdir(GRIMM_DIR){ system "make" }
end

# pulls down and compiles Gblocks, which is used by the mugsy task
task :gblocks => [:env, GBLOCKS_DIR, "#{GBLOCKS_DIR}/Gblocks"]
directory GBLOCKS_DIR
file "#{GBLOCKS_DIR}/Gblocks" do
  Dir.chdir(File.dirname(GBLOCKS_DIR)) do
    system <<-SH
      curl -L -o gblocks.tar.gz 'http://molevol.cmima.csic.es/castresana/Gblocks/Gblocks_Linux64_0.91b.tar.Z'
      tar xvzf gblocks.tar.gz
      mv Gblocks_0.91b/* #{Shellwords.escape(GBLOCKS_DIR)}
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
    system <<-SH
      curl -L -o Harvest-Linux64-v1.1.2.tar.gz 'https://github.com/marbl/harvest/releases/download/v1.1.2/Harvest-Linux64-v1.1.2.tar.gz'
      tar xvzf Harvest-Linux64-v1.1.2.tar.gz
      mv Harvest-Linux64-v1.1.2/* #{Shellwords.escape(HARVEST_DIR)}
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
    system <<-SH
      curl -L -o mash-Linux64-v2.1.tar 'https://github.com/marbl/Mash/releases/download/v2.1/mash-Linux64-v2.1.tar'
      tar xvf mash-Linux64-v2.1.tar
      mv mash-Linux64-v2.1/* #{Shellwords.escape(MASH_DIR)}
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
  
  paths = IN_PATHS.map{ |f| Shellwords.escape(f.strip) }.join(' ')
  
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
  
  tree_file = Shellwords.escape "RAxML_bestTree.#{OUT_PREFIX}"
  system <<-SH
    module load R/3.1.0
    R --no-save -f #{REPO_DIR}/scripts/plot_phylogram.R --args #{tree_file}
  SH
end

file "#{OUT_PREFIX}_snp_tree.newick.pdf" => "#{OUT_PREFIX}_snp_tree.newick" do |t|
  abort "FATAL: Task mugsy_plot requires specifying OUT_PREFIX" unless OUT_PREFIX
  
  tree_file = Shellwords.escape "#{OUT_PREFIX}_snp_tree.newick"
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
  
  paths = IN_PATHS.map{ |f| Shellwords.escape(f.strip) }.join(' ')
  
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
         --weight=#{ENV['LCB_WEIGHT']} #{Shellwords.escape genomes[0][:path]} #{Shellwords.escape genomes[1][:path]}
  SH
end

# We create BED files that can visually depict these structural variants
rule %r{\.sv\.bed$} => proc{ |n| n.sub(%r{\.sv\.bed$}, '.xmfa.backbone') } do |task|
  genomes = genomes_from_task_name(task.name)
  backbone_file = task.name.sub(/\.sv\.bed$/, '.xmfa.backbone')
  grimm_file = task.name.sub(/\.sv\.bed$/, '.grimm')
  
  system <<-SH or abort
    #{REPO_DIR}/scripts/backbone-to-grimm.rb #{Shellwords.escape backbone_file} \
        --ref #{Shellwords.escape genomes[0][:path]} \
        --query #{Shellwords.escape genomes[1][:path]} \
        --grimm #{GRIMM_DIR}/grimm \
        --bed #{Shellwords.escape task.name} \
        #{Shellwords.escape grimm_file}
  SH
end


###
# Creating .snv.bed files from pairwise MUMmer (nucmer) alignments
###

# This rule creates a filtered FASTA file from the original that drops any contigs flagged as "merged" or "garbage"
rule %r{\.filt\.(fa|fasta)$} => proc{ |n| filtered_to_unfiltered(n) } do |task|
  filter_fasta_by_entry_id(task.source, task.name, /_[mg]_/, :invert => true)
end

rule '.delta' => proc{ |n| genomes_from_task_name(n).map{ |g| [g[:filt_path], g[:out_dir]] }.flatten.uniq } do |task|
  genomes = genomes_from_task_name(task.name)
  output = task.name.sub(/\.delta$/, '')
  
  system <<-SH
    module load mummer/3.23
    nucmer -p #{output} #{Shellwords.escape genomes[0][:filt_path]} #{Shellwords.escape genomes[1][:filt_path]}
  SH
end

rule '.filtered-delta' => '.delta' do |task|  
  system <<-SH
    module load mummer/3.23
    delta-filter -r -q #{Shellwords.escape task.source} > #{Shellwords.escape task.name}
  SH
end

rule %r{(\.snv\.bed|\.snps\.count)$} => proc{ |n| n.sub(%r{(\.snv\.bed|\.snps\.count)$}, '.filtered-delta') } do |task|
  snps_file = task.name.sub(/(\.snv\.bed|\.snps\.count)$/, '.snps')
  # necessary because the .snps.count can also trigger this task
  bed_file = task.name.sub(/(\.snv\.bed|\.snps\.count)$/, '.snv.bed')
  
  system <<-SH or abort
    module load mummer/3.23
    show-snps -IHTClr #{Shellwords.escape task.source} > #{Shellwords.escape snps_file}
  SH
  
  File.open("#{snps_file}.count", 'w') { |f| f.write(`wc -l #{Shellwords.escape snps_file}`.strip.split(' ')[0]) }
  
  system <<-SH
    #{REPO_DIR}/scripts/mummer-snps-to-bed.rb #{Shellwords.escape snps_file} \
      --limit #{BED_LINES_LIMIT} \
      #{Shellwords.escape bed_file}
  SH
  
  verbose(false) { rm snps_file }  # because these are typically huge, and redundant w/ the BED files
end

###
# The summary BED track (for :sv_snv) is just a concatenation of both the .sv.bed and .snv.bed tracks
###
rule %r{\.sv_snv\.bed$} => proc{ |n| [n.sub(%r{\.sv_snv\.bed$}, '.snv.bed'), 
    n.sub(%r{\.sv_snv\.bed$}, '.sv.bed')] } do |task|
  system <<-SH or abort
    cat #{Shellwords.escape task.sources[0]} #{Shellwords.escape task.sources[1]} > #{Shellwords.escape task.name}
  SH
end


# ===========
# = heatmap =
# ===========

HEATMAP_SNV_JSON_FILE = "#{OUT_PREFIX}.#{Date.today.strftime('%Y-%m-%d')}.snv.heatmap.json"
desc "Generate assembly distances for heatmap in pathogendb-viz"
task :heatmap => [:check, HEATMAP_SNV_JSON_FILE]
SNV_COUNT_FILES = SNV_FILES.map{ |path| path.sub(%r{\.snv\.bed$}, '.snps.count') }

multifile HEATMAP_SNV_JSON_FILE do |task| #=> SNV_COUNT_FILES do |task|
  abort "FATAL: Task heatmap requires specifying IN_FOFN or IN_QUERY" unless IN_PATHS
  abort "FATAL: Task heatmap requires specifying OUT_PREFIX" unless OUT_PREFIX
  abort "FATAL: Task heatmap requires specifying PATHOGENDB_MYSQL_URI" unless PATHOGENDB_MYSQL_URI 
  
  opts = {out_dir: "#{OUT_PREFIX}.sv_snv", in_query: IN_QUERY}
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
 
  File.open(task.name, 'w') { |f| JSON.dump(json, f) }
end


# ============
# = heatmap3 =
# ============

HEATMAP_SNV_JSON_FILE = "#{OUT_PREFIX}.#{Date.today.strftime('%Y-%m-%d')}.snv.heatmap3.json"
desc "Generate assembly distances for heatmap in pathogendb-viz (mode 3)"
task :heatmap3 => [:check, HEATMAP_SNV_JSON_FILE]

file HEATMAP_SNV_JSON_FILE do |task| #=> SNV_COUNT_FILES do |task|
  abort "FATAL: Task heatmap requires specifying IN_FOFN" unless IN_PATHS
  abort "FATAL: Task heatmap requires specifying OUT_PREFIX" unless OUT_PREFIX
  mkdir_p "#{OUT}/heatmap_wd"
  system <<-SH or abort
    module load python/2.7.6
    module load py_packages/2.7
    module load mummer/3.23
    python #{REPO_DIR}/scripts/calculate_snvs.py --fofn #{IN_FOFN} --path_to_mash #{MASH_DIR}/mash --path_to_parsnp #{HARVEST_DIR}/parsnp --path_to_harvest #{HARVEST_DIR}/harvesttools --working_dir #{OUT}/heatmap_wd --output #{HEATMAP_SNV_JSON_FILE}
  SH
end


# ==========
# = parsnp =
# ==========

HEATMAP_PARSNP_JSON_FILE = "#{OUT_PREFIX}.#{Date.today.strftime('%Y-%m-%d')}.parsnp.heatmap.json"
HEATMAP_PARSNP_TSV_FILE = "#{OUT_PREFIX}.#{Date.today.strftime('%Y-%m-%d')}.parsnp.heatmap.tsv"
desc "uses Parsnp to create *.xmfa, *.ggr, and *.tree files plus a SNV distance matrix"
task :parsnp => [:check, HEATMAP_PARSNP_JSON_FILE]

def repeat_masked_to_filtered(masked_path)
  name = File.basename(masked_path).sub(%r{\.repeat_mask\.(fa|fasta)$}, '.filt.\\1')
  ["#{OUT_PREFIX}.contig_filter/#{name}", "#{OUT_PREFIX}.repeat_mask"]
end

directory "#{OUT_PREFIX}.repeat_mask"
rule %r{\.repeat_mask\.(fa|fasta)$} => proc{ |n| repeat_masked_to_filtered(n) } do |task|
  fasta_mask_repeats(task.source, task.name)
end
REPEAT_MASKED_FILES = (IN_PATHS || []).map do |path|
  "#{OUT_PREFIX}.repeat_mask/" + File.basename(path).sub(%r{\.(fa|fasta)$}, '.repeat_mask.\\1')
end

rule %r{#{OUT_PREFIX}\.\d+\.clust} => proc{ |n| } do |t|
  # TODO
end

directory "#{OUT_PREFIX}.parsnp"
multifile "#{OUT_PREFIX}.parsnp/parsnp.ggr" => (["#{OUT_PREFIX}.parsnp"] + REPEAT_MASKED_FILES) do |t|
  # TODO ... instead of this task as written
  #  X. filter bad contigs out of the fastas into #{OUT_PREFIX}.contig_filter/*.filt.(fa|fasta), 
  #     just as in the mummer SNV pathway
  #  X. filter tandem repeats out of the genomes with mummer, as in calculate_snvs.py, and put 
  #     the filtered fastas into a "#{OUT_PREFIX}.repeat_mask" directory as 
  #     .repeat_mask.(fa|fasta) files
  #  2. cluster them, roughly, by MASH or MUMi distance, and symlink them into
  #     #{OUT_PREFIX}.0.clust, #{OUT_PREFIX}.1.clust, etc. directories
  #  3. run parsnp multiple times into #{OUT_PREFIX}.0.parsnp, #{OUT_PREFIX}.1.parsnp etc. 
  #     directories
  #  4. each of the #{OUT_PREFIX}.*.parsnp directories will require .vcf and .nwk to be extracted from .ggr
  #  5. each of the #{OUT_PREFIX}.*.parsnp directories will require a parsnp.snv_distance.tsv file of SNV 
  #     distances to be calculated
  #  6. create a "#{OUT_PREFIX}.#{Date.today.strftime('%Y-%m-%d')}.parsnp.heatmap.json" that
  #     recombines all the TSVs of distances into one big matrix (uncalculated distances are marked as nil
  #     or infinitely large), and also includes the .nwk trees
  #     TODO: how to best get the VCF allele information into the JSON file? 

  if ENV['GBK']
    referenceOrGenbank = "-g #{Shellwords.escape(ENV['GBK'])}"
  else
    referenceOrGenbank = ENV['REF'] ? "-r #{Shellwords.escape(ENV['REF'])}" : "-r !"
  end

  # Run parsnp.
  system <<-SH or abort
    #{HARVEST_DIR}/parsnp #{referenceOrGenbank} -c \
        -o #{OUT_PREFIX}.parsnp/ \
        -d #{OUT_PREFIX}.repeat_mask/
  SH
end

file "#{OUT_PREFIX}.parsnp/parsnp.vcf" => "#{OUT_PREFIX}.parsnp/parsnp.ggr" do |t|
  dir = "#{OUT_PREFIX}.parsnp"
  system "#{HARVEST_DIR}/harvesttools -i #{dir}/parsnp.ggr -V #{dir}/parsnp.vcf" or abort
end

# The .nwk tree is different from the .tree in that it uses distances scaled to SNVs/Mbp
# See harvesttools option " -u 0/1 (update the branch values to reflect genome length)"
file "#{OUT_PREFIX}.parsnp/parsnp.clean.nwk" => "#{OUT_PREFIX}.parsnp/parsnp.ggr" do |t|
  dir = "#{OUT_PREFIX}.parsnp"
  system "#{HARVEST_DIR}/harvesttools -i #{dir}/parsnp.ggr -N #{dir}/parsnp.nwk" or abort
  system <<-SH or abort
    module load python/2.7.6
    module load py_packages/2.7
    python #{REPO_DIR}/scripts/cleanup_parsnp_newick.py #{dir}/parsnp.nwk #{dir}/parsnp.clean.nwk
  SH
end

PARSNP_OUT_FILES = ["#{OUT_PREFIX}.parsnp/parsnp.vcf", "#{OUT_PREFIX}.parsnp/parsnp.clean.nwk"]
file HEATMAP_PARSNP_TSV_FILE => PARSNP_OUT_FILES do |t|
  system <<-SH or abort
    module load python/2.7.6
    module load py_packages/2.7
    python #{REPO_DIR}/scripts/parsnp2table.py #{t.source} #{t.name}
  SH
end
file HEATMAP_PARSNP_JSON_FILE => HEATMAP_PARSNP_TSV_FILE do |t|
  abort "FATAL: Task parsnp requires specifying IN_FOFN or IN_QUERY" unless IN_PATHS
  abort "FATAL: Task parsnp requires specifying OUT_PREFIX" unless OUT_PREFIX
  abort "FATAL: Task parsnp requires specifying PATHOGENDB_MYSQL_URI" unless PATHOGENDB_MYSQL_URI
  snv_tsv = CSV.read(t.source, col_sep: "\t")
  tsv_key = Hash[snv_tsv.first.drop(1).zip(1..snv_tsv.size)]

  opts = {in_query: IN_QUERY, distance_unit: "parsnp SNPs"}
  json = heatmap_json(IN_PATHS, PATHOGENDB_MYSQL_URI, opts) do |json, node_hash|
    (node_hash.keys - tsv_key.keys).each do |name|
      puts "WARN: Assembly #{name} isn't in the parsnp alignment; skipping"
    end
    node_hash.each do |source_name, source|
      node_hash.each do |target_name, target|
        next unless source[:metadata] && target[:metadata]
        next unless tsv_key[source_name] && tsv_key[target_name]
        snp_distance = snv_tsv[tsv_key[source_name]][tsv_key[target_name]].to_i
        json[:links][source[:id]][target[:id]] = snp_distance
      end
    end
    json[:trees] = [File.read("#{OUT_PREFIX}.parsnp/parsnp.clean.nwk").strip]
  end

  File.open(t.name, 'w') { |f| JSON.dump(json, f) }
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
  
  pdb = PathogenDBClient.new(PATHOGENDB_MYSQL_URI)
  
  json = {generated: DateTime.now.to_s, in_query: IN_QUERY, isolates:[]}
  pdb.isolates(IN_QUERY).each do |row|
    json[:isolates] << [row[:order_date], row[:collection_unit]]
  end
 
  File.open(task.name, 'w') { |f| JSON.dump(json, f) }
end
