require 'pp'
require 'net/http'
require_relative 'lib/colors'
require_relative 'lib/lsf_client'
require 'shellwords'
include Colors

task :default => :check

LSF = LSFClient.new

REPO_DIR = File.dirname(__FILE__)
MUGSY_DIR = "#{REPO_DIR}/vendor/mugsy"
CLUSTALW_DIR = "#{REPO_DIR}/vendor/clustalw"
RAXML_DIR = "#{REPO_DIR}/vendor/raxml"
MAUVE_DIR = "#{REPO_DIR}/vendor/mauve"

OUT = File.expand_path(ENV['OUT'] || "#{REPO_DIR}/out")

#######
# Other environment variables that may be set by the user for specific tasks (see README.md)
#######


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

file "#{REPO_DIR}/scripts/env.sh" => "#{REPO_DIR}/scripts/env.example.sh" do
  cp "#{REPO_DIR}/scripts/env.example.sh", "#{REPO_DIR}/scripts/env.sh"
end

ENV_ERROR = "Configure this in scripts/env.sh and run `source scripts/env.sh` before running rake."

desc "Checks environment variables and requirements before running tasks"
task :check => [:env, "#{REPO_DIR}/scripts/env.sh", :mugsy_install, :clustalw, :raxml, :mauve_install] do
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
task :mauve_install => [:env, MAUVE_DIR, "#{MAUVE_DIR}/progressiveMauve"]
directory MAUVE_DIR
file "#{MAUVE_DIR}/progressiveMauve" do
  Dir.chdir(File.dirname(MAUVE_DIR)) do
    system <<-SH
      curl -L -o mauve.tar.gz 'http://asap.genetics.wisc.edu/software/mauve/downloads/mauve_linux_2.3.1.tar.gz'
      tar xvzf mauve.tar.gz
      mv mauve_2.3.1/* #{Shellwords.escape(MAUVE_DIR)}
      rm -rf mauve_2.3.1 mauve.tar.gz
    SH
  end
end

file "pathogendb-comparison.png" => [:graph]
desc "Generates a graph of tasks, intermediate files and their dependencies from this Rakefile"
task :graph do
  system <<-SH
    module load graphviz
    STRAIN_NAME=STRAIN_NAME rake -f #{Shellwords.escape(__FILE__)} -P \
        | #{REPO_DIR}/scripts/rake-prereqs-dot.rb --prune #{REPO_DIR} --replace-with REPO_DIR \
        | dot -Tpng -o pathogendb-comparison.png
  SH
end


# =========
# = mugsy =
# =========

desc "Produces a phylogenetic tree using Mugsy, ClustalW, and RAxML"
task :mugsy do |t|
  path_file = ENV['IN_FOFN']
  abort "FATAL: Task mugsy requires specifying IN_FOFN" unless path_file
  tree_name = ENV['OUT_PREFIX']
  abort "FATAL: Task mugsy requires specifying OUT_PREFIX" unless tree_name
  outgroup = ENV['OUTGROUP']
  abort "FATAL: Task mugsy requires specifying OUTGROUP" unless outgroup
  
  tree_directory = OUT
  mkdir_p "#{OUT}/log"
  
  fofn = File.new(path_file)
  paths = fofn.readlines.map{|f| Shellwords.escape(f.strip) }.join(' ')
  
  LSF.set_out_err("log/mugsy.log", "log/mugsy.err.log")
  LSF.job_name "#{tree_name}_mas"
  LSF.bsub_interactive <<-SH
    export MUGSY_INSTALL=#{MUGSY_DIR} &&
    #{MUGSY_DIR}/mugsy -p #{tree_name} --directory #{tree_directory} #{paths} &&
    perl #{REPO_DIR}/scripts/processMAF_File.pl #{tree_name}.maf > #{tree_name}.fa
    
    # no point in going further if mugsy failed
    if [ ! -f #{tree_name}.fa ]; then exit 1; fi
    
    # Replace all hyphens (non-matches) with 'N' in sequence lines in this FASTA file
    # Also replace the first period in sequence IDs with a stretch of 10 spaces
    # This squelches the subsequent contig IDs or accession numbers when converting to PHYLIP
    sed '/^[^>]/s/\-/N/g' #{tree_name}.fa | sed '/^>/s/\./          /' > #{tree_name}_1.fa
    
    # Convert the FASTA file to a PHYLIP multi-sequence alignment file with ClustalW
    #{CLUSTALW_DIR}/clustalw2 -convert -infile=#{tree_name}_1.fa -output=phylip
    
    # Use RAxML to create a maximum likelihood phylogenetic tree
    # Suppress these; there are thousands of them
    #{RAXML_DIR}/raxmlHPC -s #{tree_name}_1.phy -#20 -m GTRGAMMA -n #{tree_name} -p 12345 \
        -o #{outgroup.slice(0,10)}
    #{RAXML_DIR}/raxmlHPC -f A -s #{tree_name}_1.phy -m GTRGAMMA -p 12345 \
        -t RAxML_bestTree.#{tree_name} -n #{tree_name}_mas
  SH
end


# =========
# = mauve =
# =========

desc "Produces a Mauve alignment"
task :mauve do |t|
  path_file = ENV['IN_FOFN']
  abort "FATAL: Task mauve requires specifying IN_FOFN" unless path_file
  output_name = ENV['OUT_PREFIX']
  abort "FATAL: Task mauve requires specifying OUT_PREFIX" unless output_name
  seed_weight = ENV['SEED_WEIGHT']
  abort "FATAL: Task mauve requires specifying SEED_WEIGHT" unless seed_weight
  lcb_weight = ENV['LCB_WEIGHT']
  abort "FATAL: Task mauve requires specifying LCB_WEIGHT" unless lcb_weight
  
  tree_directory = OUT
  mkdir_p "#{OUT}/log"
  
  fofn = File.new(path_file)
  paths = fofn.readlines.map{|f| Shellwords.escape(f.strip) }.join(' ')
  
  LSF.set_out_err("log/mauve.log", "log/mauve.err.log")
  LSF.job_name "#{output_name}.xmfa"
  LSF.bsub_interactive <<-SH
    #{MAUVE_DIR}/progressiveMauve --output=#{output_name}.xmfa --seed-weight=#{seed_weight} \
         --weight=#{lcb_weight} #{paths}
  SH
end
