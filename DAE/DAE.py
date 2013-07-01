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

#vdb/
#    geneinfodb  phenodb  variantdb

daeDir = os.environ['DAE_DB_DIR']
phenoSubDir = os.environ['PHENO_DB_DIR']

variantDir = os.path.join(daeDir, "variantdb")
giDir = os.path.join(daeDir, "geneinfodb")
phenoDir = os.path.join(daeDir, "phenodb", phenoSubDir)

geneInfoConfFilename = os.path.join(giDir,"geneInfo.conf")

giDB = GeneInfoDB(geneInfoConfFilename, giDir)
sfriDB = SfariCollection(phenoDir)
phDB = phenoDB.rawTableFactory('str_zlib5.h5') 
vDB = VariantsDB(daeDir, sfriDB=sfriDB, giDB=giDB)

if __name__ == "__main__":
    print "hi"
