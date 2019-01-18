# This is a specification definition file for the LTLMoP toolkit.
# Format details are described at the beginning of each section below.


======== SETTINGS ========

Actions: # List of action propositions and their state (enabled = 1, disabled = 0)
interact, 1
defuse, 1
not_defuse, 1

CompileOptions:
convexify: False
parser: slurp
fastslow: False
decompose: False
use_region_bit_encoding: False

CurrentConfigName:
Basic Simulation

Customs: # List of custom propositions

RegionFile: # Relative path of region description file
rescue2.regions

Sensors: # List of sensor propositions and their state (enabled = 1, disabled = 0)
hostage, 1
bomb, 1

======== SPECIFICATION ========

Spec: # Specification in structured English
