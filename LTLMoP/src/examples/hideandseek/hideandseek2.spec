# This is a specification definition file for the LTLMoP toolkit.
# Format details are described at the beginning of each section below.


======== SETTINGS ========

Actions: # List of action propositions and their state (enabled = 1, disabled = 0)
count, 1
whistle, 1
hide, 1
say_foundyou, 1
say_imfound, 1
say_hider, 1
say_seeker, 1

CompileOptions:
convexify: True
parser: slurp
fastslow: False
decompose: True
use_region_bit_encoding: True

CurrentConfigName:
Basic simulation

Customs: # List of custom propositions
seeker
playing

RegionFile: # Relative path of region description file
hideandseek.regions

Sensors: # List of sensor propositions and their state (enabled = 1, disabled = 0)
see_player, 1
hear_whistle, 1
hear_counting, 1


======== SPECIFICATION ========

RegionMapping: # Mapping between region names and their decomposed counterparts
Classroom1 = p12
Classroom2 = p11
Office = p7
Closet = p10
Gym = p8
others = p1, p13, p14, p15, p16, p17, p18, p19, p20, p21, p22, p23, p24, p25
Parking = p6

Spec: # Specification in structured English
### Overview ###
# Start in the parking lot.  If you are a seeker, stay there and count until you hear a ready whistle.
# Then search all the hiding spots until you find someone.  Once you've found someone, you are now a hider.
# If you are a hider, go back to the parking lot and wait for counting to start.
# Once that happens, go hide somewhere and whistle.

Environment starts with not hear_whistle and not hear_counting
Robot starts in Parking
Robot goes the Office

