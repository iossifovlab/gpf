'''
Created on Sep 16, 2015

@author: lubo
'''
from random import randint


FAMILY_VARIANTS_CREATE_TABLE = '''
DROP TABLE IF EXISTS `transmitted_familyvariant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transmitted_familyvariant` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `family_id` varchar(16) NOT NULL,
  `best` varchar(16) NOT NULL,
  `counts` varchar(64) NOT NULL,
  `in_mom` tinyint(1) NOT NULL,
  `in_dad` tinyint(1) NOT NULL,
  `in_prb` tinyint(1) NOT NULL,
  `in_prb_gender` varchar(1) DEFAULT NULL,
  `in_sib` tinyint(1) NOT NULL,
  `in_sib_gender` varchar(1) DEFAULT NULL,
  `summary_variant_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `transmitted_familyvariant_0caa70f7` (`family_id`),
  KEY `transmitted_familyvariant_fd9ab97c` (`summary_variant_id`),
  CONSTRAINT `D1b9d36c68906398c84f8ef06314d61c`
  FOREIGN KEY (`summary_variant_id`)
  REFERENCES `transmitted_summaryvariant` (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
'''

FAMILY_VARIANTS_BEGIN_DUMPING_DATA = '''
--
-- Dumping data for table `transmitted_familyvariant`
--

LOCK TABLES `transmitted_familyvariant` WRITE;
/*!40000 ALTER TABLE `transmitted_familyvariant` DISABLE KEYS */;
'''

FAMILY_VARIANTS_END_DUMPING_DATA = '''
/*!40000 ALTER TABLE `transmitted_familyvariant` ENABLE KEYS */;
UNLOCK TABLES;

'''

FAMILY_VARIANTS_INSERT_BEGIN = \
    '''INSERT INTO `transmitted_familyvariant` VALUES '''

FAMILY_VARIANTS_VALUES = \
    '''( %(id)d, '%(family_id)s', '%(best)s', '%(counts)s',''' \
    ''' %(in_mom)d, %(in_dad)d, %(in_prb)d, '%(in_prb_gender)s',''' \
    ''' %(in_sib)d,''' \
    ''' '%(in_sib_gender)s', %(summary_variant_id)d)'''

SUMMARY_VARIANTS_MAX_ID = 1415355
SUMMARY_VARIANTS_MIN_ID = 1

FAMILY_ID_MAX_ID = 13000
FAMILY_ID_MIN_ID = 10000

FAMILY_VARIANTS_PER_SUMMARY_VARIANT = 3
BATCH_SIZE = 70


def generate_random_family():
    res = randint(FAMILY_ID_MIN_ID, FAMILY_ID_MAX_ID)
    return "%d" % res


def generate_family_variant(fvid, svid):
    res = {'id': fvid,
           'summary_variant_id': svid,
           'family_id': generate_random_family(),
           'best': '001/110',
           'counts': '001/110',
           'in_mom': 0,
           'in_dad': 1,
           'in_prb': 1,
           'in_sib': 0,
           'in_prb_gender': 'M',
           'in_sib_gender': 'F'}
    return FAMILY_VARIANTS_VALUES % res


def generate_family_variants_insert_batch(svid, fvid, batch_size=1000):
    family_variants = []
    for _i in xrange(1, batch_size):
        fvid += 1
        fv = generate_family_variant(fvid, svid)
        family_variants.append(fv)
    return (fvid, '%s %s;' % (FAMILY_VARIANTS_INSERT_BEGIN,
                              ','.join(family_variants)))

if __name__ == '__main__':
    print(FAMILY_VARIANTS_CREATE_TABLE)
    print(FAMILY_VARIANTS_BEGIN_DUMPING_DATA)

    fvid = 0
    for svid in xrange(1, SUMMARY_VARIANTS_MAX_ID + 1):
        for _ in xrange(1, 2):
            (fvid, insert_statement) = \
                generate_family_variants_insert_batch(svid, fvid, BATCH_SIZE)
            print(insert_statement)

    print(FAMILY_VARIANTS_END_DUMPING_DATA)
