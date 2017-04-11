require 'bio'

def filter_fasta(in_path, out_path, regexp=/_[gm]_/, opts={})
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
