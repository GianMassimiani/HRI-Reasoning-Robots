#!/bin/sh
LTLMOP_LIB=../../lib
export PYTHONPATH=$LTLMOP_LIB:$PYTHONPATH
if [ ! -d $LTLMOP_LIB ]; then
    echo "Error: LTLMoP cannot be imported."
    echo "This probably means you are not running this script from inside"
    echo "the SLURP submodule of a LTLMoP respository (/src/etc/SLURP)."
    exit 1
fi
python2 -u pragbot_slurp_server.py 10007
