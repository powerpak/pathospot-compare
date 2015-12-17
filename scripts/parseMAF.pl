use lib("/sc/orga/work/attieo02/Getopt-ArgParse-1.0.6/blib/lib/", "/sc/orga/work/attieo02/Moo-2.000002/blib/lib/", "/sc/orga/work/attieo02/Module-Runtime-0.014/blib/lib/", "/sc/orga/work/attieo02/Devel-GlobalDestruction-0.13/blib/lib/", "/sc/orga/work/attieo02/Sub-Exporter-Progressive-0.001011/blib/lib/");
use Getopt::ArgParse;
$ap=Getopt::ArgParse->new_parser(
    prog=>'extractSequencesFromMAF.pl',
    description=>'Extracts sequences from MAF file',
    epilog=>' ');
$ap->add_arg('--file', '-f', required=>1, help=>'Input file');
$ap->add_arg('--number', '-n', required=>1, help=>'Number of strains');
$args=$ap->parse_args();
$file=$args->file;
$number=$args->number;
#my $file=shift @ARGV;
#my $number=shift @ARGV;
open(FH, $file);
my $i=0;
my $mult_flag;
while(<FH>){
    if(/^a/){
	my @data1=split;
	if($data1[3] eq "mult=".$number){
	    $i++;
	    $mult_flag=1;
	}else{
	    $mult_flag=0;
	}
    }
    if(/^s/&&$mult_flag){
	my @data=split;
	my @data2=split(/\./, $data[1]);
#	print $data2[0]."\n";
        $seq{$data2[0]}{$i}=$data[6];
#	$start{$data[1]}{$i}=$data[2];
#	$length{$data[1]}{$i}=$data[3];
    }
}

    foreach $data(keys %seq){
	for(my $j=0; $j<$i; $j++){
        $Seq{$data}.=$seq{$data}{$j};
    }
}
foreach $data(keys %Seq){
    print ">".$data."\n";
    print $Seq{$data}."\n";
}
