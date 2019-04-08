#!/usr/bin/env python

'''
Created on Jun 10, 2017

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals
from builtins import object
import os


class RegenerateTestDataset(object):

    def __init__(self):
        self.DAE_SOURCE_DIR = os.getenv("DAE_SOURCE_DIR", None)
        self.WDAE_SOURCE_DIR = os.path.join(
            self.DAE_SOURCE_DIR,
            "..",
            "wdae"
        )
        self.DAE_DB_DIR = os.getenv("DAE_DB_DIR", None)
        self.TOOLS_DIR = os.path.join(
            self.DAE_SOURCE_DIR,
            "tools"
        )
        self.DATA_IMPORT_TEST = os.path.join(
            self.DAE_SOURCE_DIR,
            "tests",
            "data_import_test"
        )

        self.OUTDIR = os.path.join(
            self.DAE_DB_DIR,
            "testSt",
        )
        if not os.path.exists(self.OUTDIR):
            os.makedirs(self.OUTDIR)

        self.NUC_PED = os.path.join(
            self.OUTDIR,
            "nuc-fam.ped"
        )

        assert os.path.exists(self.OUTDIR)

    def generate_pedigree_nuc(self):
        infile = os.path.join(
            self.DATA_IMPORT_TEST,
            "fam.ped"
        )
        tool = os.path.join(
            self.TOOLS_DIR,
            "ped2NucFam.py"
        )
        assert os.path.exists(tool)
        assert os.path.exists(infile)

        command = "{} {} {}".format(
            tool,
            infile,
            self.NUC_PED
        )

        print("Executing {}".format(command))
        os.system(command)

    def generate_denovo_variants(self):
        infile = os.path.join(
            self.DATA_IMPORT_TEST,
            "denovo.csv"
        )
        outfile = os.path.join(
            self.OUTDIR,
            "dnvNuc"
        )
        tool = os.path.join(
            self.TOOLS_DIR,
            "dnv2DAE.py"
        )
        assert os.path.exists(tool)
        assert os.path.exists(infile)

        command = \
            "{} {} {} -m , -i SP_id -c CHROM -p POS -r REF -a ALT -o {}"\
            .format(
                tool,
                self.NUC_PED,
                infile,
                outfile
            )

        print("Executing {}".format(command))
        os.system(command)

    def generate_pheno_db(self):
        instruments = os.path.join(
            self.DATA_IMPORT_TEST,
            'instruments',
        )

        outfile = os.path.join(
            self.OUTDIR,
            "test.db"
        )

        tool = os.path.join(
            self.TOOLS_DIR,
            "pheno2dae.py"
        )

        assert os.path.exists(tool)
        assert os.path.exists(instruments)

        command = "{} -v -f {} -i {} -o {}".format(
            tool,
            self.NUC_PED,
            instruments,
            outfile
        )

        print("Executing {}".format(command))
        os.system(command)

    def generate_vcf_variants(self, vcffiles, out):
        tool = os.path.join(
            self.TOOLS_DIR,
            "vcf2DAE.py"
        )
        infiles = [
            os.path.join(
                self.DATA_IMPORT_TEST,
                f
            ) for f in vcffiles
        ]

        outfile = os.path.join(
            self.OUTDIR,
            out
        )

        assert os.path.exists(tool)
        print(infiles)

        assert all([os.path.exists(f) for f in infiles])

        command = "{} {} {} -o {}".format(
            tool,
            self.NUC_PED,
            ",".join(infiles),
            outfile
        )
        print("Executing {}".format(command))
        os.system(command)

    def generate_pheno_browser_cache(self):
        os.chdir(self.WDAE_SOURCE_DIR)
        command = "./manage.py pheno_browser_cache -p testSt"

        print("Executing {}".format(command))
        os.system(command)


def main():
    generator = RegenerateTestDataset()
    generator.generate_pedigree_nuc()
    generator.generate_denovo_variants()
    generator.generate_pheno_db()
    generator.generate_vcf_variants(
        ["calls.vcf.gz"], "tmNuc")
    generator.generate_vcf_variants(
        ["fam1.vcf", "fam2.vcf", "fam3.vcf"], "tmSmallNucFam")
    generator.generate_pheno_browser_cache()


if __name__ == "__main__":
    main()
