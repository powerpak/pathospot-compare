use lib("/hpc/users/attieo02/", "../");
use strict;
use common_util::generic::FastaReader;
my $fr=common_util::generic::FastaReader->new();
my $file=shift @ARGV;
$fr->init_file($file);
my $i=0;
my $total_length=0;
while(my ($P_defn, $P_body)=$fr->next()){
    $i++;
    print $$P_defn." ".length($$P_body)."\n";
    $total_length+=length($$P_body);
}
print $total_length."\n";
