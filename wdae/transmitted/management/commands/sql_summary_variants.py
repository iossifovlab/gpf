'''
Created on Aug 28, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
from DAE import vDB
import gzip
from VariantsDB import Variant, parseGeneEffect

SUMMARY_VARIANTS_CREATE_TABLE = '''
--
-- Table structure for table `transmitted_summaryvariant`
--

DROP TABLE IF EXISTS `transmitted_summaryvariant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transmitted_summaryvariant` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ln` int(11) NOT NULL,
  `chrome` varchar(3) NOT NULL,
  `position` int(11) NOT NULL,
  `variant` varchar(45) NOT NULL,
  `variant_type` varchar(4) NOT NULL,
  `effect_type` varchar(32) DEFAULT NULL,
  `effect_gene` varchar(32) DEFAULT NULL,
  `effect_gene_all` varchar(255) DEFAULT NULL,
  `effect_count` int(11) NOT NULL,
  `effect_details` varchar(255) DEFAULT NULL,
  `n_par_called` int(11) NOT NULL,
  `n_alt_alls` int(11) NOT NULL,
  `alt_freq` double NOT NULL,
  `prcnt_par_called` double NOT NULL,
  `seg_dups` int(11) NOT NULL,
  `hw` double NOT NULL,
  `ssc_freq` double DEFAULT NULL,
  `evs_freq` double DEFAULT NULL,
  `e65_freq` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `transmitted_summaryvariant_f8e19f44` (`ln`),
  KEY `transmitted_summaryvariant_554838a8` (`chrome`),
  KEY `transmitted_summaryvariant_91ca6089` (`effect_type`),
  KEY `transmitted_summaryvariant_7f96c587` (`effect_gene`)
) ENGINE=InnoDB AUTO_INCREMENT=1415356 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
'''

SUMMARY_VARIANTS_BEGIN_DUMPING_DATA = '''
--
-- Dumping data for table `transmitted_summaryvariant`
--

LOCK TABLES `transmitted_summaryvariant` WRITE;
/*!40000 ALTER TABLE `transmitted_summaryvariant` DISABLE KEYS */;
'''

SUMMARY_VARIANTS_END_DUMPING_DATA = '''
/*!40000 ALTER TABLE `transmitted_summaryvariant` ENABLE KEYS */;
UNLOCK TABLES;
'''

SUMMARY_VARIANTS_INSERT_BEGIN = \
    '''INSERT INTO `transmitted_summaryvariant` VALUES %s ;'''

SUMMARY_VARIANTS_VALUES = \
    '''( %(id)d, %(ln)d, '%(chrome)s', %(position)d, ''' \
    ''' '%(variant)s', '%(variant_type)s', ''' \
    ''' '%(effect_type)s', '%(effect_gene)s', '%(effect_gene_all)s', ''' \
    ''' %(effect_count)d, '%(effect_details)s', ''' \
    ''' %(n_par_called)d', %(n_alt_alls)d, %(alt_freq)d, ''' \
    ''' %(prcnt_par_called)f, %(seg_dups)d, %(hw)f, ''' \
    ''' %(ssc_freq)s, %(evs_freq)s, %(e65_freq)s )'''


class Command(BaseCommand):
    args = '<study_name>'
    help = '''Importst summary variants from transmitted study <study_name>
    into the SQL database.'''

    def create_summary_variant_dict(self, nrow, vals, evvals):
        res = {
            'id': nrow,
            'ln': nrow,
            'chrome': vals['chr'],
            'position': int(vals['position']),
            'variant': vals['variant'],
            'variant_type': vals['variant'][:3],
            'effect_type': evvals[0]['effect_type'] if evvals else 'NULL',
            'effect_gene': evvals[0]['symbol'] if evvals else 'NULL',
            'effect_gene_all': vals['effectGene'],
            'effect_count': len(evvals),
            'effect_details': vals['effectDetails'],
            'n_par_called': int(vals['all.nParCalled']),
            'n_alt_alls': int(vals['all.nAltAlls']),
            'alt_freq': float(vals['all.altFreq']),
            'prcnt_par_called': float(vals['all.prcntParCalled']),
            'seg_dups': int(vals['segDups']),
            'hw': float(vals['HW']),
            'ssc_freq': self.safe_float(vals['SSC-freq']),
            'evs_freq': self.safe_float(vals['EVS-freq']),
            'e65_freq': self.safe_float(vals['E65-freq']),
        }
        return res

    @staticmethod
    def safe_float(s):
        if s.strip() == '':
            return 'NULL'
        else:
            return s

    def get_summary_filename(self, study_name):
        study = vDB.get_study(study_name)

        summary_filename = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.indexFile') + ".txt.bgz"
        return summary_filename

    def create_summary_variant(self, vals):
        vals["location"] = vals["chr"] + ":" + vals["position"]
        v = Variant(vals)
        v.study = self.study
        if self.summary_row['n_alt_alls'] == 1:
            v.popType = 'ultraRare'
        else:
            v.popType = 'common'
        return v

    def create_effect_variant_dict(self, vals):
        gene_effects = parseGeneEffect(vals['effectGene'])
        variant_type = vals['variant'][0:3]

        if len(gene_effects) == 0 and vals['effectGene'] == 'intergenic':
            return [{
                'symbol': None,
                'effect_type': 'intergenic',
                'variant_type': variant_type,
                'n_par_called': int(vals['all.nParCalled']),
                'n_alt_alls': int(vals['all.nAltAlls']),
                'alt_freq': float(vals['all.altFreq']),
            }]

        res = []
        for ge in gene_effects:
            eres = {
                'symbol': ge['sym'],
                'effect_type': ge['eff'],
                'variant_type': variant_type,
                'n_par_called': int(vals['all.nParCalled']),
                'n_alt_alls': int(vals['all.nAltAlls']),
                'alt_freq': float(vals['all.altFreq']),
            }
            res.append(eres)
        return res

    def handle(self, *args, **options):
        if(len(args) != 1):
            raise CommandError('Exactly one argument expected')

        study_name = args[0]
        print("Working with transmitted study: {}".format(study_name))

        summary_filename = self.get_summary_filename(study_name)
        with gzip.open(summary_filename, 'r') as fh, \
                open('summary_variants_innod.sql', 'w') as outfile:

            column_names = fh.readline().rstrip().split('\t')

            outfile.write(SUMMARY_VARIANTS_CREATE_TABLE)
            outfile.write('\n')
            outfile.write(SUMMARY_VARIANTS_BEGIN_DUMPING_DATA)
            outfile.write('\n')

            nrow = 1

            for line in fh:
                data = line.strip("\r\n").split("\t")
                vals = dict(zip(column_names, data))
                evvals = self.create_effect_variant_dict(vals)
                svvals = self.create_summary_variant_dict(nrow, vals, evvals)
                ins_values = SUMMARY_VARIANTS_VALUES % svvals
                outfile.write(SUMMARY_VARIANTS_INSERT_BEGIN % ins_values)

                outfile.write('\n')
                nrow += 1
                if nrow % 1000 == 0:
                    print("line: {}".format(nrow))
