import unittest
import logging

from get_variants import parse_cli_arguments
from query_variants import do_query_variants, join_line

logger = logging.getLogger(__name__)


@unittest.skip
class GetVariantsTests(unittest.TestCase):
    def perform_query(self, args):
        args_dict = parse_cli_arguments(args)
        return do_query_variants(args_dict)

    def compare_variants_to_data_file(self, generator, data_file):
        count = 0
        mismatch = 0
        for v in generator:
            vline = join_line(v, '\t')
            dline = data_file.readline()
            if vline != dline:
                mismatch += 1
                if mismatch < 10:
                    logger.error('lines %d mismatched\ndl:<|%s|>\nvl:<|%s|>', count, dline, vline)
            count += 1
        if mismatch > 0:
            logger.error('number of mismatched lines: %d', mismatch)
        self.assertEqual(0, mismatch)

    def assert_variants_to_data_file(self, args, filename):
        generator = self.perform_query(args)
        data_file = open(filename, "r")
        self.compare_variants_to_data_file(generator, data_file)

    def test_denovo_single_gene_sym_not_found(self):
        args = ['--denovoStudies=wig781',
                '--geneSym=HBB',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_single_gene_sym_not_found.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_single_gene_sym(self):
        args = ['--denovoStudies=wig781',
                '--geneSym=POGZ',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_single_gene_sym.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_wig781(self):
        args = ['--denovoStudies=wig781',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_wig781.test'
        self.assert_variants_to_data_file(args, filename)

    def test_transmitted_with_region_wig781(self):
        args = ['--effectTypes=none',
                '--transmittedStudy=wig781',
                '--regionS', '1:1000000-2000000']
        filename = 'data/transmitted_with_region_wig781.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_wig873(self):
        args = ['--denovoStudies=wig873',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_wig873.test'
        self.assert_variants_to_data_file(args, filename)

    def test_transmitted_with_region_wig873(self):
        args = ['--effectTypes=none',
                '--transmittedStudy=wig873',
                '--regionS', '1:1000000-2000000']
        filename = 'data/transmitted_with_region_wig873.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_wig683(self):
        args = ['--denovoStudies=wig683',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_wig683.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_wigState322(self):
        args = ['--denovoStudies=wigState322',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_wigState322.test'
        self.assert_variants_to_data_file(args, filename)

    def test_transmitted_with_region_wigState322(self):
        args = ['--effectTypes=none',
                '--transmittedStudy=wigState322',
                '--regionS', '1:1000000-2000000']
        filename = 'data/transmitted_with_region_wigState322.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_wigState333(self):
        args = ['--denovoStudies=wigState333',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_wigState333.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_StateWE2012(self):
        args = ['--denovoStudies=StateWE2012',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_StateWE2012.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_wigStateWE2012(self):
        args = ['--denovoStudies=wigStateWE2012',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_wigStateWE2012.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_EichlerWE2012(self):
        args = ['--denovoStudies=EichlerWE2012',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_EichlerWE2012.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_wigEichlerWE2012(self):
        args = ['--denovoStudies=wigEichlerWE2012',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_wigEichlerWE2012.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_EichlerTG2012(self):
        args = ['--denovoStudies=EichlerTG2012',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_EichlerTG2012.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_DalyWE2012(self):
        args = ['--denovoStudies=DalyWE2012',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_DalyWE2012.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_IossifovWE2012(self):
        args = ['--denovoStudies=IossifovWE2012',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_IossifovWE2012.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_KarayiorgouWE2012(self):
        args = ['--denovoStudies=KarayiorgouWE2012',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_KarayiorgouWE2012.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_combSSCWE(self):
        args = ['--denovoStudies=combSSCWE',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_combSSCWE.test'
        self.assert_variants_to_data_file(args, filename)

    def test_transmitted_with_region_w873e374s322(self):
        args = ['--effectTypes=none',
                '--transmittedStudy=w873e374s322',
                '--regionS', '1:1000000-2000000']
        filename = 'data/transmitted_with_region_w873e374s322.test'
        self.assert_variants_to_data_file(args, filename)

    def test_transmitted_with_gene_sym_list_w873e374s322(self):
        args = ['--effectTypes=none', 
                '--transmittedStudy=w873e374s322', 
                '--geneSym', '"OSBPL8,DIP2C,FAM49A,AGPAT3"']
        filename = 'data/transmitted_with_gene_sym_list_w873e374s322.test' 
        self.assert_variants_to_data_file(args, filename)

