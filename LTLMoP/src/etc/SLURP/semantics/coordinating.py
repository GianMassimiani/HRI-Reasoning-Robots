"""
Handles coordination in sentences by coordinating conjunctions and lists.
"""

# Copyright (C) 2013 Taylor Turpen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from semantics.treehandler import TreeHandler
from semantics.tree import Tree
import os
import sys
from _matchingExceptions import NoRightSibling, NoLeftSibling, UnlevelCCSiblings
import copy
DEBUG = False

UTILS_PATH = os.path.abspath("/home/gian/hri_project/src")
sys.path.append(UTILS_PATH)

import utils
from graphviz import Digraph
        
class Condition(object):
    """Class to extract S trees from a parent tree that contains conditional children."""
    accepted_conditions = ["SBAR-TMP","SBAR-ADV"]
    accepted_punc = [","]
    def __init__(self):
        self.th = TreeHandler()
        
    def split_on_sbar(self,tree):
        """Return the subtrees of the tree if any SBAR present"""
        cursor = [-1]
        for condition in self.accepted_conditions:
            path = self.th.leftmost_pos(tree, condition, cursor)
            if path:
                print path                
        
class Split(object):
    """Class to split a syntax tree on CCs by replacing sibling nodes of the CC with the parent."""
    validCC = ["and", "or"]
    listCC = "," 
    def __init__(self):
        self.th = TreeHandler()     
        
    def sibling_cc_path(self,ccpath,tree=None):
        """Returns the nearest appropriate sibling to ccpath given a tree (or not)
            caveat #1 finding the leftmost sibling does not require a tree, so we can easily overload this method
            caveat #2 pop_path requires the leaf so we append a meaningless -1
        """
        if tree:
            path = self.th.nearest_right_sibling(ccpath,tree)
            path[-1] += 1
        else: 
            path = self.th.nearest_left_sibling(ccpath)
            path[-1] -= 1#actual left branch
        path.append(-1)#Faking the leaf
        return path
           
    def pop_comma_and(self,tree):
        """Given a tree, pop the comma of any siblings ", and" as in "the horse, donkey, and carriage."
            Functionally they are redundant.        
        """
        prev = (0,'')
        while True:
            leaves = tree.leaves()
            for i, leaf in enumerate(leaves):
                dleaf = self.th.remove_ulid(leaf)
                if self.th.remove_ulid(prev[1]) == "," and dleaf == "and":
                    path = tree.leaf_treeposition(prev[0])
                    break
                prev = (i,leaf)
            else:
                return
            self.th.pop_path(tree,path)

    #ADDED
    def pop_comma_or(self,tree):
        """Given a tree, pop the comma of any siblings ", and" as in "the horse, donkey, and carriage."
            Functionally they are redundant.        
        """
        prev = (0,'')
        while True:
            leaves = tree.leaves()
            for i, leaf in enumerate(leaves):
                dleaf = self.th.remove_ulid(leaf)
                if self.th.remove_ulid(prev[1]) == "," and dleaf == "or":
                    path = tree.leaf_treeposition(prev[0])
                    break
                prev = (i,leaf)
            else:
                return
            self.th.pop_path(tree,path)        
        
        
    def pos_split(self,tree,pos,possibleParents=["S","VP","NP"],desiredCC="and",ccpos="CC"):
        """The strategy for this is to find the CC in the VP (like the VB in matching),
            find the nearest left or right siblings and if they are heads, pop   
            
            @input tree input tree to split on
            @input pos is the part of speech we are splitting on
            @input possibleParents are the possible phrase parents currently supported
            @input desiredCC is the lemma of the CC we are looking for
            @input ccpos is the cc part of speech we are looking for
        """
        res = []        
        cursor = [-1]
        cccount = self.num_ccs(tree,desiredCC)
        for i in range(cccount):
            ccpath = list(self.th.get_main_pos_path(tree, ccpos, -1, cursor=cursor))
            parentPhrase = self.th.which_parent(tree, ccpath, possibleParents, -1)

            parentpos = parentPhrase.split(self.th.depthdelim)[0].split(self.th.posdelim)[0]

            if parentpos == pos:                               
                left = self.sibling_cc_path(ccpath)
                right = self.sibling_cc_path(ccpath,tree=tree);
                
                #ADDED
                #if siblings of CC are NN (e.g. "Go to office1 and office2")
                #make them NP instead
                #this is needed otherwise NNs lead to bad creation of commands
                for child_pos, child in enumerate(tree[ccpath[:-2]]):
                    if child.node.split(".")[0] == "NN":
                        temp_path = ccpath[:-2]
                        temp_path.append(child_pos)
                        child_path = temp_path
                        new_child = Tree("NP-A", [child])
                        tree[child_path] = new_child

                if len(left) != len(ccpath) != len(right):
                    raise UnlevelCCSiblings
                lefttree = copy.deepcopy(tree)

                #Instead of popping, need to replace parent with correct branch 
                temp = self.th.pop_path_cc(lefttree,right,ccpath)
                if temp:
                    #If splitting on S, temp will be the parent replacement
                    lefttree = temp
                #Recurse on "," list
                lefttrees = self.pos_split(lefttree,pos,possibleParents=possibleParents,desiredCC=self.listCC,ccpos=self.listCC)

                res.extend(lefttrees) #Copy and put left branch in results and keep going
                self.th.pop_left(tree,ccpath)#Pop everything to the left of ccpath and keep looking
                #self.th.pop_path_cc(tree, left,ccpath)#Pop for real, keep looking
                cursor = [-1]
            else:
                if DEBUG: print pos,' CC: ',ccpath
                cursor = ccpath
        if len(tree) == 1:
            #Only one branch-> split on S, consume
            tree = tree[0]  
        res.append(tree)               
        return res
        
    def num_ccs(self,tree,cc):
        """
        Given a CC, return the number of appearances 
        of that CC in a given tree.
        """
        #CHANGED
        return [self.th.remove_ulid(w.lower()) in [cc] for w in tree.leaves()].count(True)

    def split_on_cc(self,tree):
        """Split on "and"...extend to other CCs later.        
        """
        self.pop_comma_and(tree)#Prepare the tree
        #CHANGED
        numCCs = 0
        for cc in self.validCC:
            numCCs += self.num_ccs(tree, cc)

        if numCCs < 1:
            return [tree]

        self.th.depth_ulid_augment(tree, 0)
        
        try:        
            ssplit = self.pos_split(tree,"S",desiredCC=self.validCC[1])
            #for s in ssplit: self.th.append_period(s)
            vpSplit = [self.pos_split(v,"VP",desiredCC=self.validCC[1]) for v in ssplit]
            vpSplit = [item for sublist in vpSplit for item in sublist]#Flatten list
            npSplit = [self.pos_split(s,"NP",desiredCC=self.validCC[1]) for s in vpSplit]
            flatSplit = [item for sublist in npSplit for item in sublist]#Flatten list
        except NoRightSibling:
            sys.stderr.write("No right sibling found for tree on CC, should be impossible. Check parse.")
            raise
        except NoLeftSibling:
            sys.stderr.write("No left sibling found for tree on CC, should be impossible. Check parse.")
            raise        
        except UnlevelCCSiblings:
            sys.stderr.write("Unlevel CC parse. Check parse.")
            raise
        for item in flatSplit: self.th.depth_ulid_deaugment(item)

        return flatSplit

    #ADDED
    def split_on_cc(self, tree, cc):
        """Split tree on given cc."""
        if cc == "and":
            self.pop_comma_and(tree)
        elif cc == "or":
            self.pop_comma_or(tree)
        else:
            raise Exception("Cannot split on {}: conjunction not supported.".format(cc))

        #DEBUG
        """
        g1 = Digraph(format='png')
        utils.print_tree_to_png(g1, [tree])
        g1.render("/home/gian/hri_project/graphs/test/before.gv")
        """

        numCCs = self.num_ccs(tree, cc)

        if numCCs < 1:
            return [tree]

        self.th.depth_ulid_augment(tree, 0)
        
        try:        
            ssplit = self.pos_split(tree,"S",desiredCC=cc)

            #DEBUG
            """
            for i, item in enumerate(ssplit): 
                self.th.depth_ulid_deaugment(item)
                g2 = Digraph(format='png')
                utils.print_tree_to_png(g2, [item])
                g2.render("/home/gian/hri_project/graphs/test/ssplit{}.gv".format(str(i)))
            """

            #for s in ssplit: self.th.append_period(s)
            vpSplit = [self.pos_split(v,"VP",desiredCC=cc) for v in ssplit]
            
            #DEBUG
            """
            for item in vpSplit:
                for i, t in enumerate(item): 
                    self.th.depth_ulid_deaugment(t)
                    g3 = Digraph(format='png')
                    utils.print_tree_to_png(g3, [t])
                    g3.render("/home/gian/hri_project/graphs/test/vpsplit{}.gv".format(str(i)))
            """

            vpSplit = [item for sublist in vpSplit for item in sublist]#Flatten list
            npSplit = [self.pos_split(s,"NP",desiredCC=cc) for s in vpSplit]
            flatSplit = [item for sublist in npSplit for item in sublist]#Flatten list
        except NoRightSibling:
            sys.stderr.write("No right sibling found for tree on CC, should be impossible. Check parse.")
            raise
        except NoLeftSibling:
            sys.stderr.write("No left sibling found for tree on CC, should be impossible. Check parse.")
            raise        
        except UnlevelCCSiblings:
            sys.stderr.write("Unlevel CC parse. Check parse.")
            raise
        for item in flatSplit: self.th.depth_ulid_deaugment(item)

        #DEBUG
        """
        print "Splitted: "
        for i, item in enumerate(flatSplit): 
            g4 = Digraph(format='png')
            utils.print_tree_to_png(g4, [item])
            g4.render("/home/gian/hri_project/graphs/test/npsplit{}.gv".format(str(i)))
            print item
        """

        return flatSplit

    def split_on_multiple_ccs(self, tree, cc):
        temp_trees = self.split_on_cc(tree, cc)

        #in the case when 'if' phrase contains many or's 
        #e.g. 'If you see a bomb or a hostage or a... or a... etc.
        #we need to split until we have all single if phrases, i.e. with no or's
        num_single_if = 0 #number of if phrases with no "or" inside
        while num_single_if < len(temp_trees):
            new_temp_trees = []
            num_single_if = 0
            for t in temp_trees:
                if self.num_ccs(t, cc) > 0:
                    for tt in self.split_on_cc(t, cc):
                        new_temp_trees.append(tt)
                else:
                    new_temp_trees.append(t)
                    num_single_if += 1
            temp_trees = new_temp_trees

        #let's eliminate duplicate trees
        unique_trees = []
        for t in temp_trees:
            is_duplicate = False
            
            for ut in unique_trees:
                if t.leaves() == ut.leaves():
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_trees.append(t)

        return unique_trees
