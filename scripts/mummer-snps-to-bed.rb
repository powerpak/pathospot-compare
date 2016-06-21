#!/usr/bin/env ruby

require 'pp'

class MummerSnpsToBed
  
  HELP = <<-EOT

Usage: #{$0} in.snps [out.grimm]

Transcodes a .snps file as produced by MUMmer's show-snps tool into a BED track that 
can be displayed against the reference (not query!) genome.

IMPORTANT: The expected flags when running show-snps are: -IHTClr. This produces 
headerless, tab-delimited output with sequence length information included and indels
excluded.

For details on all the steps leading up to calling SNPs with MUMmer, and how 
various options for show-snps change its output, please refer to:

http://mummer.sourceforge.net/manual/#snpdetection
EOT

  NT_COLORS = {A:'255,0,0', T:'255,0,255', C:'0,0,255', G:'0,255,0'}
  
  def initialize(args)
    if args.size < 1
      puts "FATAL: #{$0} requires a .snps file produced by MUMmer's show-snps tool as its first argument"
      abort HELP
    end
    
    @snps_path = args.first
    @in = File.new(@snps_path) rescue abort("FATAL: Could not open #{@snps_path}")
    @out = STDOUT
  end
  
  def run!
    track_name = File.basename(@snps_path).sub(/\.\w+$/, '')
    @out.puts "track name=\"#{track_name}_snv\" description=\"SNPs called by MUMmer\" itemRgb=\"on\""
    
    @in.each_line do |line|
      # Each line of show-snps output is tab-delimited with the columns as follows:
      #   0) reference pos
      #   1) reference nt
      #   2) query nt
      #   3) query pos
      #   4) distance to nearest mismatch
      #   5) distance to nearest contig edge
      #   6) reference contig length
      #   7) query contig length
      #   8) reference sequence direction
      #   9) query sequence direction
      #   10) reference contig name
      #   11) query contig name
      row = line.split("\t")
      left = row[0].to_i
      desc = "#{row[1]} > #{row[2]}"
      item_rgb = NT_COLORS[row[2]]
      
      # All we have to do is simply translate this to the BED columns, which are defined here:
      # https://genome.ucsc.edu/FAQ/FAQformat.html#format1. The typical layout is:
      #
      # chrom, chromStart, chromEnd, name, score, strand, thickStart, thickEnd, itemRgb
      #
      # NOTE: BED uses 0-based coordinates, while show-snps outputs 1-based coordinates.
      @out.puts [row[10], left - 1, left, desc, '0', '+', left - 1, left, item_rgb].join("\t")
    end
  end
  
end


# =====================================
# = If this script is called directly =
# =====================================

if __FILE__ == $0
  mstb = MummerSnpsToBed.new(ARGV)
  
  mstb.run!
end