#!/usr/bin/env ruby

# Transcodes a progressiveMauve .backbone file into an ordered list of numerical genes
# that GRIMM can use as input.
#
# progressiveMauve .backbone format is described here: http://darlinglab.org/mauve/user-guide/files.html
# GRIMM is described here: http://grimm.ucsd.edu/GRIMM/
#
# GRIMM implements the Hannenhalli-Pevzner algorithms for minimal rearrangement distance between sets of chromosomes.
#
# NOTE: This currently only handles .backbone files for two genomes.

class MauveBackboneToGrimm
  
  # Set up the tran
  def initialize(args)
    abort "FATAL: #{$0} requires a Mauve .backbone file as its first argument" unless args.size > 0
    abort "FATAL: #{args.first} does not exist" unless File.exist? args.first
    
    @backbone_file = File.new(args.first) rescue abort("FATAL: Could not open #{args.first}")
    @out = STDOUT
    
    begin
      @out = File.open(args[1], 'w') if args[1] && args[1] != '-'
    rescue
      abort("FATAL: Could not open #{args[1]}")
    end
  end
  
  def parse_input
    @backbone = []
    @backbone_file.each_line do |line|
      cells = line.split("\t")
      next if cells[0] == "seq0_leftend"
      @backbone << cells.map(&:strip).map(&:to_i)
    end
  end
  
  def extract_genes
    @backbone.sort_by!{|row| row[0].abs }
    gene_num = 0
    @backbone.each do |row|
      # Skip rows where the block is not in one or the other genome (these are islands)
      next if row[0] == 0 && row[1] == 0
      next if row[2] == 0 && row[3] == 0
      gene_num += 1
      row[4] = gene_num
    end
    
    # By definition, the first genome's genes are in order
    @gene_orders = [(1..gene_num).to_a, []]
    
    # To get the relative order in the second genome, sort by its left end positions and read off the gene numbers
    @backbone.sort_by{|row| row[2].abs }.each do |row|
      next if row[0] == 0 && row[1] == 0
      next if row[2] == 0 && row[3] == 0
      @gene_orders[1] << ((row[0] * row[2]) > 0 ? row[4] : -row[4])
    end
  end
  
  def write_output
    @gene_orders.each_with_index do |row, i|
      @out.puts ">seq#{i}"
      @out.puts row.join " "
    end
  end
  
  def run!
    parse_input
    extract_genes
    write_output
  end
  
end

# =====================================
# = If this script is called directly =
# =====================================

if __FILE__ == $0
  mbtg = MauveBackboneToGrimm.new(ARGV)
  
  mbtg.run!
end