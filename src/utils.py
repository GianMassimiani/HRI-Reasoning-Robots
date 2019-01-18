import os
import sys
from graphviz import Digraph

LTLMOP_SLURP_DIR = os.path.abspath("../LTLMoP/src/etc/SLURP")

sys.path.append(LTLMOP_SLURP_DIR)

#imports from SLURP
from semantics.tree import Tree

#LIBRARY OF USEFUL FUNCTIONS

def print_tree_to_png(g, queue=[], ID=0):
	"""
	Print a parse tree to .png using Graphviz.
	
	:param g:	    instance of Graphviz graph
	:param queue:	a list containing an instance of Tree
	:param ID:	where to start in the tree (usually the root, i.e. 0)
	"""

	if not isinstance(queue[0], Tree):
		raise Exception("Tree must be an instance of Tree class. See " + LTLMOP_SLURP_DIR +\
						"/semantics/tree.py")
	try:
		item = queue[ID]
		if ID == 0:
			g.node(str(ID), label = item.node)
	except IndexError:
		return # end of queue, done with printing

	# if item is terminal symbol (i.e. a leaf)
	if not isinstance(item, Tree):
		# skip item
		print_tree_to_png(g, queue, ID+1)
	else:
		child_ID = len(queue)
		for child in item:
			queue.append(child)

			if not isinstance(child, Tree):
				g.node(str(child_ID), label=child, color='blue')
			else:
				g.node(str(child_ID), label=child.node)
			g.edge(str(ID), str(child_ID))
			child_ID += 1

		print_tree_to_png(g, queue, ID+1)