# This is a specification definition file for the LTLMoP toolkit.
# Format details are described at the beginning of each section below.


======== SETTINGS ========

Actions: # List of action propositions and their state (enabled = 1, disabled = 0)

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
mytutorial.regions

Sensors: # List of sensor propositions and their state (enabled = 1, disabled = 0)

======== SPECIFICATION ========

Spec: # Specification in structured English
Go to the office

