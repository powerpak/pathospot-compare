library(gplots)
args <- commandArgs(TRUE)
dir<-args[1]
print(dir)
setwd(dir)
motmat<-read.table("motif_matrix.csv",sep=",",header=T)
motmat<-motmat[,-2]
a<-ncol(motmat)
motmat[,a] <- gsub("]", "", motmat[,a])
df<-data.matrix(motmat)
rownames(df)<-motmat$id
df<-df[,-c(1)]
tree_order<-read.table("tree_order.txt",header=F)

tree_order<-tree_order[tree_order$V1 %in% rownames(df), ]
iso_id<-as.character(tree_order$V1)
mlst<-as.character(tree_order$V2)


colfunc <- colorRampPalette(c("black", "white"))

pdf("motif_heatmap_no_singletons_raw.pdf", width=9, height=8)
#remove singletons
df2 = df[,colSums(df) > 1]
my_palette <- colorRampPalette(c("lightgrey","cornflowerblue"))
motif_hm<-heatmap.2(df2[iso_id,],col=my_palette,,margins=c(12,8),Rowv=FALSE,Colv=TRUE,dendrogram='column',trace="none",RowSideColors=as.character(as.numeric(mlst)))
legend("bottomleft",      
    legend = unique(as.numeric(mlst)),
    col = unique(as.numeric(mlst)), 
    lty= 1,             
    lwd = 5,           
    cex=.7
    )

dev.off()

pdf("motif_heatmap_with_singletons_raw.pdf", width=9, height=8)
my_palette <- colorRampPalette(c("lightgrey","cornflowerblue"))
motif_hm<-heatmap.2(df[iso_id,],col=my_palette,,margins=c(12,8),Rowv=FALSE,Colv=TRUE,dendrogram='column',trace="none",RowSideColors=as.character(as.numeric(mlst)))
legend("bottomleft",
    legend = unique(as.numeric(mlst)),
    col = unique(as.numeric(mlst)),
    lty= 1,
    lwd = 5,
    cex=.7
)
dev.off()


