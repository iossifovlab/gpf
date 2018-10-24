from functools import partial

from studies.study import Study
from variants.raw_thrift import ThriftFamilyVariants
from variants.raw_vcf import RawFamilyVariants


class StudyFactory(object):

    STUDY_TYPES = {
        "vcf": RawFamilyVariants,
        "thrift": ThriftFamilyVariants
    }

    def __init__(self, thrift_connection=None):
        if thrift_connection is None:
            thrift_connection = ThriftFamilyVariants.get_thrift_connection()
        self.thrift_connection = thrift_connection

    def make_study(self, study_config):
        if study_config.type not in self.STUDY_TYPES:
            raise ValueError(
                "Unknown study type: {}\nKnown ones: {}"
                .format(study_config.type, list(self.STUDY_TYPES.keys()))
            )

        study_type_constructor = self.STUDY_TYPES[study_config.type]
        if study_type_constructor == self.STUDY_TYPES["thrift"]:
            study_type_constructor = partial(
                study_type_constructor, thrift_connection=self.thrift_connection
            )

        variants = study_type_constructor(
            prefix=study_config.prefix)

        return Study(study_config.study_name, variants, study_config)
