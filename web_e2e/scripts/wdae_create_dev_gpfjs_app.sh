#!/bin/bash

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")
# Export for create_gpfjs_dev_app.py
export GPFJS_URL="http://gpf/gpf"

wdaemanage.py shell < $SCRIPTPATH/create_gpfjs_dev_app.py
