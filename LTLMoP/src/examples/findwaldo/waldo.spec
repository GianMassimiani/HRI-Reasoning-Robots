# This is a specification definition file for the LTLMoP toolkit.
# Format details are described at the beginning of each section below.


======== SETTINGS ========

Actions: # List of action propositions and their state (enabled = 1, disabled = 0)
camera, 1
radio, 0

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
waldo.regions

Sensors: # List of sensor propositions and their state (enabled = 1, disabled = 0)
hostage, 1
bomb, 1
kid, 0

======== SPECIFICATION ========

Spec: # Specification in structured English

#example 1
#Start in r1
#Go to r3
#If you see waldo activate camera

#example 2 -> this gives a problem because of verb "be"
#Start in r2
#Go to r3
#If you are in r3, activate the camera

Start in r1
Go to r3
If you see a hostage and a bomb activate the camera
#Activate the radio
