'''
Created on Aug 28, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
from DAE import vDB
import gzip
from VariantsDB import parseGeneEffect


GENE_EFFECT_VARIANTS_CREATE_TABLE = '''
--
-- Table structure for table `transmitted_geneeffectvariant`
--

DROP TABLE IF EXISTS `transmitted_geneeffectvariant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transmitted_geneeffectvariant` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `symbol` varchar(32) DEFAULT NULL,
  `effect_type` varchar(32) NOT NULL,
  `variant_type` varchar(4) NOT NULL,
  `n_par_called` int(11) NOT NULL,
  `n_alt_alls` int(11) NOT NULL,
  `alt_freq` double NOT NULL,
  `summary_variant_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `transmitted_geneeffectvariant_97bff268` (`symbol`),
  KEY `transmitted_geneeffectvariant_91ca6089` (`effect_type`),
  KEY `transmitted_geneeffectvariant_fd9ab97c` (`summary_variant_id`),
  CONSTRAINT `d3a6ab47e8f9acff1fd095bac97aa175`
  FOREIGN KEY (`summary_variant_id`)
  REFERENCES `transmitted_summaryvariant` (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

'''

GENE_EFFECT_VARIANTS_BEGIN_DUMPING_DATA = '''
--
-- Dumping data for table `transmitted_geneeffectvariant`
--

LOCK TABLES `transmitted_geneeffectvariant` WRITE;
/*!40000 ALTER TABLE `transmitted_geneeffectvariant` DISABLE KEYS */;
'''

GENE_EFFECT_VARIANTS_END_DUMPING_DATA = '''
/*!40000 ALTER TABLE `transmitted_geneeffectvariant` ENABLE KEYS */;
UNLOCK TABLES;


'''

GENE_EFFECT_VARIANTS_INSERT_BEGIN = \
    '''INSERT INTO `transmitted_geneeffectvariant` VALUES %s ;'''

GENE_EFFECT_VARIANTS_VALUES = \
    '''( %(id)d, %(symbol)s, "%(effect_type)s", "%(variant_type)s", ''' \
    '''  %(n_par_called)d, %(n_alt_alls)d, %(alt_freq)f, ''' \
    '''  %(summary_variant_id)d )'''


class Command(BaseCommand):
    args = '<study_name>'
    help = '''Importst summary variants from transmitted study <study_name>
    into the SQL database.'''

    @staticmethod
    def safe_float(s):
        if s.strip() == '':
            return None
        else:
            return float(s)

    def get_summary_filename(self, study_name):
        study = vDB.get_study(study_name)

        summary_filename = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.indexFile') + ".txt.bgz"
        return summary_filename

    def create_effect_variant_dict(self, vals, vrow, erow):
        gene_effects = parseGeneEffect(vals['effectGene'])
        variant_type = vals['variant'][0:3]

        if len(gene_effects) == 0 and vals['effectGene'] == 'intergenic':
            erow += 1
            return erow, [{
                'id': erow,
                'symbol': 'NULL',
                'effect_type': 'intergenic',
                'variant_type': variant_type,
                'n_par_called': int(vals['all.nParCalled']),
                'n_alt_alls': int(vals['all.nAltAlls']),
                'alt_freq': float(vals['all.altFreq']),
                'summary_variant_id': vrow,
            }]

        res = []
        for ge in gene_effects:
            erow += 1
            eres = {
                'id': erow,
                'symbol': '"%s"' % ge['sym'],
                'effect_type': ge['eff'],
                'variant_type': variant_type,
                'n_par_called': int(vals['all.nParCalled']),
                'n_alt_alls': int(vals['all.nAltAlls']),
                'alt_freq': float(vals['all.altFreq']),
                'summary_variant_id': vrow,
            }
            res.append(eres)
        return erow, res

    def handle(self, *args, **options):
        if(len(args) != 1):
            raise CommandError('Exactly one argument expected')

        study_name = args[0]
        print("Working with transmitted study: {}".format(study_name))

        summary_filename = self.get_summary_filename(study_name)
        with gzip.open(summary_filename, 'r') as fh, \
                open('gene_effect_variants_innodb.sql', 'w') as outfile:

            column_names = fh.readline().rstrip().split('\t')

            outfile.write(GENE_EFFECT_VARIANTS_CREATE_TABLE)
            outfile.write('\n')
            outfile.write(GENE_EFFECT_VARIANTS_BEGIN_DUMPING_DATA)
            outfile.write('\n')

            vrow = 1
            erow = 1
            ins_line = []
            for line in fh:
                data = line.strip("\r\n").split("\t")
                vals = dict(zip(column_names, data))
                erow, evvals = \
                    self.create_effect_variant_dict(vals, vrow, erow)
                ins_values = [GENE_EFFECT_VARIANTS_VALUES % ev
                              for ev in evvals]
                ins_line.extend(ins_values)
                vrow += 1
                if vrow % 100 == 0:
                    outfile.write(GENE_EFFECT_VARIANTS_INSERT_BEGIN %
                                  ', '.join(ins_line))
                    outfile.write('\n')
                    ins_line = []
                    print("line: {}".format(vrow))

            outfile.write(GENE_EFFECT_VARIANTS_END_DUMPING_DATA)
            outfile.write('\n')
