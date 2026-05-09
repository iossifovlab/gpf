export WD="$(pwd)"
export DAE_DB_DIR="${WD}/gpf_e2e_instance"

# export DUCKDB_STORAGE="/mnt/cephfs/seqpipe/duckdb_testing_instances_storage"
# export PHENO_STORAGE="/mnt/cephfs/seqpipe/data-phenodb-production"

LABEL=$(/usr/bin/basename $WD)

PS1="($LABEL seqpipe) $PS1"
PS1=$(echo ${PS1//\w+/ })
PS1="$PS1 "

export PS1
