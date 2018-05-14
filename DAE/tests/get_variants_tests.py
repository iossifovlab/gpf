from __future__ import print_function
from builtins import zip
import unittest
import logging

from get_variants import parse_cli_arguments, get_variants
from query_variants import join_line

logger = logging.getLogger(__name__)


class GetVariantsTests(unittest.TestCase):
    def perform_query(self, args):
        args_dict = parse_cli_arguments(args)
        return get_variants(args_dict)

    def compare_variant_lines(self, vl, dl):
        vs = vl.split('\t')
        ds = dl.split('\t')
        self.assertEquals(len(vs), len(ds))
        pairs = list(zip(vs, ds))
        for (v, d) in pairs:
            v1 = v.strip()
            d1 = d.strip()
            if v1 == d1:
                continue
            try:
                v2 = float(v1)
                d2 = float(d1)
                if v2 != d2:
                    print("{}!={}".format(v, d))
                    return False
            except ValueError:
                print("{}!={}".format(v, d))
                return False
        return True

    def compare_variants_to_data_file(self, generator, filename):
        with open(filename, "r") as data_file:
            count = 0
            mismatch = 0
            for v in generator:
                vline = join_line(v, '\t')
                dline = data_file.readline()
                if not self.compare_variant_lines(vline, dline):
                    mismatch += 1
                    if mismatch < 10:
                        logger.error('lines %d mismatched\n'
                                     'dl:<|%s|>\nvl:<|%s|>',
                                     count, dline, vline)
                count += 1
            if mismatch > 0:
                logger.error('number of mismatched lines: %d', mismatch)
            self.assertEqual(0, mismatch)

    def store_variants_to_data_file(self, generator, filename):
        with open(filename, 'w') as data_file:
            for v in generator:
                vline = join_line(v, '\t')
                data_file.write(vline)
                # data_file.write('\n')

    def assert_variants_to_data_file(self, args, filename):
        generator = self.perform_query(args)
        res = [v for v in generator]
        res.sort()
        # self.store_variants_to_data_file(generator, filename)
        self.compare_variants_to_data_file(generator, filename)

    def test_denovo_single_gene_sym_not_found(self):
        args = ['--denovoStudies=IossifovWE2014',
                '--geneSym=HBB',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_single_gene_sym_not_found.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_single_gene_sym(self):
        args = ['--denovoStudies=IossifovWE2014',
                '--geneSym=POGZ',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_single_gene_sym.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_IossifovWE2014(self):
        args = ['--denovoStudies=IossifovWE2014',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_IossifovWE2014.test'
        self.assert_variants_to_data_file(args, filename)

    def test_transmitted_with_region_w1202s766e611(self):
        args = ['--effectTypes=none',
                '--transmittedStudy=w1202s766e611',
                '--regionS=1:1000000-2000000']
        filename = 'data/transmitted_with_region_w1202s766e611.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_StateWE2012(self):
        args = ['--denovoStudies=StateWE2012',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_StateWE2012.test'
        self.assert_variants_to_data_file(args, filename)

    def test_denovo_defaults_EichlerWE2012(self):
        args = ['--denovoStudies=EichlerWE2012',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_EichlerWE2012.test'
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

    def test_denovo_defaults_ALL_SSC(self):
        args = ['--denovoStudies=ALL SSC',
                '--effectTypes=none',
                '--transmittedStudy=none']
        filename = 'data/denovo_defaults_ALL_SSC.test'
        self.assert_variants_to_data_file(args, filename)

    def test_transmitted_with_gene_sym_list_w1202s766e611(self):
        args = ['--effectTypes=none',
                '--transmittedStudy=w1202s766e611',
                '--geneSym=OSBPL8,DIP2C,FAM49A,AGPAT3']
        filename = 'data/transmitted_with_gene_sym_list_w1202s766e611.test'
        self.assert_variants_to_data_file(args, filename)
