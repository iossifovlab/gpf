from studies.study import Study
from variants.raw_thrift import ThriftFamilyVariants
from variants.raw_vcf import RawFamilyVariants


class StudyFactory(object):

    STUDY_TYPES = {
        "vcf": RawFamilyVariants,
        "thrift": ThriftFamilyVariants
    }

    def make_study(self, study_config):
        if study_config.type not in self.STUDY_TYPES:
            raise ValueError(
                "Unknown study type: {}\nKnown ones: {}"
                .format(study_config.type, list(self.STUDY_TYPES.keys()))
            )

        variants = self.STUDY_TYPES[study_config.type](prefix=study_config.prefix)

        return Study(variants)
