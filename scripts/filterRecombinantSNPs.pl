#my $file=shift @ARGV;
my $vcf_file=shift @ARGV;
my %block;
for(my $i=1; $i<=5; $i++){
open(FH, "/sc/orga/projects/InfectiousDisease/studies/investigation_VRE-outbreak_2014/illumina/Sample_VRE".$i."/VRE_".$i."_Recombination.txt");
while(<FH>){
    chomp;
    if($_=~/^\d+:\d/){
	my @data=split(/\:/, $_);
	if($data[1]==0.0){
	    $block{$data[0]}=1;
    }
}
}
close(FH);
}
for(my $i=7; $i<=10; $i++){
    open(FH, "/sc/orga/projects/InfectiousDisease/studies/investigation_VRE-outbreak_2014/illumina/Sample_VRE".$i."/VRE_".$i."_Recombination.txt");
    while(<FH>){
	chomp;
	if($_=~/^\d+:\d/){
	    my @data=split(/\:/, $_);
	    if($data[1]==0.0){
		$block{$data[0]}=1;
	    }
	}
    }
    close(FH);
}
open(FH, "/sc/orga/projects/InfectiousDisease/studies/investigation_VRE-outbreak_2014/illumina/Sample_VRE12/VRE_12_Recombination.txt");
while(<FH>){
    chomp;
    if($_=~/^d+:\d/){
	my @data=split(/\:/, $_);
	if($data[1]==0.0){
	    $block{$data[0]}=1;
	    }
	}
    }
close(FH);
my @regions=sort{$a<=>$b}(keys %block);
#for(my $i=0; $i<@regions; $i++){
#    print $regions[$i]."\n";
#}
open(FH1, $vcf_file);
while(<FH1>){
    if(/^#/){
    }else{
	my @data=split;
	for(my $i=0; $i<@regions; $i++){
	    if($data[1]<=1000*($regions[$i]+1)&&($data[1]>=1000*$regions[$i])){
		$flag{$data[1]}=1;
	    }
	   
	}
	if($flag{$data[1]}){
	}else{
	    print $data[1]." ".$data[3]." ".$data[4]."\n";
	}
    }
}
