#!/usr/bin/env ruby

require 'bio'
require 'optparse'
require 'shellwords'
require 'tempfile'
require 'pp'

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
    @options = {}

    opt_parser = OptionParser.new do |opts|
      opts.banner = <<-USAGE

Usage: #{$0} -f in.fofn [options] in.xmfa.backbone [out.grimm]

Transcodes a progressiveMauve .backbone file into an ordered list of numerical genes
that GRIMM can use as input. Optionally, if provided with the path to GRIMM, this can
run GRIMM, parse the output, and convert the result to other formats.

You *must* provide an -f/--fofn argument pointing to a file of file names for the
original FASTA sequences, which will be consulted for contig or chromosome lengths
allowing multichromosomal analysis of rearrangements by GRIMM. Otherwise, the genomes
would be considered to be contiguous, which is an inaccurate assumption.
      USAGE

      opts.separator ""
      opts.separator "Required options:"
      
      opts.on("-f", "--fofn [PATH]",
              "Path to the file of filenames (FOFN) for sequences aligned in the .xmfa.backbone") do |path|
        @options[:fofn] = path
      end

      opts.separator ""
      opts.separator "Other options:"
      
      opts.on("-g", "--grimm [PATH]",
              "Path to the compiled GRIMM binary. This script then runs it for you.") do |path|
        abort "FATAL: -g/--grimm should be the path to the executable GRIMM binary" unless File.executable? path
        @options[:grimm] = path
      end
      
      opts.on("-b", "--bed [PATH]",
              "Saves a translation of GRIMM output in BED format at this path. Requires -g/--grim") do |path|
        abort "FATAL: --bed requires that --grimm is specified" unless @options[:grimm]
        @options[:bed] = path
      end

      opts.on_tail("-h", "--help", "Show this message") do
        abort opts.to_s
      end
    end
    
    opt_parser.parse!(args)
    
    if args.size < 1
      puts "FATAL: #{$0} requires a Mauve .backbone file as its first argument"
      abort opt_parser.help
    end
    
    abort "FATAL: -f/--fofn parameter is required" + opt_parser.help unless @options[:fofn]
        
    @backbone_file = File.new(args.first) rescue abort("FATAL: Could not open #{args.first}")
    @out = STDOUT
    @out_path = '-'
    
    if args[1] && args[1] != '-'
      @out = File.open(args[1], 'w') rescue abort("FATAL: Could not open #{args[1]}")
      @out_path = args[1]
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
  
  def parse_fofn(fofn_path = nil)
    fofn_path ||= @options[:fofn]
    @seqs = []
    fh = File.open(fofn_path) rescue abort("FATAL: Could not open --fofn parameter #{fofn_path}")
    fh.each_line do |seq_path|
      chrom_sizes = []
      seq_fh = Bio::FlatFile.auto(seq_path.strip)
      seq_fh.each_with_index do |entry, i| 
        chr_pos = 1 + entry.naseq.size + (i > 0 ? chrom_sizes.last[:pos] : 0)
        chrom_sizes << {:name => entry.definition.gsub('|', '_'), :pos => chr_pos}
      end
      @seqs << chrom_sizes
    end
    fh.close
  end
  
  def extract_genes
    @backbone.sort_by!{|row| row[0].abs }
    @gene_orders = [[], []]
    gene_num = 0
    chr_num = 0
    @backbone.each do |row|
      # Skip rows where the block is not in one or the other genome (these are islands)
      next if row[0] == 0 && row[1] == 0
      next if row[2] == 0 && row[3] == 0
      # If we have chromosome boundaries, add them as required to the GRIMM numbered gene list
      if @seqs && row[0].abs >= @seqs[0][chr_num][:pos]
        @gene_orders[0] << '$'
        chr_num += 1 until @seqs[0][chr_num][:pos] > row[0].abs
      end
      
      gene_num += 1
      row[4] = gene_num
      @gene_orders[0] << gene_num
    end
        
    # To get the relative order in the second genome, sort by its left end positions and read off the gene numbers
    chr_num = 0
    @backbone.sort_by{|row| row[2].abs }.each do |row|
      # Skip rows where the block is not in one or the other genome (these are islands)
      next if row[0] == 0 && row[1] == 0
      next if row[2] == 0 && row[3] == 0
      # If we have chromosome boundaries, add them as required to the GRIMM numbered gene list
      if @seqs && row[2].abs >= @seqs[1][chr_num][:pos]
        @gene_orders[1] << '$'
        chr_num += 1 until @seqs[1][chr_num][:pos] > row[2].abs
      end
      
      @gene_orders[1] << ((row[0] * row[2]) > 0 ? row[4] : -row[4])
    end
  end
  
  def write_output(fh = nil)
    fh ||= @out
    @gene_orders.each_with_index do |row, i|
      fh.puts ">seq#{i}"
      fh.puts row.join " "
    end
  end
  
  def run_grimm
    if @out_path == '-'
      Tempfile.open('backbone-to-grimm') do |fh|
        write_output(fh)
        parse_grimm `#{Shellwords.escape @options[:grimm]} -f #{Shellwords.escape fh.path}`
      end
    else
      parse_grimm `#{Shellwords.escape @options[:grimm]} -f #{Shellwords.escape @out_path}`
    end
  end
  
  def parse_grimm(grimm_output)
    @parsed = {:rearrangements => []}
    parts = grimm_output.split('======================================================================')
    parts.first.split(/\n/).each do |line|
      k, v = line.split(/:/, 2).map(&:strip)
      v.sub!(/\s+\(\w+\)$/, '') if k == "Number of Chromosomes"
      @parsed[k.downcase.gsub(' ', '_').to_sym] = v.match(/\A[+-]?\d+\Z/) ? v.to_i : v
    end
    parts[2].split(/\n/).each do |line|
      # Parse lines of the form:
      # Step 1: Chrom. 1, gene 587 [587] through chrom. 1, gene 591 [591]: Reversal
      # into an orderly array of rearrangement
      next unless line =~ /^Step (\d)+:/
      next if $1.to_i == 0
      m = line.match(/Chrom. (\d+), gene (-?\d+) \[(-?\d+)\] through chrom. (\d+), gene (-?\d+) \[(-?\d+)\]:([\w ]+)/)
      @parsed[:rearrangements] << m.to_a.slice(1..-2).map(&:to_i).concat([m[-1].strip])
    end
  end
  
  def collect_bed_data
    # First, collect all presumptive insertions.  We will want to match them with deletions to create indels where possible.
    insertions = @backbone.select{|row| row[0] == 0 && row[1] == 0 }
    bed = {:indels => [], :inserts => [], :dels => []}
    
    # @backbone is sorted by row[0].abs to start.
    # We are going iterate over all presumptive deletions
    @backbone.each_with_index do |row, i|
      next unless row[2] == 0 && row[3] == 0
      prev = @backbone[i - 1]
      after = @backbone[i + 1 % @backbone.size]
      
      # Look for an insertion that matches this deletion
      if prev[4] && after[4] # implies that both rows have nonzero values in all columns
        if prev[3].abs < after[2].abs
          # Same orientation. If we find a matching insertion, we'll pair the insertion/deletion and call this an indel 
          if insertions.delete([0, 0, prev[3].abs + 1, after[2].abs - 1])
            bed[:indels] << [row[0], row[1] + 1, "ins(#{after[2].abs - prev[3].abs - 1})del(#{row[1] - row[0] + 1})", '+']
            next
          end
        else
          # Reverse orientation. Same as above.
          if insertions.delete([0, 0, after[3].abs + 1, prev[2].abs - 1])
            bed[:indels] << [row[0], row[1] + 1, "ins(#{prev[2].abs - after[3].abs - 1})del(#{row[1] - row[0] + 1})", '-']
            next
          end
        end
      end
      
      # No match. we'll call it a straight up deletion
      bed[:dels] << [row[0], row[1] + 1, "del(#{row[1] - row[0] + 1})", '+']
    end
    
    # Sort by the second genome now, and try to align the remaining insertions to the first genome
    resorted = @backbone.sort_by{|row| row[2].abs }
    resorted.each_with_index do |row, i|
      next unless row[0] == 0 && row[1] == 0 && insertions.include?(row)
      prev = resorted[i - 1]
      after = resorted[i + 1 % @backbone.size]
      
      # If surrounding matches to the first genome are in the same orientation, and consecutive,
      # this is a straight up insertion that is unambiguously alignable to the first genome
      if prev[4] && after[4] && (prev[4] < 0 == after[4] < 0) && after[4] - prev[4] == 1
        if after[4] > 0
          del_size = after[0] - prev[1] - 1
          bed[:inserts] << [prev[1] + 1, after[0], "ins(#{row[3] - row[2] + 1})", '+']
        else
          del_size = prev[0].abs - after[1].abs - 1
          bed[:inserts] << [after[1].abs + 1, prev[0].abs, "ins(#{row[3] - row[2] + 1})", '+']
        end
      else
        # No alignable match to the other genome, so it could align to either of two positions
        possible_aligns = [prev[0] < 0 ? prev[0].abs : prev[1], after[0] < 0 ? after[1].abs : after[0]]
        # Do we always pick one side? Dilemma
        bed[:inserts] << [row[2], row[3]]
      end
    end
    
    pp bed
    
    bed
  end
  
  def write_bed(bed_path = nil)
    bed_path ||= @options[:bed]
    fh = File.open(bed_path, 'w') rescue abort("FATAL: Could not open #{bed_path} for writing BED output")
    bed_tracks = collect_bed_data
  end
  
  def run!
    parse_fofn
    parse_input
    extract_genes
    write_output
    run_grimm if @options[:grimm]
    write_bed if @options[:bed]
  end
  
end

# =====================================
# = If this script is called directly =
# =====================================

if __FILE__ == $0
  mbtg = MauveBackboneToGrimm.new(ARGV)
  
  mbtg.run!
end