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
        # assert os.path.exists(self.pedigree), self.pedigree
        # assert os.path.exists(self.vcf), self.vcf
        # assert os.path.exists(self.annotation), self.annotation

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
    def from_prefix_parquet(prefix, bucket_index=0, suffix=None):
        # assert os.path.exists(prefix)
        # assert os.path.isdir(prefix)
        assert bucket_index >= 0

        if suffix is None and bucket_index == 0:
            filesuffix = ""
        elif bucket_index > 0 and suffix is None:
            filesuffix = "_{:0>6}".format(bucket_index)
        elif bucket_index == 0 and suffix is not None:
            filesuffix = "{}".format(suffix)
        else:
            filesuffix = "_{:0>6}{}".format(bucket_index, suffix)

        summary_filename = os.path.join(
            prefix, "summary{}.parquet".format(filesuffix))
        family_filename = os.path.join(
            prefix, "family{}.parquet".format(filesuffix))
        member_filename = os.path.join(
            prefix, "member{}.parquet".format(filesuffix))
        effect_gene_filename = os.path.join(
            prefix, "effect_gene{}.parquet".format(filesuffix))
        pedigree_filename = os.path.join(
            prefix, "pedigree{}.parquet".format(filesuffix))

        conf = {
            'parquet': {
                'summary_variant': summary_filename,
                'family_variant': family_filename,
                'member_variant': member_filename,
                'effect_gene_variant': effect_gene_filename,
                'pedigree': pedigree_filename,
                'db': 'parquet'
            }
        }

        return Configure(conf)

    @staticmethod
    def from_prefix_impala(prefix, db=None, bucket_index=0, suffix=None):
        # assert os.path.exists(prefix)
        # assert os.path.isdir(prefix)
        assert bucket_index >= 0

        if db is None:
            basename = os.path.basename(prefix)
            db = basename
            if not db:
                db = "test_impala_db"

        if suffix is None and bucket_index == 0:
            filesuffix = ""
        elif bucket_index > 0 and suffix is None:
            filesuffix = "_{:0>6}".format(bucket_index)
        elif bucket_index == 0 and suffix is not None:
            filesuffix = "{}".format(suffix)
        else:
            filesuffix = "_{:0>6}{}".format(bucket_index, suffix)

        variants_filename = os.path.join(
            prefix, "variants{}.parquet".format(filesuffix))
        pedigree_filename = os.path.join(
            prefix, "pedigree{}.parquet".format(filesuffix))

        conf = {
            'impala': {
                'files': {
                    'variants': variants_filename,
                    'pedigree': pedigree_filename,
                },
                'db': db,
                'tables': {
                    'variant': 'variant',
                    'pedigree': 'pedigree',
                }
            }
        }

        return Configure(conf)

    @staticmethod
    def from_thrift_db(
            db, summary='summary', family='family',
            effect_gene='effect_gene', member='member',
            pedigree='pedigree'):

        conf = {
            'parquet': {
                'summary_variant': summary,
                'family_variant': family,
                'member_variant': member,
                'effect_gene_variant': effect_gene,
                'pedigree': pedigree,
                'db': db,
            }
        }

        return Configure(conf)

    @staticmethod
    def parquet_prefix_exists(prefix, bucket_index=0, suffix=None):
        if not os.path.exists(prefix) or not os.path.isdir(prefix):
            return False
        conf = Configure.from_prefix_parquet(prefix, bucket_index, suffix)
        conf = conf.parquet

        return os.path.exists(conf.summary_variant) and \
            os.path.exists(conf.family_variant) and \
            os.path.exists(conf.member_variant) and \
            os.path.exists(conf.effect_gene_variant) and \
            os.path.exists(conf.pedigree)
