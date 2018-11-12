import sys
import re
from ete3 import Tree

USAGE = """
cleanup_parsnp_newick.py
Takes a .nwk file produced by parsnp and cleans up the leaf labels

USAGE: python cleanup_parsnp_newick.py parsnp.nwk output.nwk
"""

if len(sys.argv) < 3:
    print USAGE
    sys.exit(1)

t = Tree(sys.argv[1])
for leaf in t.get_leaves():
    leaf.name = re.sub(r'(\.\w+)+$', '', leaf.name.strip("'"))

t.write(format=0, outfile=sys.argv[2])