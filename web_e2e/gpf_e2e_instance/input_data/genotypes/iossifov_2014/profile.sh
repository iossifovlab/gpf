#!/bin/sh

mkdir -p log
# rm -f out/*.tsv
COMMAND=$(python -c "import dae.tools.simple_study_import; print(dae.tools.simple_study_import.__file__)")

echo "COMMAND=$COMMAND"

python -m cProfile -o log/simple_study_import1.profile \
     $COMMAND  \
	IossifovWE2014.ped --denovo IossifovWE2014.tsv --id iossifov_2014

pyprof2calltree -i log/simple_study_import1.profile -o log/simple_study_import1.calltree


