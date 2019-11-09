#!/bin/sh



dir_setup() {
    data_tar_time=`stat -c %Y data-hg19-startup-latest.tar.gz`
    data_dir_time=`stat -c %Y data-hg19-startup`
    if [ ! -d 'data-hg19-startup' ] || [ $data_tar_time -nt $data_dir_time ];
    then
        tar zxf data-hg19-startup-latest.tar.gz
    fi
}

get_file() {
    wget -c https://iossifovlab.com/distribution/public/data-hg19-startup-3.0.0dev-genotype-storage.tar.gz
    mv data-hg19-startup-3.0.0dev-genotype-storage.tar.gz data-hg19-startup-latest.tar.gz
}

if [ -f 'data-hg19-startup-latest.tar.gz' ];
then
    new_time=`curl -I https://iossifovlab.com/distribution/public/data-hg19-startup-3.0.0dev-genotype-storage.tar.gz | grep Last-Modified | sed "s/^Last-Modified: \(.*\)$/\1/"`
    python ${SOURCE_DIR}/jenkins_data_check_timestamp.py "$new_time"
    if [ $? != 0 ];
    then
        rm data-hg19-startup-latest.tar.gz
	get_file
    fi
else
    get_file
fi

dir_setup