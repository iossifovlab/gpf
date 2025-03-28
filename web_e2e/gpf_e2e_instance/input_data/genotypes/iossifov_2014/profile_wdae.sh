#!/bin/sh

mkdir -p log/wdaeprofile
# rm -f out/*.tsv
# COMMAND=$(python -c "import dae.tools.simple_study_import; print(dae.tools.simple_study_import.__file__)")

# COMMAND=$(python -c "import wdaemanage; print(wdaemanage.__file__)")
# COMMAND="./wdaeprofile.py"

# echo "COMMAND=$COMMAND"


# DJANGO_SETTINGS_MODULE=wdae.settings python -m cProfile -o log/wdaemanage1.profile $COMMAND runserver
# DJANGO_SETTINGS_MODULE=wdae.settings python -m cProfile -o log/wdaemanage1.profile $COMMAND

wdaemanage.py runprofileserver --kcachegrind --prof-path=./log/wdaeprofile/
# pyprof2calltree -i log/wdaemanage1.profile -o log/wdaemanage1.calltree


