#!/bin/bash

codePath=$1
dataPath=$2
testsDef=$3
resDir=$4

export DAE_SOURCE_DIR=$1
export DAE_DB_DIR=$2
export PHENO_DB_DIR=/mnt/wigclust1/data/safe/leotta/sfari/v14
export PHENO_DB_PREFIX=$PHENO_DB_DIR/14_
PATH=/data/software/local/bin:$PATH
PATH=${DAE_SOURCE_DIR}/tools:$PATH
export PATH=${DAE_SOURCE_DIR}/tests:$PATH
export PYTHONPATH=${DAE_SOURCE_DIR}:$PYTHONPATH

#echo DAE_SOURCE_DIR=$DAE_SOURCE_DIR
#echo PATH=$PATH
#echo codePath=$codePath
#echo dataPath=$dataPath
#echo testsDef=$testsDef
#echo resDir=$resDir

mkdir -p $resDir
lineNum=0
while read cmd; do
	((lineNum++))
	echo $lineNum,$cmd	
    `$cmd > $resDir/$lineNum-out.txt 2> $resDir/$lineNum-err.txt`
    echo $? > $resDir/$lineNum-exitCode.txt
    echo $cmd > $resDir/$lineNum-cmd.txt
done < $testsDef
