import os
from sim import Simulator

def main():
	num_bombs = 3
	num_hostages = 2
    
	#------------
	#|    |      |
	#| r2 |   r3 |
	#|    |      |
	#|-----------|
	#|      | r4 |
	#|  r1  |    |
	#------------
	sim = Simulator({'r1': {'xmin': -3.3 , 'xmax': 3.45, 'ymin': -2.0, 'ymax': 2.45},
					 'r2': {'xmin': -3.0, 'xmax': -0.33, 'ymin': 5.0 , 'ymax': 11.0},
					 'r3': {'xmin': 2.0, 'xmax': 9.0, 'ymin': 5.0, 'ymax': 11.0},
					 'r4': {'xmin': 5.7, 'xmax': 9.0, 'ymin': 0.9, 'ymax': 2.6}},
					 [('r1', 'r2'),('r2', 'r3'), ('r3', 'r4'), ('r1', 'r4')],
					 num_bombs,
					 num_hostages,
					 bomb_sdf_filepath = os.path.abspath("../models/Dynamite/model.sdf"),
					 hostage_sdf_filepath = os.path.abspath("../models/Patrick/model.sdf"))
	

	spec_filepath = os.path.abspath("../LTLMoP/src/examples/searchrescue/rescue.spec")
	spec = ""
	instructions = "Write your specification. Press ENTER to add a command to the specification. " \
					"Press CTRL+D to send the specification to the robot. Q/q to abort."
	print instructions
	while True:
		try:
			line = raw_input(">")
			if line in ["Q", "q", "quit", "Quit"]:
				return
			spec += ("\n" + line)
		except EOFError:
			#if CTRL+D is pressed we send the specification
			#to the robot that executes it
			sim.run(spec_filepath, spec)
			print instructions
			spec = ""

if __name__ == "__main__":
	main()
