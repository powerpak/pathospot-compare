#!/bin/bash 
TAG=$1
echo "
<p>Core Genome Sizes</p>
<div id="list">
  <p><iframe src=""$TAG"_Lengths.txt" frameborder="0" height="200"
      width="95%"></iframe></p>
</div>
<p>ETE SNP Tree</p>
<img src=""$TAG"_ete_tree.png">
<p></p>
<a href=""$TAG"_ete_tree.pdf">SNP tree as PDF</a></li>" >> index.html

