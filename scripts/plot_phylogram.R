library(ape)
args = commandArgs(trailingOnly = TRUE)

if (length(args) < 1) { 
  stop("You must specify the name of the tree file as the first argument.")
}

my_tree <- read.tree(file=args[1])
out_pdf <- if(length(args) > 1) args[2] else paste(args[1], ".pdf", sep="")

pdf(out_pdf, width=9, height=5)
par(mar=c(0.2,0.2,0.2,0.2))       # Suppress any margins.

scaling <- 1
if (max(my_tree$edge.length) > 6000) {
  scaling <- max(my_tree$edge.length) / 5000
  my_tree$edge.length <- my_tree$edge.length / scaling
}

plot(my_tree)
tree_order<-my_tree$tip.label[order(.PlotPhyloEnv$last_plot.phylo$yy[1:.PlotPhyloEnv$last_plot.phylo$Ntip])]
write.table(tree_order,"tree_order.txt",quote=FALSE,row.names=FALSE,col.names=FALSE)
edgelabels(round(my_tree$edge.length * scaling, 3), adj = c(0.5, -0.25), cex=0.7, frame="none")
