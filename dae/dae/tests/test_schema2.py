import sys
import logging 
import json 

from dae.utils.variant_utils import mat2str, str2mat
from dae.genomic_resources.gene_models import load_gene_models_from_file
from dae.backends.schema2.bigquery_variants import BigQueryVariants 
from dae.backends.schema2.impala_variants import ImpalaVariants
from dae.backends.impala.impala_variants import ImpalaVariants as ImpalaVariants1 
from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.utils.regions import Region 

GENE = {'MEGF6'}

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


# Schema 1 - row is family schema1 contains subset of alleles that affect the family 
# Schema 2 - row is join from summary & family 

# count results 
def count_rows(iter):
    logger.info(f"COUNT: {sum(1 for _ in iter)}")
    iter.close()

# gather subset of fields to compare BigQuery sets and Impala sets
def fv_to_record(iter):
    rows = []
    for fv in iter:
        row = {
            'location': fv.location,
            # 'summary_variant': str(fv.summary_variant),
            'family_id': fv.family_id,
            'best_state': mat2str(fv.gt),
            'family_variant': str(fv)
        }

        rows.append(json.dumps(row, sort_keys=True))

    # set(tuple(loca..) 
    # return pd.DataFrame(rows)
    return set(rows) 


def record_diff(tag, control, db):
    control = fv_to_record(control)
    db = fv_to_record(db)

    excess_control = control.difference(db)
    excess_db = db.difference(control)
    
    
    logger.info(tag) 
    logger.info(f'CONTROL - DB {len(excess_control)}')
    logger.info(f'DB - CONTROL {len(excess_db)}')
    logger.info(f'DB AND CONTROL {len(db & control)}')

    if excess_control:
        print(list(excess_control)[:10])

    if excess_db:
        print(list(excess_db)[:10])


if __name__ == "__main__":
    import pprint 

    logger.info("BigQuery vs Impala Benchmark")
    logger.info("Loading Gene Model (from file)")
    gm = load_gene_models_from_file('./reference/refGene-20190211.gz')
    # get gm from gpf_instance 

    i1 = ImpalaVariants1(
        ImpalaHelpers(["localhost"], 21050), 
        "data_hg19_empty",
        "schema1_variants", 
        "schema1_pedigree",
        gm)

    i2 = ImpalaVariants(
        ImpalaHelpers(["localhost"], 21050), 
        "gpf_schema2",
        "imported_family_alleles", 
        "imported_summary_alleles",
        "imported_pedigree",
        "imported_meta",
        gm)

    b2 = BigQueryVariants(
        "data-innov", 
        "schema2", 
        "imported_summary_alleles",
        "imported_family_alleles",
        "imported_pedigree",
        "imported_meta",
        gm)

    logger.info("101, gene")
   
    # - make sure this works, extend to more queries
    # - use queries from benchmark tool 
    # - reference vs unknown. load vs display variants that are ref.allele. 
    # - case when some of the members unknown genotype. 
    # - in serialization + storage consider "continue" on reference alleles 
    # - families and queries 
    GENES_MULTIPLE = [
        'SCNN1D', 'MIR6808', 'TTLL10', 'B3GALT6', 'MIR6727', 
        'C1QTNF12', 'ACAP3', 'MIR429', 'SDF4', 'MIR200B']

    FAMILY_IDS = [
        'SF0001111', 'SF0010429', 'SF0034120', 'SF0027065', 'SF0000691', 
        'SF0025437', 'SF0047329', 'SF0045260', 'SF0035260', 'SF0000076']
    
    CUSTOM_EFFECT_TYPES = ['splice-site', 'frame-shift', 'nonsense']
    
    CUSTOM_EFFECT_TYPES_2 = [
        'splice-site', 'frame-shift', 'nonsense',
        'no-frame-shift-newStop',
        'noStart', 'noEnd', 'missense', 'no-frame-shift', 'CDS']

    CODING_EFFECT_TYPES = [
       'splice-site',
        'frame-shift',
        'nonsense',
        'no-frame-shift-newStop',
        'noStart',
        'noEnd',
        'missense',
        'no-frame-shift',
        'CDS',
        'synonymous',
        'coding_unknown',
        'regulatory',
        "3'UTR",
        "5'UTR"]

    queries = [
        {
            'genes':GENES_MULTIPLE
        },
        {
            'effect_types':['intergenic']
        },
        {
            'effect_types':CUSTOM_EFFECT_TYPES,
            'ultra_rare':True
        },
        {
            'genes':GENES_MULTIPLE,
            'effect_types':CUSTOM_EFFECT_TYPES,
            'ultra_rare':True
        },
        {
            'genes':GENES_MULTIPLE,
            'effect_types':CUSTOM_EFFECT_TYPES + ['no-frame-shift-newStop'],
            'ultra_rare':True,
            'roles':'prb'
        },
        {
            'family_ids':FAMILY_IDS[:1],
            'real_attr_filter':[('af_allele_freq', (None, 1))],
            'effect_types':CUSTOM_EFFECT_TYPES_2 
        },
        {
            'family_ids':FAMILY_IDS,
            'real_attr_filter':[('af_allele_freq', (None, 1))],
            'effect_types':CODING_EFFECT_TYPES
        }
    ]

    queries = [
        {
            'family_ids':FAMILY_IDS[:1],
            'regions':[Region.from_str('1:1100001-1210000')]
        }
    ]

    # revive partitions, 
    # right now 1 parquet for all variants 
    # multiple parquet files - study schema 1 partition schema
    # port it to schema 2. write dataset incrementally (check in pa documentation) 

    for query in queries:
        print("Test:")
        print(query)
        print("=" * 40) 

        truth = list(i1.query_variants(**query)) 
        bq = list(b2.query_variants(**query))
        im = list(i2.query_variants(**query)) 
 
        print("TRUTH \t[schema1]", len(truth))
        print("BIG_Q \t[schema2]", len(bq))
        print("IMPALA\t[schema2]", len(im))

        record_diff("TRUTH vs IMPALA", truth, im) 
        record_diff("TRUTH vs BQ", truth, bq)

