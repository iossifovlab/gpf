
UT_DIR=.
UT_DEFS_DIR=.
UT_TEST_DEF=$UT_DEFS_DIR/testdefs1.txt

PRD_DB_DIR=/mnt/wigclust8/home/iossifov/work/T115/secondWD
DEV_DB_DIR=/data/safe/leotta/send_to_natalia/data

PRD_SRC_DIR=/mnt/wigclust8/data/safe/autism/SeqPipeline/python/DAE
DEV_SRC_DIR=/data/safe/leotta/wigserv2_clone3/python/DAE


$UT_DIR/runUT_production.sh $PRD_SRC_DIR $PRD_DB_DIR $UT_TEST_DEF production
$UT_DIR/runUT_development.sh $DEV_SRC_DIR $DEV_DB_DIR $UT_TEST_DEF development

$UT_DIR/compareUT.py production development

