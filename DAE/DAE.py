import os
from VariantsDB import VariantsDB 
from GeneInfoDB import GeneInfoDB 
import phenoDB 
from Sfari import SfariCollection

daeDir = os.environ['DAE_DB_DIR']

giDB = GeneInfoDB(daeDir + "/geneInfo.conf", daeDir)
sfriDB = SfariCollection(os.environ['PHENO_DB_DIR'])
phDB = phenoDB.rawTableFactory('str_zlib5.h5') 
vDB = VariantsDB(daeDir,sfriDB=sfriDB,giDB=giDB)

if __name__ == "__main__":
    print "hi"
