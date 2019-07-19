#!/bin/sh


wget -c https://iossifovlab.com/distribution/public/data-hg19-startup.tar.gz

data_tar_time=`stat -c %Y data-hg19-startup.tar.gz`
data_dir_time=`stat -c %Y data-hg19-startup`
if [ $data_tar_time -nt $data_dir_time ];
then
    tar zxf data-hg19-startup.tar.gz
fi

