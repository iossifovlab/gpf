#!/usr/bin/env bash

export DOC_DIR=$HOME/jobs/seqpipe/jobs/gpf-documentation/
export HTML_DIR=$DOC_DIR/html

export HTML_BAK=$DOC_DIR/html.bak

rm -rf $HTML_BAK
mv $HTML_DIR $HTML_BAK
tar zxvf gpf-html.tar.gz -C $DOC_DIR
