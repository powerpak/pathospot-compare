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


# 20 colors that are used to distinguish paired items in the BED output

COL_20 = ['31,119,180' , '255,127,14' , '44,160,44'  , '214,39,40'  , '148,103,189',
          '140,86,75'  , '227,119,194', '127,127,127', '188,189,34' , '23,190,207' ,
          '174,199,232', '255,187,120', '152,223,138', '255,152,150', '197,176,213',
          '196,156,148', '247,182,210', '199,199,199', '219,219,141', '158,218,229']

class MauveBackboneToGrimm
  
  def initialize(args)
    @options = {}

    opt_parser = OptionParser.new do |opts|
      opts.banner = <<-USAGE

Usage: #{$0} -f in.fofn [options] in.xmfa.backbone [out.grimm]

Transcodes a progressiveMauve .backbone file into an ordered list of numerical genes
that GRIMM can use as input. Optionally, if provided with the path to GRIMM, this
can run GRIMM, parse the output, and convert the result to other formats.

**NOTE**: this currently only processes progressiveMauve alignments between 2 genomes.

You *must* provide an -r/--ref argument pointing to the sequence for the reference
genome (seq0 in the .backbone), and a -q/--query argument pointing to the sequence
for the query genome (seq1 in the .backbone), which will be consulted for contig or
chromosome lengths allowing multichromosomal analysis of rearrangements by GRIMM.
Otherwise, the genomes would be considered to be contiguous, which is an inaccurate
assumption.


      USAGE

      opts.separator ""
      opts.separator "Required options:"
      
      opts.on("-r", "--ref [PATH]",
              "Path to the filename for seq0 (the reference genome) in the .xmfa.backbone") do |path|
        @options[:ref] = path
      end
      
      opts.on("-q", "--query [PATH]",
              "Path to the filename for seq0 (the reference genome) in the .xmfa.backbone") do |path|
        @options[:query] = path
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
    
    abort "FATAL: -r/--ref parameter is required" + opt_parser.help unless @options[:ref]
    abort "FATAL: -q/--query parameter is required" + opt_parser.help unless @options[:query]
        
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
  
  def parse_genomes
    @seqs = []
    @seq_names = []
    [@options[:ref], @options[:query]].each do |seq_path|
      chrom_sizes = []
      @seq_names << File.basename(seq_path).sub(/\.\w+$/, '')
      seq_fh = Bio::FlatFile.auto(seq_path.strip) rescue abort("FATAL: Could not open -r/--ref parameter #{@options[:ref]}")
      seq_fh.each_with_index do |entry, i| 
        chr_end = 1 + entry.naseq.size + (i > 0 ? chrom_sizes.last[:end] : 0)
        chrom_sizes << {:name => entry.definition.gsub('|', '_'), :end => chr_end}
      end
      @seqs << chrom_sizes
    end
  end
  
  # Converts a pair of 1-based genomic coordinates as [left, right] representing a right-open range
  # into a 0-based range mapped to a contig/chromosome and represented as [chr_name, left, right]
  def ref_chr_range(genome_range)
    chr_index = @seqs[0].index{|chr| chr[:end] > genome_range[0] }
    chr_index ||= @seqs[0].size - 1
    chr_start = chr_index > 0 ? @seqs[0][chr_index - 1][:end] : 1
    chr_size = @seqs[0][chr_index][:end] - chr_start
    [@seqs[0][chr_index][:name], [genome_range[0] - chr_start, 0].max, [genome_range[1] - chr_start, chr_size].min]
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
      if @seqs && row[0].abs >= @seqs[0][chr_num][:end]
        @gene_orders[0] << '$'
        chr_num += 1 until @seqs[0][chr_num][:end] > row[0].abs
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
      if @seqs && row[2].abs >= @seqs[1][chr_num][:end]
        @gene_orders[1] << '$'
        chr_num += 1 until @seqs[1][chr_num][:end] > row[2].abs
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
    fh.close
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
    
  def write_bed(bed_path = nil)
    bed_path ||= @options[:bed]
    fh = File.open(bed_path, 'w') rescue abort("FATAL: Could not open #{bed_path} for writing BED output")
    bed_tracks = collect_bed_data
    @color_i = -1
    # The BED format is tab-delimited, and defined here: https://genome.ucsc.edu/FAQ/FAQformat.html#format1
        
    fh.puts "track name=\"#{@seq_names[1]}_indels\" description=\"aligned insertions, deletions, and indels\" itemRgb=\"on\""
    {:indels => '0,0,0', :dels => '127,0,0', :inserts => '0,127,0'}.each do |type, color|
      bed_tracks[type].each do |row|
        chr_name, left, right = ref_chr_range(row[0..1])
        # chrom, chromStart, chromEnd, name, score, strand, thickStart, thickEnd, itemRgb
        fh.puts [chr_name, left, right, row[2], '0', row[3], left, right, color].join("\t")
      end
    end
        
    fh.puts "track name=\"#{@seq_names[1]}_rearrange\" description=\"aligned rearrangement points\" itemRgb=\"on\""
    bed_tracks[:rearrangements].each do |pair|
      if pair.size > 1
        # Rearrangement with two flanking regions (reversals, translocations)
        write_bed_pair(fh, pair)
      else 
        # Rearrangement with one flanking region (fission)
        chr_name, left, right = ref_chr_range(pair.first[0..1])
        # chrom, chromStart, chromEnd, name, score, strand, thickStart, thickEnd, itemRgb
        bed_line = [chr_name, left, right, pair.first[2], '0', pair.first[3], left, right, '0,0,0']
        # blockCount, blockSizes, blockStarts
        bed_line += [1, "#{pair.first[1] - pair.first[0]},", '0,']
        fh.puts bed_line.join("\t")
      end
    end
    
    fh.puts "track name=\"#{@seq_names[1]}_ambig_ins\" descripton=\"insertions that couldn't be aligned to the reference\" itemRgb=\"on\""
    bed_tracks[:ambig_inserts].each do |pair|
      write_bed_pair(fh, pair)
    end
    fh.close
  end
  
  def run!
    parse_genomes
    parse_input
    extract_genes
    write_output
    run_grimm if @options[:grimm]
    write_bed if @options[:bed]
  end
  
  private
  
  # Parses GRIMM's output into a hash of data values.
  # Rearrangements for the "optimal sequence" are parsed into an ordered array of arrays, each of the form:
  # [chr_1_num, gene_1_pos, gene_1_num, chr_2_num, gene_2_pos, gene_2_num, operation]
  def parse_grimm(grimm_output)
    @grimm_output = grimm_output
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
      next unless line =~ /^Step (\d)+:/
      next if $1.to_i == 0
      m = line.match(/Chrom. (\d+), gene (-?\d+) \[(-?\d+)\] through chrom. (\d+), gene (-?\d+) \[(-?\d+)\]:([\w ]+)/)
      @parsed[:rearrangements] << m.to_a.slice(1..-2).map(&:to_i).concat([m[-1].strip])
    end
  end
  
  # Collect all the information parsed out of the .backbone and the GRIMM output into BED track data
  # that summarizes insertions, deletions, indels, and rearrangements
  #
  # NOTE: all the regions returned by this function are RIGHT OPEN, e.g. [0, 1) is 1 base long, unlike .backbone format
  def collect_bed_data
    # First, collect all presumptive insertions.  We will want to match them with deletions to create indels where possible.
    insertions = @backbone.select{|row| row[0] == 0 && row[1] == 0 }
    # This is the form of the returned data
    bed = {
      # One array of BED data per feature
      :indels => [], :inserts => [], :dels => [], 
      # One pair of arrays of BED data (contained in their own array) per feature
      :ambig_inserts => [], :rearrangements => []
    }
    
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
      
      if prev[4] && after[4] # implies that both rows have nonzero values in all columns
        # If surrounding matches to the first genome are in the same orientation, and consecutive,
        # this is a straight up insertion that is unambiguously alignable to the first genome
        if (prev[4] < 0 == after[4] < 0) && after[4] - prev[4] == 1
          if after[4] > 0  # positive orientation
            del_size = after[0] - prev[1] - 1
            # We need to potentially adjust the second coordinate on inserts because we can't have a 0-length BED feature
            bed[:inserts] << [prev[1] + 1, [after[0], prev[1] + 2].max, "ins(#{row[3] - row[2] + 1})", '+']
          else
            del_size = prev[0].abs - after[1].abs - 1
            bed[:inserts] << [after[1].abs + 1, [prev[0].abs, after[1].abs + 2].max, "ins(#{row[3] - row[2] + 1})", '+']
          end
        else
          # No alignable match to the other genome, so it could align to either of two positions
          possible_aligns = [prev[0] < 0 ? prev[0].abs : prev[1], after[0] < 0 ? after[1].abs : after[0]]
          
          # Do we always pick one side? Dilemma
          bed[:ambig_inserts] << possible_aligns.map do |aln|
            [aln - 1, aln + 1, "ambig-#{bed[:ambig_inserts].size + 1}-ins(#{row[3] - row[2] + 1})", '+']
          end
        end
      end
    end
        
    @parsed[:rearrangements].each_with_index do |rearrange, i|
      genes = [rearrange[2], rearrange[5]].sort_by{|v| v.abs }
      
      # For the genes involved in the rearrangement, get the flanking indel/deletion region
      flank_regions = genes.each_with_index.map do |gene, j|
        backbone_row = @backbone.find{|row| row[4] == gene.abs }
        
        # Fission, fusion, and translocation events can map to non-existent gene numbers, which
        # means that they involve one of the "caps" on a contig/chromosome.
        next if !backbone_row && ['Fission', 'Fusion', 'Translocation'].include?(rearrange[6])
        raise "Invalid gene number #{rearrange.join(' ')} #{@backbone.max_by{|row| row[4] ? row[4].abs : 0}}" if !backbone_row
        
        if (gene > 0 && j == 0) || (gene < 0 && j == 1)
          # We need to look at the previous flanking region in the original gene order
          adj_indel_or_del = (bed[:indels] + bed[:dels] + bed[:inserts]).find{|row| row[1] == backbone_row[0].abs }
          # If we couldn't find one, just use the end of the gene
          adj_indel_or_del ||= [backbone_row[0].abs - 1, backbone_row[0].abs + 1]  
        else
          # Following flanking region
          adj_indel_or_del = (bed[:indels] + bed[:dels] + bed[:inserts]).find{|row| row[0] == backbone_row[1].abs + 1 }
          adj_indel_or_del ||= [backbone_row[1].abs, backbone_row[1].abs + 2]
        end
      end
      
      # Fission events can have only one flanking region.
      flank_regions.compact!
      
      bed[:rearrangements] << flank_regions.map do |flank_regions|
        [flank_regions[0], flank_regions[1], "#{rearrange[6].downcase}-#{i + 1}", '+']
      end
    end
    
    bed
  end
  
  # Writes BED rows for paired features. If on the same contig/chromosome,
  # they are represented as a single feature with blocks and an intron line connecting them;
  # otherwise, they are represented as similarly colored blocks.
  def write_bed_pair(fh, pair)
    pair.sort_by!{|p| p[0] }
    
    first = {}
    second = {}
    first[:chr], first[:left], first[:right] = ref_chr_range(pair[0])
    second[:chr], second[:left], second[:right] = ref_chr_range(pair[1])
    
    if first[:chr] == second[:chr]
      # Paired points are on the same contig/chromosome, can connect directly.
      # chrom, chromStart, chromEnd, name, score, strand, thickStart, thickEnd
      row = [first[:chr], first[:left], second[:right], pair[0][2], '0', '+', first[:left], second[:right]]
      # itemRgb, blockCount, blockSizes, blockStarts
      row += ['0,0,0', 2, [pair[0][1] - pair[0][0], pair[1][1] - pair[1][0]].join(','), [0, pair[1][0] - pair[0][0]].join(',')]
      fh.puts(row.join("\t"))
    else
      # Rearrangment points are not on the same contig/chromosome, must connect visually with same color
      color = COL_20[@color_i = (@color_i + 1) % COL_20.size]
      row = [first[:chr], first[:left], first[:right], pair[0][2], '0', pair[0][3], first[:left], first[:right]]
      row += [color, 1, "#{pair[0][1] - pair[0][0]},", '0,']
      fh.puts(row.join("\t"))
      row = [second[:chr], second[:left], second[:right], pair[1][2], '0', pair[0][3], second[:left], second[:right]]
      row += [color, 1, "#{pair[1][1] - pair[1][0]},", '0,']
      fh.puts(row.join("\t"))
    end
  end
  
end

# =====================================
# = If this script is called directly =
# =====================================

if __FILE__ == $0
  mbtg = MauveBackboneToGrimm.new(ARGV)
  
  mbtg.run!
end