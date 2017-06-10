#!/usr/bin/env python

'''
Created on Jun 10, 2017

@author: lubo
'''
import os


class RegenerateTestDataset(object):

    def __init__(self):
        self.DAE_SOURCE_DIR = os.getenv("DAE_SOURCE_DIR", None)
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

    def generate_pedigree_nuc(self):
        infile = os.path.join(
            self.DATA_IMPORT_TEST,
            "fam.ped"
        )
        outfile = os.path.join(
            self.OUTDIR,
            "nuc-fam.ped"
        )
        self.NUC_PED = outfile

        tool = os.path.join(
            self.TOOLS_DIR,
            "ped2NucFam.py"
        )
        assert os.path.exists(tool)
        assert os.path.exists(infile)

        command = "{} {} {}".format(
            tool,
            infile,
            outfile
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
            "pheno2DAE.py"
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


def main():
    generator = RegenerateTestDataset()
    generator.generate_pedigree_nuc()
    generator.generate_denovo_variants()
    generator.generate_pheno_db()


if __name__ == "__main__":
    main()
