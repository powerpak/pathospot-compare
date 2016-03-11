#!/usr/bin/env python
# draw_coloured_tree.py   Written by: Mitchell Sullivan   mjsull@gmail.com
# organisation: Icahn School of Medicine - Mount Sinai
# Version 0.0.1 2016.01.19
# License: GPLv3

from ete3 import Tree
import sys
from ete3 import NodeStyle
from ete3 import TreeStyle


# take a hue, saturation and lightness value and return a RGB hex string
def hsl_to_str(h, s, l):
    c = (1 - abs(2*l - 1)) * s
    x = c * (1 - abs(h *1.0 / 60 % 2 - 1))
    m = l - c/2
    if h < 60:
        r, g, b = c + m, x + m, 0 + m
    elif h < 120:
        r, g, b = x + m, c+ m, 0 + m
    elif h < 180:
        r, g, b = 0 + m, c + m, x + m
    elif h < 240:
        r, g, b, = 0 + m, x + m, c + m
    elif h < 300:
        r, g, b, = x + m, 0 + m, c + m
    else:
        r, g, b, = c + m, 0 + m, x + m
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    return "#%x%x%x" % (r/16,g/16,b/16)

# main function for drawing tree
def draw_tree(t, colour, label, out_file):
#    t = Tree(the_tree)
    o = t.get_midpoint_outgroup()
    t.set_outgroup(o)
    the_leaves = []
    for leaves in t.iter_leaves():
        the_leaves.append(leaves)
    groups = {}
    num = 0
    # set cutoff value for clades as 1/20th of the distance between the furthest two branches
    clade_cutoff = t.get_distance(the_leaves[0], the_leaves[-1]) /20
    # assign nodes to groups
    last_node = None
    for node in the_leaves:
        i = node.name
        if not last_node is None:
            if t.get_distance(node, last_node) <= clade_cutoff:
                groups[group_num].append(i)
            else:
                groups[num] = [num, i]
                group_num = num
                num += 1
        else:
            groups[num] = [num, i]
            group_num = num
            num += 1
        last_node = node

    ca_list = []
    # Colour each group and then get the common ancestor node of each group
    if colour:
        for i in groups:
            num = groups[i][0]
            h = num * 360/len(groups)
            the_col = hsl_to_str(h, 0.5, 0.5)
            style = NodeStyle()
            style['size'] = 0
            style["vt_line_color"] = the_col
            style["hz_line_color"] = the_col
            style["vt_line_width"] = 2
            style["hz_line_width"] = 2
            if len(groups[i]) == 2:
                ca = t.search_nodes(name=groups[i][1])[0]
                ca.set_style(style)
            else:
                ca = t.get_common_ancestor(groups[i][1:])
                ca.set_style(style)
                tocolor = []
                for j in ca.children:
                    tocolor.append(j)
                while len(tocolor) > 0:
                    x = tocolor.pop(0)
                    x.set_style(style)
                    for j in x.children:
                        tocolor.append(j)
            ca_list.append((ca, h))
        # for each common ancestor node get it's closest common ancestor neighbour and find the common ancestor of those two nodes
        # colour the common ancestor then add it to the group - continue until only the root node is left
        while len(ca_list) > 1 and len(ca_list)<20:
            distance = float('inf')
            for i, col1 in ca_list:
                for j, col2 in ca_list:
                    if not i is j:
                        parent = t.get_common_ancestor(i, j)
                        getit = True
                        for children in parent.children:
                            if children != i and children != j:
                                getit = False
                                break
                        if getit:
                            the_dist = t.get_distance(i, j)
                            if the_dist <= distance:
                                distance = the_dist
                                the_i = i
                                the_j = j
                                the_i_col = col1
                                the_j_col = col2
#            print (the_i, the_i_col)
#            print ca_list
#            if((the_i, the_i_col) in ca_list and (the_j, the_j_col) in ca_list):
            if((the_i, the_i_col) in ca_list):
                ca_list.remove((the_i, the_i_col))
            if((the_j, the_j_col) in ca_list):
                ca_list.remove((the_j, the_j_col))
            new_col = (the_i_col + the_j_col) / 2
            new_node = t.get_common_ancestor(the_i, the_j)
            the_col = hsl_to_str(new_col, 0.5, 0.3)
            style = NodeStyle()
            style['size'] = 0
            style["vt_line_color"] = the_col
            style["hz_line_color"] = the_col
            style["vt_line_width"] = 2
            style["hz_line_width"] = 2
            new_node.set_style(style)
            ca_list.append((new_node, new_col))
    # if you just want a black tree
    else:
        style = NodeStyle()
        style['size'] = 0
        style["vt_line_color"] = '#000000'
        style["hz_line_color"] = '#000000'
        style["vt_line_width"] = 1
        style["hz_line_width"] = 1
        for n in t.traverse():
            n.set_style(style)
    ts = TreeStyle()
    # Set these to False if you don't want bootstrap/distance values
#    ts.show_branch_length = label
#    ts.show_branch_support = label
    ts.show_branch_length=False
    ts.show_branch_support=False
    ts.margin_left = 20
    ts.margin_right = 100
    ts.margin_top = 20
    ts.margin_bottom = 20
    t.render(out_file, w=210, units='mm', tree_style=ts)

#if len(sys.argv) != 5:
#    sys.stdout.write('''#####################################################################
#draw_coloured_tree.py written by Mitchell Sullivan (mjsull@gmail.com)
#####################################################################

#USAGE: draw_coloured_tree.py <tree.nw> <colour> <label> <out_file>

#where <tree.nw> is an unrooted newick tree.
#<colour> is T if you want the tree coloured or F if you want a Black and white tree.
#<label> is T if you want bootstrap and distance values to be shown or F if you don't want them displayed
#and <outfile> is the filename for the output - valid formats are PNG, PDF and SVG
#format will be determined by file suffix (i.e. .png .pdf or .svg)
#''')
#    sys.exit()

#draw_tree(sys.argv[1], sys.argv[2] != 'F', sys.argv[3] != 'F', sys.argv[4])
