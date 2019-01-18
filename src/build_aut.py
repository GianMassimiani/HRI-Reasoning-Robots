import os
from automaton import *
from graphviz import Digraph

def print_graphviz(aut):
    g = Digraph(format='png')
    for node in aut.nodes:

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

    for node in aut.nodes:
        for s in node.successors:
            edge_label = ""
            for (sense, truth) in s.sensors:
                if truth:
                    edge_label = edge_label + sense + "\n"
            g.edge(str(node.ID), str(s.ID), edge_label)

    g.render()
    

def build(aut):
    filepath = os.path.abspath("/home/gian/hri_project/LTLMoP/src/examples/searchrescue/rescue.aut")
    f = open(filepath)


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
                if not prop in aut.reactions:
                    aut.reactions.append(prop)
            elif "mem" in prop:
                mems.append((prop, truth))
                if not prop in aut.memories:
                    aut.memories.append(prop)
            elif prop in aut.regions:
                if truth:
                    region = prop
            elif prop in aut.sensors:
                sens.append((prop, truth))
            elif prop in aut.actuators:
                acts.append((prop, truth))

        successors[int(nodeID)] = [int(s) for s in stripped_succ]
        state = Node(nodeID, sens, reacts, acts, mems, region)
        aut.nodes.append(state)

    for ID, succ_IDs in successors.iteritems():
        node = aut.get_node(ID)
        succ_list = []
        for s in succ_IDs:
            succ_list.append(aut.get_node(int(s)))
        node.set_successors(succ_list)
            

            
                

if __name__ == "__main__":
    sensors = ["bomb", "hostage"]
    actuators = ["defuse", "not_defuse", "interact"]
    regions = ["r1", "r2", "r3", "r4"]
    a = Automaton(sensors, regions, actuators)
    build(a)

    print_graphviz(a)
    
    
