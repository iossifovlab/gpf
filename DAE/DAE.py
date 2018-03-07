import os
from VariantsDB import VariantsDB 
from VariantsDB import mat2Str 
from VariantsDB import str2Mat 
from VariantsDB import viewVs 
from VariantsDB import safeVs
from VariantsDB import _safeVs
from Variant import isVariant
from Variant import normalRefCopyNumber
from GeneInfoDB import GeneInfoDB
from GeneTerms import loadGeneTerm 
# import phenoDB
from Sfari import SfariCollection
from GenomesDB import GenomesDB

from Config import *
from pheno.pheno_factory import PhenoFactory
config = Config()

giDB = GeneInfoDB(config.geneInfoDBconfFile, config.daeDir, config.data_dir)
sfariDB = SfariCollection(config.sfariDBdir)
# phDB = phenoDB.rawTableFactory(config.phenoDBFile)
genomesDB = GenomesDB(config.daeDir, config.genomesDBconfFile, config.data_dir)

vDB = VariantsDB(config.daeDir, 
                 data_dir=config.data_dir, 
                 confFile=config.variantsDBconfFile,
                 sfariDB=sfariDB, 
                 giDB=giDB, phDB=None, genomesDB=genomesDB)


def get_gene_sets_symNS(geneSetsDef, denovoStudies=None):
    if geneSetsDef == 'denovo':
        geneTerms = vDB.get_denovo_sets(denovoStudies)
    else:
        try:
            geneTerms = giDB.getGeneTerms(geneSetsDef)
        except:
            geneTerms = loadGeneTerm(geneSetsDef)
 
        if geneTerms.geneNS == 'id':
            def rF(x):
                if x in giDB.genes:
                    return giDB.genes[x].sym
            geneTerms.renameGenes("sym", rF)
 
        if geneTerms.geneNS != 'sym':
            raise Exception('Only work with id or sym namespace')
    return geneTerms

pheno = PhenoFactory()


if __name__ == "__main__":
    print "hi"
