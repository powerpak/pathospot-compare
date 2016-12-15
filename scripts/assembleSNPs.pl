my %mutation;
my %reference;
my %seq;
for(my $i=2; $i<=5; $i++){
    open(FH, "illumina/Sample_VRE".$i."/VRE_".$i."_Aus0004.snps");
    while(<FH>){
	my @data=split;
	if($data[1]=~/[ACGT]/){
	$mutation{$data[0]}{$i}=$data[2];
	$reference{$data[0]}=$data[1];
	}
    }
    close(FH);
}
for(my $i=7; $i<=10; $i++){
    open(FH, "illumina/Sample_VRE".$i."/VRE_".$i."_Aus0004.snps");
    while(<FH>){
	my @data=split;
	    if($data[2] eq "A\,T"){
		$data[2]="A";
	    }
	    if($data[2] eq "C\,T"){
		$data[2]="C";
	    }
	if($data[1]=~/[ACGT]/){
	    $mutation{$data[0]}{$i}=$data[2];
	    $reference{$data[0]}=$data[1];
	}
    }
    close(FH);
}
open(FH, "illumina/Sample_VRE12/VRE_12_Aus0004.snps");
while(<FH>){
    my @data=split;
    if($data[1]=~/[ACGT]/){
	$mutation{$data[0]}{12}=$data[2];
	$reference{$data[0]}=$data[1];
    }
}
close(FH);
my @sorted_positions=sort{$a<=>$b}(keys %mutation);
foreach $position(@sorted_positions){
#    if($mutation{$position}{8} && $mutation{$position}{7}){
#	print $position." ".$mutation{$position}{8}." ".$mutation{$position}{7}."\n";
#    }elsif($mutation{$position}{8} && !$mutation{$position}{7}){
#	    print $position." ".$mutation{$position}{8}." ".$reference{$position}."\n";
#    }elsif(!$mutaton{$position}{8} && $mutation{$position}{8}){
#	print $position." ".$reference{$position}." ".$mutation{$position}{7}."\n";
#    }else{
#	print $position." ".$reference{$position}." ".$reference{$position}."\n";
#    }


    for(my $i=2; $i<=5; $i++){
	if($mutation{$position}{$i}){
	    $seq{$i}.=$mutation{$position}{$i};
	}else{
	    $seq{$i}.=$reference{$position};
	}
    }
    for(my $i=7; $i<=10; $i++){
	if($mutation{$position}{$i}){
	    $seq{$i}.=$mutation{$position}{$i};
	}else{
	    $seq{$i}.=$reference{$position};
	}
    }
    if($mutation{$position}{12}){
	$seq{12}.=$mutation{$position}{12};
    }else{
	$seq{12}.=$reference{$position};
    }
}
for(my $i=2; $i<=5; $i++){
    print ">VRE_".$i."_SNPs\n";
    print $seq{$i}."\n";
}
for(my $i=7; $i<=10; $i++){
    print ">VRE_".$i."_SNPs\n";
    print $seq{$i}."\n";
}
print ">VRE_12_SNPs\n";
print $seq{12}."\n";
