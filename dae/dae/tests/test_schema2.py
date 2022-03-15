import sys
import logging 
import json 

from dae.utils.variant_utils import mat2str, str2mat
from dae.genomic_resources.gene_models import load_gene_models_from_file
from dae.backends.schema2.bigquery_variants import BigQueryVariants 
from dae.backends.schema2.impala_variants import ImpalaVariants
from dae.backends.impala.impala_variants import ImpalaVariants as ImpalaVariants1 
from dae.backends.impala.impala_helpers import ImpalaHelpers

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

        # DEBUG
        if fv.family_id == 'SF0002235' and fv.location == '1:1233891':
            print(row)


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
        gm)

    b2 = BigQueryVariants(
        "data-innov", 
        "schema2", 
        "imported_summary_alleles",
        "imported_family_alleles",
        "imported_pedigree",
        gm)

    logger.info("101, gene")
   
    # - make sure this works, extend to more queries
    # - use queries from benchmark tool 
    # - reference vs unknown. load vs display variants that are ref.allele. 
    # - case when some of the members unknown genotype. 
    # - in serialization + storage consider "continue" on reference alleles 
    # - families and queries 

    queries = [
        {'genes':['MIR200B']},
        {'effect_types':['intergenic']}
        ]

    for query in queries:
        truth = list(i1.query_variants(**query)) 
        bq = list(b2.query_variants(**query))
        im = list(i2.query_variants(**query)) 
 
        print("TRUTH \t[schema1]", len(truth))
        print("BIG_Q \t[schema2]", len(bq))
        print("IMPALA\t[schema2]", len(im))

        record_diff("TRUTH vs IMPALA", truth, im) 
        record_diff("TRUTH vs BQ", truth, bq)

