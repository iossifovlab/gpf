#!/bin/bash
# filename : ComputeDepthSGE.sh
# generated : 12/21/2012
# author(s) : Anthony Leotta
# origin : CSHL
# purpose : This script generates jobs that will create a depth of coverage
# histogram for a quad.
# It submits each job to the sun grid engine for execution in parallel
# caveates: it does not do the X or Y chromosome
 

FAMILY="auSSC12596 auSSC12605"
CHR="1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22"
DATAPATH="/data/safe/leotta/sge/DepthCoverage/"
OUTPUTPATH="/data/safe/leotta/sge/DepthCoverage/"
CWD=`pwd`

for family in ${FAMILY}
do
	for chrom in ${CHR}
	do
		#JOB="${OUTPUTPATH}${family}/${family}_${chrom}_DepthHist_job.sh"
		JOB="${family}_${chrom}_DepthHist_job.sh"

		if [ -f ${JOB} ] ; then
			rm ${JOB}
		fi

		infile="${DATAPATH}${family}/${family}_${chrom}_TargetCoverage_redo.out"
		
		outfile="${DATAPATH}${family}/${family}-${chrom}-Depths-Histogram.txt"

		if [ -f ${outfile} ] ; then
			rm ${outfile}
		fi

		if [ -f ${infile} ] ; then
			#echo ${JOB}
			#touch ${JOB}
			echo "#!/bin/bash" >> ${JOB}
			echo "cat ${infile} | ./DepthHist.py > ${outfile}" >> ${JOB}
			chmod +x ${JOB} 
			#cat ${JOB}
			#-o out.txt -e err.txt 
			qsub -cwd ${JOB}		
		else
			echo "${infile} is missing"
		fi 
		
	done
done
