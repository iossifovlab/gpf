from functools import partial

from studies.study import Study
from variants.raw_thrift import ThriftFamilyVariants
from variants.raw_vcf import RawFamilyVariants


class StudyFactory(object):

    FILE_FORMAT = {
        "vcf": RawFamilyVariants,
        "thrift": ThriftFamilyVariants
    }

    def __init__(self, thrift_connection=None):
        self.thrift_connection = thrift_connection

    def make_study(self, study_config):
        if study_config.type not in self.FILE_FORMAT:
            raise ValueError(
                "Unknown study format: {}\nKnown ones: {}"
                .format(study_config.type, list(self.FILE_FORMAT.keys()))
            )

        study_type_constructor = self.FILE_FORMAT[study_config.type]
        if study_type_constructor == self.FILE_FORMAT["thrift"]:
            if self.thrift_connection is None:
                self.thrift_connection = \
                    ThriftFamilyVariants.get_thrift_connection()
            study_type_constructor = partial(
                study_type_constructor,
                thrift_connection=self.thrift_connection
            )

        variants = study_type_constructor(
            prefix=study_config.prefix)

        return Study(study_config, variants)
