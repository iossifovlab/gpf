#!/bin/bash

codePath=$DAE_SOURCE_DIR
dataPath=$DAE_DB_DIR
testsDef=$DAE_SOURCE_DIR/tests/default.txt
resDir=.

argCnt=0
inc=1

for arg in "$@"
do
   echo $arg
   argCnt=$(( $argCnt + $inc ))
done

echo "arg count=",$argCnt

if [ $argCnt -gt 0 ]
then
    dataPath=$1
    export DAE_DB_DIR=$dataPath
else
    [ -z "$DAE_SOURCE_DIR" ] && echo "Need to set DAE_SOURCE_DIR" && exit 1;
fi

if [ $argCnt -gt 1 ]
then
    codePath=$2
    export DAE_SOURCE_DIR=$codePath
else
    [ -z "$DAE_DB_DIR" ] && echo "Need to set DAE_DB_DIR" && exit 1;
fi

if [ $argCnt -gt 2 ]
then
    testsDef=$3
fi

if [ $argCnt -gt 3 ]
then
    resDir=$4
fi
 
# runUT.sh <data dir> <code directory> <test def file> <result directory>
# echo $dataPath,$codePath,$testsDef,$resDir

#PATH=/data/software/local/bin:$PATH
export PATH=${DAE_SOURCE_DIR}/tools:$PATH
export PATH=${DAE_SOURCE_DIR}/tests:$PATH
export PYTHONPATH=${DAE_SOURCE_DIR}:$PYTHONPATH

mkdir -p $resDir
lineNum=0
while read cmd; do
	((lineNum++))
	echo $lineNum,$cmd	
    `$cmd > $resDir/$lineNum-out.txt 2> $resDir/$lineNum-err.txt`
    echo $? > $resDir/$lineNum-exitCode.txt
    echo $cmd > $resDir/$lineNum-cmd.txt
done < $testsDef


