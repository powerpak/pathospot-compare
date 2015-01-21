require 'bio'
require 'shellwords'

########
#
# IMPORTANT: nucmer, delta-filter, and show-snps from MUMmer 3.23 must be on PATH before running this
# On Minerva, this should be as easy as module load mummer/3.23
#
########

def nucmerSNPs(fa_ref, fa_query, prefix)
  fa_ref = Shellwords.escape(fa_ref)
  fa_query = Shellwords.escape(fa_query)
  
  system <<-SH
    nucmer -p #{prefix} #{fa_ref} #{fa_query}
    delta-filter -lr #{prefix}.delta > #{prefix}_df1.delta
  SH
  nucmer_output = `show-snps -Clr #{prefix}_df1.delta`
  nucmer_output.split("\n")
end