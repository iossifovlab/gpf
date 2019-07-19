'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import unicode_literals, absolute_import, print_function
from box import ConfigBox
import os


class Configure(ConfigBox):

    def __init__(self, data, **kwargs):
        super(Configure, self).__init__(data, **kwargs)

    @staticmethod
    def array_from_enabled_dir(enabled_dir):
        assert os.path.exists(enabled_dir)

        result = []

        for filename in os.listdir(enabled_dir):
            path = os.path.join(enabled_dir, filename)
            if os.path.isfile(path):
                result.append(Configure.from_config(enabled_dir, filename))

        return result

    @staticmethod
    def from_dict(conf):
        return Configure(conf)

    @staticmethod
    def from_prefix_vcf(prefix):
        vcf_filename = '{}.vcf'.format(prefix)
        if not os.path.exists(vcf_filename):
            vcf_filename = '{}.vcf.gz'.format(prefix)

        conf = {
            'vcf': {
                'pedigree': '{}.ped'.format(prefix),
                'vcf': vcf_filename,
                'annotation': '{}-eff.txt'.format(prefix),
                'prefix': prefix
            }
        }
        return Configure(conf)

    @staticmethod
    def from_prefix_dae(prefix):
        summary_filename = '{}.txt.gz'.format(prefix)
        toomany_filename = '{}-TOOMANY.txt.gz'.format(prefix)
        family_filename = "{}.families.txt".format(prefix)

        conf = {
            'dae': {
                'summary_filename': summary_filename,
                'toomany_filename': toomany_filename,
                'family_filename': family_filename,
            }
        }
        return Configure(conf)

    @staticmethod
    def from_prefix_denovo(prefix):
        denovo_filename = '{}.txt'.format(prefix)
        family_filename = "{}.families.txt".format(prefix)

        conf = {
            'denovo': {
                'denovo_filename': denovo_filename,
                'family_filename': family_filename,
            }
        }
        return Configure(conf)

    @staticmethod
    def from_prefix_impala(
            prefix, db=None, study_id=None, bucket_index=0, suffix=None):

        assert bucket_index >= 0

        basename = os.path.basename(os.path.abspath(prefix))
        if study_id is None:
            study_id = basename
        assert study_id

        if db is None:
            db = study_id

        if suffix is None and bucket_index == 0:
            filesuffix = ""
        elif bucket_index > 0 and suffix is None:
            filesuffix = "_{:0>6}".format(bucket_index)
        elif bucket_index == 0 and suffix is not None:
            filesuffix = "{}".format(suffix)
        else:
            filesuffix = "_{:0>6}{}".format(bucket_index, suffix)

        variant_filename = os.path.join(
            prefix, "{}_variant{}.parquet".format(
                study_id, filesuffix))
        pedigree_filename = os.path.join(
            prefix, "{}_pedigree{}.parquet".format(
                study_id, filesuffix))

        conf = {
            'impala': {
                'files': {
                    'variant': variant_filename,
                    'pedigree': pedigree_filename,
                },
                'db': db,
                'tables': {
                    'variant': '{}_variant'.format(study_id),
                    'pedigree': '{}_pedigree'.format(study_id),
                }
            }
        }

        return Configure(conf)

