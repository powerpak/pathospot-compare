require 'bio'
require 'tmpdir'
require 'shellwords'
require 'set'
require 'fileutils'

def filter_fasta_by_entry_id(in_path, out_path, regexp=/_[gm]_/, opts={})
  in_file = Bio::FlatFile.open(Bio::FastaFormat, in_path)
  invert = !!opts[:invert]
  matching_contigs = 0
  contig_count = 0
  
  File.open(out_path, 'w') do |out_file|
    in_file.each_entry do |entry|
      if invert ^ regexp.match(entry.entry_id)
        out_file.puts(entry.seq.to_fasta(entry.entry_id, 60))
        matching_contigs += 1
      end
      contig_count += 1
    end
  end
  
  [matching_contigs, contig_count]
end

def find_repeats_with_mummer(fasta_path)
  repeat_mask = {}
  start_reading = false
  Dir.mktmpdir do |tmp|
    system <<-SH
      module load mummer/3.23
      nucmer --maxmatch --nosimplify --prefix #{tmp}/repeats \
          #{Shellwords.escape(fasta_path)} #{Shellwords.escape(fasta_path)}
      show-coords #{tmp}/repeats.delta > #{tmp}/repeats.coords
    SH
    File.open("#{tmp}/repeats.coords", 'r').each_line do |line|
      if line =~ /^==========/ then start_reading = true; next; end
      next unless start_reading
      vals = line.strip.split(/[\s|]+/)
      start1, end1, start2, end2 = vals[0..3].map{|v| v.to_i }
      query_contig, subject_contig = vals[7..8]
      repeat_mask[query_contig] ||= Set.new
      repeat_mask[subject_contig] ||= Set.new
      if (start1 != start2 || end1 != end2) && query_contig == subject_contig
        # Store all (0-based) positions that matched a repeat sequence within the same contig
        repeat_mask[query_contig].merge((start1 - 1)...end1)
        repeat_mask[query_contig].merge((start2 - 1)...end2)
      end
    end
  end
  repeat_mask
end

def fasta_mask_repeats(in_path, out_path)
  repeat_mask = find_repeats_with_mummer(in_path)
  in_file = Bio::FlatFile.open(Bio::FastaFormat, in_path)
  
  File.open(out_path, 'w') do |out_file|
    in_file.each_entry do |entry|
      if repeat_mask.include?(entry.entry_id)
        # Masking is done by contiguous ranges, not characterwise, to save on thrashing memory
        start_mask = nil
        end_mask = nil
        repeat_mask[entry.entry_id].to_a.sort.each do |pos|
          start_mask ||= pos
          # Everytime we skip to another contiguous range of the contig, mask the last range
          if end_mask && pos != end_mask + 1
            entry.seq[start_mask..end_mask] = 'n' * (end_mask - start_mask + 1)
            start_mask = pos
          end
          end_mask = pos
        end
        # Mask the very last range
        entry.seq[start_mask..end_mask] = 'n' * (end_mask - start_mask + 1) if start_mask
      end
      out_file.puts(entry.seq.to_fasta(entry.entry_id, 60))
    end
  end
end