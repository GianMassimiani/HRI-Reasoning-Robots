"""
Tests coordination in sentences via semantics.coordinating.
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

from semantics.tree import Tree
from semantics.coordinating import Split, Condition
from semantics.treehandler import TreeHandler
import unittest
    
class exampleCoordination(unittest.TestCase):
    #Correctly parsed by methodology leads to hardDict's incorrect parses
    def setUp(self):
        self.splitter = Split()
        self.th = TreeHandler()
        self.easyDict = {"Defuse_VP_VP" : {"sent": "Defuse the bomb and go to the hallway.",
                          "tree": Tree('S', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VP-A', [Tree('VB', ['Defuse']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['bomb'])])]), Tree('CC', ['and']), Tree('VP-A', [Tree('VB', ['go']), Tree('PP-CLR', [Tree('TO', ['to']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['hallway'])])])])]), Tree('.', ['.'])])
                          },
                    }
        
        self.exDict = {"Extracts VP, produces S trees with no verb" : {"sent" : "Go and defuse the bomb in the cellar.",
                    "tree" : Tree('S', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['Go']), Tree('CC', ['and']), Tree('VB', ['defuse']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['bomb'])]), Tree('PP-MNR', [Tree('IN', ['in']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['cellar'])])])]), Tree('.', ['.'])])
                    },
                  "Two carrys only one source-dest because of wrongly embedded 'to' pp": {"sent" : "Carry the hostages from the kitchen and the cafeteria to the cellar.",
                                                                    "tree" : Tree('S', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['Carry']), Tree('NP-A', [Tree('DT', ['the']), Tree('NNS', ['hostages'])]), Tree('PP-CLR', [Tree('IN', ['from']), Tree('NP-A', [Tree('NP', [Tree('DT', ['the']), Tree('NN', ['kitchen'])]), Tree('CC', ['and']), Tree('NP', [Tree('NP', [Tree('DT', ['the']), Tree('NN', ['cafeteria'])]), Tree('PP', [Tree('TO', ['to']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['cellar'])])])])])])]), Tree('.', ['.'])])
                                                                    },
                  "VP_NPNP_VP" : { "sent": "Defuse the bomb and the bomb and go to the hallway.",
                                  "tree" : Tree('S', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VP-A', [Tree('VB', ['Defuse']), Tree('NP-A', [Tree('NP', [Tree('DT', ['the']), Tree('NN', ['bomb'])]), Tree('CC', ['and']), Tree('NP', [Tree('DT', ['the']), Tree('NN', ['bomb'])])])]), Tree('CC', ['and']), Tree('VP-A', [Tree('VB', ['go']), Tree('PP-CLR', [Tree('TO', ['to']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['hallway'])])])])]), Tree('.', ['.'])])
                                  },
             "go_to_np_comma_np_comma" : {
                                          "sent" : "Go to the cellar, kitchen, and bedroom.",
                                          "tree" : Tree('S', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['Go']), Tree('PP-CLR', [Tree('TO', ['to']), Tree('NP-A', [Tree('NP', [Tree('DT', ['the']), Tree('NN', ['cellar'])]), Tree(',', [',']), Tree('NP', [Tree('NNP', ['kitchen'])]), Tree(',', [',']), Tree('CC', ['and']), Tree('NP', [Tree('NN', ['bedroom'])])])])]), Tree('.', ['.'])]),
                                          "correct_list" : [Tree('S', [Tree('NP-SBJ-A', [Tree('-NPNONE-', ['*'])]), Tree('VP', [Tree('VB', ['Go']), Tree('PP-CLR', [Tree('TO', ['to']), Tree('NP', [Tree('DT', ['the']), Tree('NN', ['cellar'])])])]), Tree('.', ['.'])]), Tree('S', [Tree('NP-SBJ-A', [Tree('-NPNONE-', ['*'])]), Tree('VP', [Tree('VB', ['Go']), Tree('PP-CLR', [Tree('TO', ['to']), Tree('NP', [Tree('NNP', ['kitchen'])])])]), Tree('.', ['.'])]), Tree('S', [Tree('NP-SBJ-A', [Tree('-NPNONE-', ['*'])]), Tree('VP', [Tree('VB', ['Go']), Tree('PP-CLR', [Tree('TO', ['to']), Tree('NP', [Tree('NN', ['bedroom'])])])]), Tree('.', ['.'])])]
                                          }
                  }
        self.ccConditionalDict = {"CC and adv conditional" : {"sent" : "Go to the cellar and if you see a bomb, activate your camera.",
                                              "tree" : Tree('S', [Tree('S-A', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['Go']), Tree('PP-CLR', [Tree('TO', ['to']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['cellar'])])])])]), Tree('CC', ['and']), Tree('S-A', [Tree('SBAR-ADV', [Tree('IN', ['if']), Tree('S-A', [Tree('NP-SBJ-A', [Tree('PRP', ['you'])]), Tree('VP', [Tree('VBP', ['see']), Tree('NP-A', [Tree('DT', ['a']), Tree('NN', ['bomb'])])])])]), Tree(',', [',']), Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['activate']), Tree('NP-A', [Tree('PRP$', ['your']), Tree('NN', ['camera'])])])]), Tree('.', ['.'])]),
                                              "frames" : []                                      
                                          },
                  "CC and tmp conditional" : {"sent" : "Go to the cellar and when you see a bomb, activate your camera.",
                                              "tree" : Tree('S', [Tree('S-A', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['Go']), Tree('PP-CLR', [Tree('TO', ['to']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['cellar'])])])])]), Tree('CC', ['and']), Tree('S-A', [Tree('SBAR-TMP', [Tree('WHADVP-0', [Tree('WRB', ['when'])]), Tree('S-A', [Tree('NP-SBJ-A', [Tree('PRP', ['you'])]), Tree('VP', [Tree('VBP', ['see']), Tree('NP-A', [Tree('DT', ['a']), Tree('NN', ['bomb'])]), Tree('ADVP-0', [Tree('-NONE-', ['*T*'])])])])]), Tree(',', [',']), Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['activate']), Tree('NP-A', [Tree('PRP$', ['your']), Tree('NN', ['camera'])])])]), Tree('.', ['.'])]),
                                              "frames": [],
                                              }
                             
                  }
        #Examples the current methods do not correctly parse
        self.hardDict = { "Carry_NP_NP" : {"sent" : "Carry the hostages from the kitchen and bedroom to the cellar.",
                                      "tree" : Tree('S', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['Carry']), Tree('NP-A', [Tree('DT', ['the']), Tree('NNS', ['hostages'])]), Tree('PP-CLR', [Tree('IN', ['from']), Tree('NP-A', [Tree('NP', [Tree('DT', ['the']), Tree('NN', ['kitchen'])]), Tree('CC', ['and']), Tree('NP', [Tree('NP', [Tree('NN', ['bedroom'])]), Tree('PP', [Tree('TO', ['to']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['cellar'])])])])])])]), Tree('.', ['.'])])                           
                                      },
                    "Go_NP_NP" : {"sent": "Go to the cellar and kitchen.",
                                  "tree": Tree('S', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['Go']), Tree('PP-CLR', [Tree('TO', ['to']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['cellar']), Tree('CC', ['and']), Tree('NN', ['kitchen'])])])]), Tree('.', ['.'])])
                                  },
                    "Carry_NP_NP_2" : {"sent": "Carry meals to the cafeteria and lounge.",
                                       "tree": Tree('S', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['Carry']), Tree('NP-A', [Tree('NNS', ['meals'])]), Tree('PP-CLR', [Tree('TO', ['to']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['cafeteria']), Tree('CC', ['and']), Tree('NN', ['lounge'])])])]), Tree('.', ['.'])])
                                       },
                    "Carry_NPNP_NPNP" : {"sent" : "Carry meals from the kitchen and cafeteria to the office and lounge.",
                                         #Wrong pp attachment for this tree ("to the office" modifies cafeteria)
                                         "tree" : Tree('S', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['Carry']), Tree('NP-A', [Tree('NNS', ['meals'])]), Tree('PP-CLR', [Tree('IN', ['from']), Tree('NP-A', [Tree('NP', [Tree('DT', ['the']), Tree('NN', ['kitchen'])]), Tree('CC', ['and']), Tree('NP', [Tree('NP', [Tree('NN', ['cafeteria'])]), Tree('PP', [Tree('TO', ['to']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['office'])])])]), Tree('CC', ['and']), Tree('NP', [Tree('NN', ['lounge'])])])])]), Tree('.', ['.'])])
                          },
                    "Two carrys only one source-dest because of wrongly embedded 'to' pp": {"sent" : "Carry the hostages from the kitchen and the cafeteria to the cellar.",
                                                                                    "tree" : Tree('S', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['Carry']), Tree('NP-A', [Tree('DT', ['the']), Tree('NNS', ['hostages'])]), Tree('PP-CLR', [Tree('IN', ['from']), Tree('NP-A', [Tree('NP', [Tree('DT', ['the']), Tree('NN', ['kitchen'])]), Tree('CC', ['and']), Tree('NP', [Tree('NP', [Tree('DT', ['the']), Tree('NN', ['cafeteria'])]), Tree('PP', [Tree('TO', ['to']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['cellar'])])])])])])]), Tree('.', ['.'])])
                                                                                    },
                    "Extracts VP, produces S trees with no verb" : {"sent" : "Go and defuse the bomb in the cellar.",
                                                                    "tree" : Tree('S', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['Go']), Tree('CC', ['and']), Tree('VB', ['defuse']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['bomb'])]), Tree('PP-MNR', [Tree('IN', ['in']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['cellar'])])])]), Tree('.', ['.'])])
                                                                    },
                        
                    "Carry_NPNP_NP" : {"sent" : "Carry meals to the library and cellar from the kitchen.",
                                       "tree": Tree('S', [Tree('NP-SBJ-A', [Tree('-NONE-', ['*'])]), Tree('VP', [Tree('VB', ['Carry']), Tree('NP-A', [Tree('NP', [Tree('NNS', ['meals'])]), Tree('PP', [Tree('TO', ['to']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['library']), Tree('CC', ['and']), Tree('NN', ['cellar'])])])]), Tree('PP-CLR', [Tree('IN', ['from']), Tree('NP-A', [Tree('DT', ['the']), Tree('NN', ['kitchen'])])])]), Tree('.', ['.'])]),
                                       }
                    }
        
    def test_list_cc(self):
        """Test a list command separated by commands and a single 'and'"""
        key = "go_to_np_comma_np_comma"
        tree = self.exDict[key]["tree"]
        correct_list = self.exDict[key]["correct_list"]
        self.th.depth_ulid_augment(tree, 0)        
        trees = self.splitter.split_on_cc(tree)
        self.assertEqual(trees,correct_list)        
        
    def coordination(self,matcher):
        easy = self.easyDict
        hard = self.hardDict
        for cs in hard:
            print "Sent: ",hard[cs]["sent"]
            print "Tree: ",hard[cs]["tree"]
            
    def conditional(self,matcher):
        dict = self.ccConditionalDict
        splitter = Split()
        conditioner = Condition()
        for sent in dict:
            tree = dict[sent]["tree"]
            sent = dict[sent]["sent"]            
            print "Sent: ",sent
            print "Tree: ",tree
            matcher.th.depth_ulid_augment(tree,0)
            trees = splitter.split_on_cc(tree)            
            for t in trees:
                conditions = conditioner.split_on_sbar(t)                
                #And match when get frames
            
if __name__=="__main__":
    unittest.main()
                
