import os
from VariantsDB import VariantsDB 
from VariantsDB import mat2Str 
from VariantsDB import str2Mat 
from VariantsDB import viewVs 
from VariantsDB import safeVs
from VariantsDB import _safeVs
from VariantsDB import isVariant
from VariantsDB import normalRefCopyNumber 
from GeneInfoDB import GeneInfoDB
import phenoDB
from Sfari import SfariCollection

from Config import *
config = Config()

giDB = GeneInfoDB(config.geneInfoDBconfFile, config.daeDir)
sfriDB = SfariCollection(config.sfriDBdir)
phDB = phenoDB.rawTableFactory(config.phenoDBFile)
vDB = VariantsDB(config.daeDir, config.variantsDBconfFile, sfriDB=sfriDB, giDB=giDB)

if __name__ == "__main__":
    print "hi"
