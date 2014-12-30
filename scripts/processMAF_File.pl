# This file needs major cleanup, but in so many lines, 
# it converts a MAF (multiple sequence alignment file)
# into a multisequence FASTA file.

my $file=shift @ARGV;
my $no_strains;
open(FH, $file);
my $i=0;
my $k=0;
my $n=0;
while(<FH>){
    if(/^a/ && $k==0){
	my @data1=split;
	$data1[3]=~s/mult=//;
	$no_strains=$data1[3];
#	print $no_strains."\n";
	$k++;
    }
    if(/^s/){
	my @data=split;
#	print $data[0];
#	print $data[6];
	for(my $j=0; $j<$no_strains; $j++){
	if($i%$no_strains==$j){
	    $variant[$j][$n]=$data[6];
	    $variant_name[$j][$n]=$data[1];
	}
#	if($i%14==1){
#	    push(@variant2, $data[6]);
#	    push(@variant2_name, $data[1]);
#	}
#	if($i%14==2){
#	    push(@variant3, $data[6]);
#	    push(@variant3_name, $data[1]);
#	}
#	if($i%14==3){
#	    push(@variant4, $data[6]);
#	    push(@variant4_name, $data[1]);
#	}
#	if($i%14==4){
#	    push(@variant5, $data[6]);
#	    push(@variant5_name, $data[1]);
#	}
#	if($i%14==5){
#	    push(@variant6, $data[6]);
#	    push(@variant6_name, $data[1]);
#	}
#	if($i%14==6){
#	    push(@variant7, $data[6]);
#	    push(@variant7_name, $data[1]);
#	}
#	if($i%14==7){
#	    push(@variant8, $data[6]);
#	    push(@variant8_name, $data[1]);
#	}
#	if($i%14==8){
#	    push(@variant9, $data[6]);
#	    push(@variant9_name, $data[1]);
#	}
#	if($i%14==9){
#	    push(@variant10, $data[6]);
#	    push(@variant10_name, $data[1]);
#	}
#	if($i%14==10){
#	    push(@variant11, $data[6]);
#	    push(@variant11_name, $data[1]);
#	}
#	if($i%14==11){
#	    push(@variant12, $data[6]);
#	    push(@variant12_name, $data[1]);
#	}
#	if($i%14==12){
#	    push(@variant13, $data[6]);
#	    push(@variant13_name, $data[1]);
#	}
#	if($i%14==13){
#	    push(@variant14, $data[6]);
#	    push(@variant14_name, $data[1]);
#	}



	}
	$i++;
	if($i%$no_strains==0){
	    $n++;
	}

#	print $data[0]." ".$data[1]." ".$data[2]." ".$data[3]." ".$data[5]." ".length($data[6])."\n";
    }
}
$no_blocks=$n;
#print $no_strains." ".$no_blocks."\n";
#    for(my $i=0; $i<$no_blocks; $i++){
#for(my $j=0; $j<$no_strains; $j++){
#	print $i." ".$j." ".length($variant[$j][$i])."\n";
#    }
#}
#	my @data=split;
#	print $data[0]." ".$data[1]." ".$data[2]." ".$data[3]." ".$data[5]." ".length($data[6])."\n";
#    }
#}
for(my $i=0; $i<$no_blocks; $i++){
    $flag[$i]=1;
}
for(my $j=0; $j<$no_strains; $j++){
    for(my $i=0; $i<$no_blocks; $i++){
	if(length($variant[0][$i])==length($variant[$j][$i])){
#	    print "Agree:".length($variant[0][$i])."\n";
	    $flag[$i]*=1;
	}else{
	    $flag[$i]*=0;
#	    print "Disagree:".length($variant[0][$i])." ".length($variant[$j][$i])."\n";
	}
    }
}

for(my $i=0; $i<$no_blocks; $i++){
   if($flag[$i]){
for(my $j=0; $j<$no_strains; $j++){
	$variant_seq[$j].=$variant[$j][$i];
    }
}
}
for(my $j=0; $j<$no_strains; $j++){
print ">".$variant_name[$j][0]."\n";
print $variant_seq[$j]."\n";
#print ">".$variant2_name[0]."\n";
#print $variant2_seq."\n";
#print ">".$variant3_name[0]."\n";
#print $variant3_seq."\n";
#    print ">".$variant4_name[0]."\n";
#    print $variant4_seq."\n";
#   print ">".$variant5_name[0]."\n";
#   print $variant5_seq."\n";
#print ">".$variant6_name[0]."\n";
#print $variant6_seq."\n";
#print ">".$variant7_name[0]."\n";
#print $variant7_seq."\n";
#print ">".$variant8_name[0]."\n";
#print $variant8_seq."\n";
#print ">".$variant9_name[0]."\n";
#print $variant9_seq."\n";
#print ">".$variant10_name[0]."\n";
#print $variant10_seq."\n";
#print ">".$variant11_name[0]."\n";
#print $variant11_seq."\n";
#print ">".$variant12_name[0]."\n";
#print $variant12_seq."\n";
#print ">".$variant13_name[0]."\n";
#print $variant13_seq."\n";
#print ">".$variant14_name[0]."\n";
#print $variant14_seq."\n";
}
