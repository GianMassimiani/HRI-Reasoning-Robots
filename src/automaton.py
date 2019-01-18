import os
import sys
import logging
import logging.handlers
logging.basicConfig()
from graphviz import Digraph

LTLMOP_DIR = os.path.abspath("../LTLMoP/src/")
sys.path.append(os.path.join(LTLMOP_DIR, "lib"))

from specCompiler import SpecCompiler

class Node(object):
    def __init__(self, ID, sensors,
                 reactions, actuators, memories,
                 region, successors = None):
        self.ID = ID
        self.sensors = sensors
        self.reactions = reactions
        self.actuators = actuators
        self.memories = memories
        self.region = region
        self.successors = successors

    def get_sensors(self):
    	return self.sensors

    def get_reactions(self):
    	return self.reactions

    def get_actuators(self):
    	return self.actuators

    def get_memories(self):
    	return self.memories

    def get_region(self):
    	return self.region

    def get_successors(self):
    	return self.successors

    def set_successors(self, nodes_list):
        for node in nodes_list:
            if not isinstance(node, Node):
                raise Exception("Successor must be an instance of Node.")

        self.successors = nodes_list

    def add_successors(self, nodes_list):
    	for node in nodes_list:
    		if not isinstance(node, Node):
    			raise Exception("Successor must be an instance of Node.")
    		self.successors.append(node)

    def remove_successor(self, succ):
    	for s in self.successors:
    		if s == succ:
    			self.successors.remove(s)

    def pprint(self):
    	print "sensors: ", self.sensors
    	print "actuators: ", self.actuators
    	print "reactions: ", self.reactions
    	print "memories: ", self.memories
    	print "region: ", self.region

    def __eq__(self, node):
    	"""Return True if this node is equal
    	to the given node"""
    	for sense in self.sensors:
    		if not sense in node.get_sensors():
    			return False
    	for act in self.actuators:
    		if not act in node.get_actuators():
    			return False
    	for react in self.reactions:
    		if not react in node.get_reactions():
    			return False
    	for mem in self.memories:
    		if not mem in node.get_memories():
    			return False
    	if self.region != node.get_region():
    		return False
    	return True

class Automaton(object):
	def __init__(self, sensors, regions, actuators, filename = None):
		if filename:
			self.filename = filename

		self.sensors = sensors
		self.regions = regions
		self.actuators = actuators
		self.reactions = []
		self.memories = [] #i.e. robot goals
		self.nodes = []

	def get_node(self, ID):
		for node in self.nodes:
			if node.ID == ID:
				return node

	def get_equal_node(self, node):
		"""
		Return the node in the automaton which is
		equal to the given node, if this exists.
		"""
		if not isinstance(node, Node):
			raise Exception("Node must be an instance of Node.")
		for n in self.nodes:
			if n == node:
				return n
		return None

	def get_sensors(self):
		return self.sensors

	def get_regions(self):
		return self.regions

	def get_actuators(self):
		return self.actuators

	def get_reactions(self):
		return self.reactions

	def get_memories(self):
		return self.memories
                
	def set_filename(self, filename):
		self.filename = filename

	def print_graphviz_wrong(self, filepath):
		"""Print automaton with Graphviz."""
		g = Digraph(format='png')
		for node in self.nodes:
			label = ""
			#for each node print only the propositions that are true
			for (reaction, is_true) in node.reactions:
				if is_true:
					label = label + reaction + "\n"
			for (actuator, is_true) in node.actuators:
				if is_true:
					label = label + actuator + "\n"
			for (memory, is_true) in node.memories:
				if is_true:
					label = label + memory + "\n"

			label = label + node.region
			g.node(str(node.ID), label)

		for node in self.nodes:
			for s in node.successors:
				edge_label = ""
				for (sense, truth_value) in s.sensors:
					if truth_value:
						edge_label = edge_label + sense + "\n"
				g.edge(str(node.ID), str(s.ID), edge_label)

		g.render(filepath)

	def print_graphviz(self, filepath):
		"""Print automaton with graphviz."""
		g = Digraph(format='png')
		for node in self.nodes:

			#DEBUG
			#print node.ID
			#print node.sensors
			#print node.reactions
			#print node.actuators
			#print node.region
			#print

			label = str(node.ID)
			for (reaction, truth) in node.reactions:
				if truth:
					label = "\n".join([label, reaction])
			for (actuator, truth) in node.actuators:
				if truth:
					label = "\n".join([label, actuator])
			for (memory, truth) in node.memories:
				if truth:
					label = "\n".join([label, memory])

			label = "\n".join([label, node.region])
			g.node(str(node.ID), label)

		for node in self.nodes:
			for s in node.successors:
				edge_label = ""
				for (sense, truth) in s.sensors:
					if truth:
						edge_label = edge_label + sense + "\n"
				g.edge(str(node.ID), str(s.ID), edge_label)

		g.render(filepath)

	def build_wrong(self):
		"""Build automaton by reading from file."""
		if not self.filename:
			raise Exception("Cannot build automaton: no filename specified.")

		f = open(self.filename)
		line = None
		state_ID = 0
		successors = {}
		while line != "":
			line = f.readline()

			if line != "\n" and line != "":
				line = line.strip()
				line = line.split("-> <")[1]
				line = line.split(">")[0].split(",")

				label = ""
				sensors = []
				reactions = []
				actuators = []
				memories = []
				region = None
				for el in line:
					el = el.strip()
					el = el.split(":")
					prop = el[0]
					
					#check whether proposition is true or false
					is_true = bool(int(el[1]))

					if "react" in prop:
						reactions.append((prop, is_true))
						if not prop in self.reactions:
							self.reactions.append(prop)
					elif "mem" in prop:
						memories.append((prop, is_true))
						if not prop in self.memories:
							self.memories.append(prop)
					elif prop in self.regions:
						if is_true:
							region = prop
					elif prop in self.sensors:
						sensors.append((prop, is_true))
					elif prop in self.actuators:
						actuators.append((prop, is_true))

				successors[state_ID] = []
				candidates_successors = f.readline().strip().split(":")[1]

				for s in candidates_successors:
					try:
						successors[state_ID].append(int(s))
					except ValueError:
						continue

				state = Node(state_ID, sensors, reactions, actuators, memories, region)
				state_ID += 1
				self.nodes.append(state)

		f.close()
		#for each node find its successors
		for node in self.nodes:
			for state in successors:
				if state == node.ID:
					succ_nodes = []
					for s in successors[state]:
						succ_nodes.append(self.get_node(s))
					node.set_successors(succ_nodes)
					break

	def build(self):
		"""Build automaton by reading from file."""
		if not self.filename:
			raise Exception("Cannot build automaton: no filename specified.")
		f = open(self.filename)


		text_to_list = f.read().split("\n")
		stripped_list = []
		for chunk in text_to_list:
			if chunk:
				stripped_list.append(chunk.strip())

		f.close()
    
		new_list = []
		for i, el in enumerate(stripped_list):
			#if index is even
			if not i%2:
				new_list.append((stripped_list[i], stripped_list[i+1]))

		stripped_new_list = []
		for j, tupl in enumerate(new_list):
			nodeID = j
			node_props = tupl[0].split("->")[1].strip().strip("<").strip(">")
			succ_info = tupl[1].split(":")[1].strip()
			stripped_new_list.append((nodeID, node_props, succ_info))

		successors = {}
		for el in stripped_new_list:
			nodeID = el[0]
			node_props = el[1].split(",")
			node_succ = el[2].split(",")

			stripped_props = []
			for prop in node_props:
				stripped_props.append(prop.strip())

			stripped_succ = []
			for succ in node_succ:
				stripped_succ.append(succ.strip())

			reacts = []
			mems = []
			sens = []
			acts = []
			for p in stripped_props:
				splitted_p = p.split(":")
				prop = splitted_p[0]
				truth = bool(int(splitted_p[1]))
				if "react" in prop:
					reacts.append((prop, truth))
					if not prop in self.reactions:
						self.reactions.append(prop)
				elif "mem" in prop:
					mems.append((prop, truth))
					if not prop in self.memories:
						self.memories.append(prop)
				elif prop in self.regions:
					if truth:
						region = prop
				elif prop in self.sensors:
					sens.append((prop, truth))
				elif prop in self.actuators:
					acts.append((prop, truth))

			successors[int(nodeID)] = [int(s) for s in stripped_succ]
			state = Node(nodeID, sens, reacts, acts, mems, region)
			self.nodes.append(state)

		for ID, succ_IDs in successors.iteritems():
			node = self.get_node(ID)
			succ_list = []
			for s in succ_IDs:
				succ_list.append(self.get_node(int(s)))
			node.set_successors(succ_list)


class AutomatonSynthesizer(object):
	"""
	This class translates user specifications into LTL formulas
	and then synthesizes an automaton.
	"""
	def __init__(self, context = None, log_level = logging.DEBUG):
		self.log = logging.getLogger(self.__class__.__name__)
		self.log.setLevel(log_level)

		self.log_level = log_level

		self.compiler = SpecCompiler()
		self.automaton = None
		self.context = context

	def set_log_level(self, log_level):
		self.log.setLevel(log_level)
		self.log_level = log_level

	def set_context(self, context):
		self.context = context

	def set_default_options(self):
		"""Set default options for the specification compiler."""

		self.compiler.proj.compile_options["convexify"] = False
		self.compiler.proj.compile_options["parser"] = "slurp"
		self.compiler.proj.compile_options["fastslow"] = False
		self.compiler.proj.compile_options["decompose"] = False
		self.compiler.proj.compile_options["use_region_bit_encoding"] = False

	def __call__(self, specfile = None, text = "", automatonID = ""):
		if specfile and text:
			self.log.warning("Compiling from a spec file: compiler may be using the compiling \
				             options provided in the spec file (if these are specified). Note that these \
				             may be different from its default options, and can lead to \
				             unsuccessfull compilation.")
			
			self.compiler.loadSpec(specfile)

			self.compiler.proj.specText=text
			self.compiler.specText = text

			#DEBUG
			#print "PROJ.SPECTEXT: "
			#print repr(self.compiler.proj.specText)
			#print "COMPILER.SPECTEXT: "
			#print repr(self.compiler.specText)

			sensors = self.compiler.proj.enabled_sensors
			actuators = self.compiler.proj.enabled_actuators
			regions = []
			for region in self.compiler.proj.rfi.regions:
				regions.append(str(region.name))

			self.automaton = Automaton(sensors,
				                       regions,
				                       actuators)
		elif specfile:
			self.log.warning("Compiling from a spec file: compiler may be using the compiling \
				             options provided in the spec file (if these are specified). Note that these \
				             may be different from its default options, and can lead to \
				             unsuccessfull compilation.")
			self.compiler.loadSpec(specfile)

			#DEBUG
			#print "PROJ.SPECTEXT: "
			#print repr(self.compiler.proj.specText)
			#print "COMPILER.SPECTEXT: "
			#print repr(self.compiler.specText)

			sensors = self.compiler.proj.enabled_sensors
			actuators = self.compiler.proj.enabled_actuators
			regions = []
			for region in self.compiler.proj.rfi.regions:
				regions.append(str(region.name))

			self.automaton = Automaton(sensors,
				                       regions,
				                       actuators)
		elif text:
			if not self.context:
				self.log.error("Can't compile: no context provided. See set_context.")
				return
			self.set_default_options()
			try:
			    self.compiler.loadSimpleSpec(text,
			    	                         self.context["regions"],
			    	                         self.context["sensors"],
			    	                         self.context["actuators"],
			    	                         self.context["customs"],
			    	                         self.context["adjacent_regions"],
			    	                         self.context["outputfile"])
			    
			    self.automaton = Automaton(self.context["sensors"], 
			    	                       self.context["regions"],
			    	                       self.context["actuators"])
			except KeyError:
				self.log.error("Can't load specification: invalid context. \
					Please provide a list of regions, sensors, actuators, \
					customs propositions, adjacent regions, and an outputfile.")
				return
		else:
			self.log.error("Can't compile: no specification provided.")
			return

        #compile specification and save automaton to file
		output = self.compiler.compile()
		self.log.debug("Automaton file saved in: {}".format(self.compiler.proj.getFilenamePrefix() + ".aut"))

        #build automaton from file and print to png file
		self.automaton.set_filename(self.compiler.proj.getFilenamePrefix() + ".aut")
		self.automaton.build()
		self.automaton.print_graphviz(os.path.abspath("../figures/automaton/automaton{}.gv".format(str(automatonID))))
		self.log.debug("Automaton figure saved in: {}".format(os.path.abspath("../figures/automaton/automaton{}.gv".format(str(automatonID)))))
		return self.automaton

if __name__ == "__main__":
	filename = os.path.abspath("../LTLMoP/src/examples/searchrescue/rescue.aut")
	aut = Automaton(["hostage", "bomb"], ["r1", "r2"], ["camera"], filename)
	aut.build()
	aut.print_graphviz()
