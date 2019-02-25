#!/usr/bin/env python
"""
cleanup_parsnp_newick.py
Takes a .nwk file produced by parsnp and cleans up the leaf labels
If [regex] is given, will also delete all [regex] matches from leaf labels

USAGE: python cleanup_parsnp_newick.py parsnp.nwk output.nwk [regex]
"""

import sys
import re
from ete3 import Tree

if len(sys.argv) < 3:
    print __doc__
    sys.exit(1)

t = Tree(sys.argv[1])
for leaf in t.get_leaves():
    leaf.name = re.sub(r'(\.\w+)+$', '', leaf.name.strip("'"))
    if len(sys.argv) >= 4:
        leaf.name = re.sub(sys.argv[3], '', leaf.name)

t.write(format=0, outfile=sys.argv[2])