VARIANT_DB_CONFIG = u"""
[DEFAULT]
studyDir = %(wd)s/cccc

[dataset.DENOVO_DATASET]
name = DENOVO_DATASET
studies = DENOVO_STUDY
studyTypes = WE,TG

[study.DENOVO_STUDY]
familyInfo.file = %(studyDir)s/DENOVO_STUDY/families.tsv
familyInfo.fileFormat = simple
denovoCalls.files = %(studyDir)s/DENOVO_STUDY/data_annotated.tsv
study.phenotype=autism
study.type=WE
description=DENOVO_STUDY

[study.TRANSMITTED_STUDY]
familyInfo.file = %(studyDir)s/TRANSMITTED_STUDY/famData.txt
familyInfo.fileFormat = simple
transmittedVariants.indexFile = %(studyDir)s/TRANSMITTED_STUDY/TRANSMITTED_STUDY.format-annot
description=TRANSMITTED_STUDY
"""
