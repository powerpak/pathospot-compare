library(ape)
args = commandArgs(trailingOnly = TRUE)

if (length(args) < 1) { 
  stop("You must specify the name of the tree file as the first argument.")
}

my_tree <- read.tree(file=args[1])
out_pdf <- if(length(args) > 1) args[2] else paste(args[1], ".pdf", sep="")

pdf(out_pdf, width=7, height=5)
plot(my_tree)