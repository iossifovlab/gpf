'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import unicode_literals
from box import ConfigBox
import reusables
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
    def from_config(work_dir=None, filename=None):
        if work_dir is None:
            from variants.default_settings import DATA_DIR
            work_dir = DATA_DIR

        if filename is None:
            from variants.default_settings import CONFIG_FILE
            filename = CONFIG_FILE

        if not os.path.exists(filename):
            filename = os.path.abspath(os.path.join(work_dir, filename))

        assert os.path.exists(filename)

        conf = reusables.config_dict(
            filename,
            auto_find=False,
            verify=True,
            defaults={
                'wd': work_dir,
            })

        return Configure(conf)

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
    def from_prefix_parquet(prefix):
        assert os.path.exists(prefix)
        assert os.path.isdir(prefix)

        summary_filename = os.path.join(
            prefix, "summary.parquet")
        family_filename = os.path.join(
            prefix, "family.parquet")
        allele_filename = os.path.join(
            prefix, "allele.parquet")
        pedigree_filename = os.path.join(
            prefix, "pedigree.parquet")

        conf = {
            'parquet': {
                'summary_variants': summary_filename,
                'family_variants': family_filename,
                'family_alleles': allele_filename,
                'pedigree': pedigree_filename
            }
        }

        return Configure(conf)
