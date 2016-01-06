library(gplots)
motmat<-read.table("motif_matrix.csv",sep=",",header=T)
df<-data.matrix(motmat)
rownames(df)<-motmat$id
df<-df[,-1]
tree_order<-read.table("tree_order.txt",header=F)
tree_order<-as.character(tree_order$V1)
pdf("motif_heatmap.pdf", width=9, height=8)
motif_hm<-heatmap.2(df[tree_order,],trace="none",col=greenred(10),margins=c(12,8),Rowv=FALSE,Colv=TRUE,dendrogram='column')
dev.off()
