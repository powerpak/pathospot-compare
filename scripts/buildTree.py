import sys
sys.path.append("/sc/orga/projects/InfectiousDisease/tools/anaconda_ete/bin/")
from ete3 import *
from draw_coloured_tree import *

bestTree=sys.argv[1]
nodeLabelledTree=sys.argv[2]
outfile=sys.argv[3]
#labels=sys.argv[4]
#t=Tree("test_ete_tree.txt")
t1=Tree(bestTree)
#ancestor=t.get_common_ancestor()
t=Tree(nodeLabelledTree)
#t.set_outgroup("ER03544_3B")
#t.unrooted=True
ts=TreeStyle()
ts.show_leaf_name=True
#ts.show_branch_length=True
#ts.show_branch_support=True
#for node in t1.traverse("postorder"):
#    print node.support
#    print node.name
leaves=t.get_leaves()
nodeDict={}
for node in leaves:
    i=0
#    node1=node.up
    while node:
        if(node.is_leaf()):
            nodeDict[node.name]=node.dist
            leaf_name=node.name
#            print node.name+" "+str(int(node.dist))
        else:
            nodeDict[leaf_name+"_"+str(i)]=node.dist
            i+=1
#            print str(int(node.support))+" "+str(int(node.dist))
        node=node.up
#print nodeDict
leaves1=t1.get_leaves()
nodeDict1={}
visited=[]
for node1 in leaves1:
    i=0
    while node1:
        if(node1.is_leaf()):
            node1.add_face(TextFace(nodeDict[node1.name]),column=0, position="branch-top")
#            print nodeDict[node1.name]
  #          nodeDict1[node1.name]=node1.dist
            leaf_name1=node1.name
        elif node1 not in visited:
            node1.add_face(TextFace(nodeDict[leaf_name1+"_"+str(i)]), column=0, position="branch-top")
 #           print nodeDict[leaf_name1+"_"+str(i)]
            i+=1
            visited.append(node1)
        node1=node1.up
#print nodeDict1
#for node1 in t.traverse("postorder"):
#    if(node1.support>1):
#        print str(int(node1.support))+" "+str(int(node1.dist))
#    else:
#        print str(node1.name)+" "+str(int(node1.dist))
#    for node1 in t.traverse("postorder"):
#        node1.add_face(TextFace(node.dist),column=0, position="branch-top")
ts.branch_vertical_margin=10
ts.arc_start=-180
ts.arc_span=180
#ts.force_topology=True
#ts.mode="c"
#t1.render("test_tree10.png", w=1830,h=1830,tree_style=ts)
draw_tree(t1,"T","F", outfile)
