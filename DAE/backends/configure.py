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
    def from_prefix_parquet(prefix):
        if os.path.exists(prefix) and os.path.isdir(prefix):
            dirname = prefix
            fileprefix = ""
        else:
            dirname, fileprefix = os.path.split(prefix)

        assert os.path.exists(dirname)
        assert os.path.isdir(dirname)

        summary_filename = os.path.join(
            dirname, "{}summary.parquet".format(fileprefix))
        family_filename = os.path.join(
            dirname, "{}family.parquet".format(fileprefix))
        member_filename = os.path.join(
            dirname, "{}member.parquet".format(fileprefix))
        effect_gene_filename = os.path.join(
            dirname, "{}effect_gene.parquet".format(fileprefix))
        pedigree_filename = os.path.join(
            dirname, "{}pedigree.parquet".format(fileprefix))

        conf = {
            'parquet': {
                'summary_variant': summary_filename,
                'family_variant': family_filename,
                'member_variant': member_filename,
                'effect_gene_variant': effect_gene_filename,
                'pedigree': pedigree_filename
            }
        }

        return Configure(conf)

    @staticmethod
    def parquet_prefix_exists(prefix):
        if not os.path.exists(prefix) or not os.path.isdir(prefix):
            return False
        conf = Configure.from_prefix_parquet(prefix).parquet
        print(conf)
        
        return os.path.exists(conf.summary_variant) and \
            os.path.exists(conf.family_variant) and \
            os.path.exists(conf.member_variant) and \
            os.path.exists(conf.effect_gene_variant) and \
            os.path.exists(conf.pedigree)
