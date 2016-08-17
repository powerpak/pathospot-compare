FOFN=$1
#PKEEP=$2
PKEEP=0.5
OUT=$3
python make_motif_matrix.py ${FOFN} ${PKEEP} ${OUT}
Rscript make_motif_heatmap.R ${OUT}
