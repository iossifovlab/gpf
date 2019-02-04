from functools import partial

from studies.study import Study
from backends.thrift.raw_thrift import ThriftFamilyVariants
from backends.vcf.raw_vcf import RawFamilyVariants


class StudyFactory(object):

    FILE_FORMAT = {
        "vcf": RawFamilyVariants,
        "thrift": ThriftFamilyVariants
    }

    def __init__(self, thrift_connection=None):
        self.thrift_connection = thrift_connection

    def make_study(self, study_config):
        if study_config.file_format not in self.FILE_FORMAT:
            raise ValueError(
                "Unknown study format: {}\nKnown ones: {}"
                .format(
                    study_config.file_format, list(self.FILE_FORMAT.keys()))
            )

        backend_constructor = self.FILE_FORMAT[study_config.file_format]
        if backend_constructor == self.FILE_FORMAT["thrift"]:
            if self.thrift_connection is None:
                self.thrift_connection = \
                    ThriftFamilyVariants.get_thrift_connection()
            backend_constructor = partial(
                backend_constructor,
                thrift_connection=self.thrift_connection
            )

        variants = backend_constructor(
            prefix=study_config.prefix)

        return Study(study_config, variants)
