require 'pp'
require 'net/http'
require_relative 'lib/colors'
require_relative 'lib/lsf_client'
require 'shellwords'
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

OUT     = File.expand_path(ENV['OUT'] || "#{REPO_DIR}/out")
IN_FOFN = ENV['IN_FOFN'] && File.expand_path(ENV['IN_FOFN'])

begin
  IN_PATHS = IN_FOFN && File.new(IN_FOFN).readlines.map(&:strip).reject(&:empty?)
  IN_PATHS_PAIRS = IN_PATHS && IN_PATHS.permutation(2)
rescue Errno::ENOENT
  abort "FATAL: Could not read the file you specified as IN_FOFN. Check the path and permissions?"
end

#######
# Other environment variables that may be set by the user for specific tasks (see README.md)
#######

OUT_PREFIX = ENV['OUT_PREFIX'] || "out"

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
task :check => [:env, "#{REPO_DIR}/scripts/env.sh", :mugsy_install, :clustalw, :raxml, :mauve_install, :grimm] do
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
task :mugsy => [:check, "RAxML_bestTree.#{OUT_PREFIX}", "RAxML_marginalAncestralStates.#{OUT_PREFIX}_mas",
                "#{OUT_PREFIX}_snp_tree.newick"]

file "#{OUT_PREFIX}.fa" do |t|
  # First, performs whole genome alignment with Mugsy, producing a .maf file that we convert to .fa
  abort "FATAL: Task mugsy requires specifying IN_FOFN" unless IN_PATHS
  abort "FATAL: Task mugsy requires specifying OUT_PREFIX" unless OUT_PREFIX
  abort "FATAL: Task mugsy requires specifying OUTGROUP" unless ENV['OUTGROUP']
  
  mkdir_p "#{OUT}/log"
  
  paths = IN_PATHS.map{|f| Shellwords.escape(f.strip) }.join(' ')
  
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
  SH
end

file "#{OUT_PREFIX}_1.fa-gb.phy" => "#{OUT_PREFIX}_1.fa" do |t|
  abort "FATAL: Task mugsy requires specifying OUT_PREFIX" unless OUT_PREFIX
  
  mkdir_p "#{OUT}/log"
  LSF.set_out_err("log/mugsy_phy.log", "log/mugsy_phy.err.log")
  LSF.job_name "#{OUT_PREFIX}_1.fa-gb.phy"
  LSF.bsub_interactive <<-SH
  /sc/orga/projects/InfectiousDisease/tools/Gblocks_0.91b/Gblocks #{OUT_PREFIX}_1.fa -t=d -b5=a -b4=1000
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
  SH
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
  
  paths = IN_PATHS.map{|f| Shellwords.escape(f.strip) }.join(' ')
  
  LSF.set_out_err("log/mauve.log", "log/mauve.err.log")
  LSF.job_name "#{OUT_PREFIX}.xmfa"
  LSF.bsub_interactive <<-SH
    #{MAUVE_DIR}/linux-x64/progressiveMauve --output=#{OUT_PREFIX}.xmfa --seed-weight=#{seed_weight} \
         --weight=#{lcb_weight} #{paths}
  SH
end


# ============
# = sv_snv =
# ============

desc "Pairwise analysis of structural + single nucleotide changes between genomes"
task :sv_snv => [:check, "#{OUT_PREFIX}.sv_snv", :sv_snv_check, :sv_snv_files]
task :sv_snv_check do
  abort "FATAL: Task sv_snv requires specifying IN_FOFN" unless IN_PATHS
  abort "FATAL: Task sv_snv requires specifying SEED_WEIGHT" unless ENV['SEED_WEIGHT']
  abort "FATAL: Task sv_snv requires specifying LCB_WEIGHT" unless ENV['LCB_WEIGHT']
  
  genome_names = IN_PATHS.map{|path| File.basename(path).sub(/\.\w+$/, '') }
  unless genome_names.uniq.size == genome_names.size
    abort "FATAL: Task sv_snv requires that all IN_FOFN filenames (with the extension removed) are unique"
  end
end

SV_SNV_FILES = []
# Setup, as dependencies for this task, all permutations of IN_FOFN genome names
directory "#{OUT_PREFIX}.sv_snv"
IN_PATHS && IN_PATHS.map{|path| File.basename(path).sub(/\.\w+$/, '') }.each do |genome_name|
  directory "#{OUT_PREFIX}.sv_snv/#{genome_name}"
  Rake::Task[:sv_snv_check].enhance ["#{OUT_PREFIX}.sv_snv/#{genome_name}"]
end
IN_PATHS_PAIRS && IN_PATHS_PAIRS.each do |pair|
  genome_names = pair.map{|path| File.basename(path).sub(/\.\w+$/, '') }
  SV_SNV_FILES << "#{OUT_PREFIX}.sv_snv/#{genome_names[0]}/#{genome_names.join '_'}.bed"
end

multitask :sv_snv_files => SV_SNV_FILES

def genomes_from_task_name(task_name)
  genomes = [{:name => task_name.sub("#{OUT_PREFIX}.sv_snv/", '').split(/\//).first}]
  genomes[1] = {:name => task_name.sub("#{OUT_PREFIX}.sv_snv/#{genomes[0][:name]}/#{genomes[0][:name]}_", '').split(/\./).first}
  genomes.each do |g| 
    g[:path] = IN_PATHS.find{|path| path =~ /#{g[:name]}\.\w+$/ }
  end
  genomes
end

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
rule '.bed' => '.xmfa.backbone' do |task|
  genomes = genomes_from_task_name(task.name)
  backbone_file = task.name.sub(/\.bed$/, '.xmfa.backbone')
  grimm_file = task.name.sub(/\.bed$/, '.grimm')
  
  system <<-SH or abort
    #{REPO_DIR}/scripts/backbone-to-grimm.rb #{Shellwords.escape backbone_file} \
        --ref #{Shellwords.escape genomes[0][:path]} \
        --query #{Shellwords.escape genomes[1][:path]} \
        --grimm #{GRIMM_DIR}/grimm \
        --bed #{Shellwords.escape task.name} \
        #{Shellwords.escape grimm_file}
  SH
end
