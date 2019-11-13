from box import ConfigBox
import os


class Configure(ConfigBox):

    def __init__(self, data, **kwargs):
        super(Configure, self).__init__(data, **kwargs)

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
        family_filename = "{}_families.txt".format(prefix)

        conf = {
            'denovo': {
                'denovo_filename': denovo_filename,
                'family_filename': family_filename,
            }
        }
        return Configure(conf)
