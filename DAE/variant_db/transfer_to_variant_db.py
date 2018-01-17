import traceback
import logging

from sqlalchemy import create_engine

from DAE import vDB
from variant_db.model import *
from variant_db.variant_query import Session

LOGGER = logging.getLogger(__name__)

class TransferToVariantDB:

    STR_TO_VARIANT_TYPE = {
        'sub' : VariantType.substitution,
        'ins' : VariantType.insertion,
        'del' : VariantType.deletion,
        'cnv' : VariantType.cnv,
        'com' : VariantType.complex
    }

    def __init__(self):
        self.session = Session(bind = create_engine(
                'mysql+mysqldb://{}:{}@{}:{}/{}'.format('seqpipe', 'lae0suNu', '127.0.0.1', '3306', 'variant_db')
                #'mysql+mysqldb://{}:{}@{}:{}/{}'.format(user, password, host, port, db)
            )
        )

    def transfer(self, study_name, limit):
        try:
            self._transfer(study_name, limit)
        except Exception as ex:
            print('Exception while transferring  variants to database: ')
            traceback.print_exc()
            print('Rolling back.')
            self.session.rollback()

    def _transfer(self, study_name, limit):
        LOGGER.debug('So it begins.')

        variant_ids = {}
        family_ids = {}
        person_ids = {}
        gene_ids = {}

        variant_id_seq = 1
        effect_id_seq = 1
        gene_id_seq = 1
        family_id_seq = 1
        person_id_seq = 1

        variants = []
        numeric_attributes = []
        genes = []
        effects = []
        families = []
        people = []
        family_members = []
        family_variants = []
        person_variants = []

        session = self.session
        study = vDB.get_study(study_name)
        variants_generator = study.get_transmitted_variants(maxAltFreqPrcnt=-1, limit=limit)
        count = 1
        ten_percent_count = limit / 10
        for old_variant in variants_generator:

            count += 1

            if (old_variant.atts['chr'], old_variant.atts['position'], old_variant.variant) in variant_ids:
                variant_id = variant_ids[(old_variant.atts['chr'], old_variant.atts['position'], old_variant.variant)]
            else:
                # create variant, numeric attributes, genes and effects
                # -------------------
                # variant
                variant_id = variant_id_seq
                variant_ids[(old_variant.atts['chr'], old_variant.atts['position'], old_variant.variant)] = variant_id
                variant_id_seq += 1
                variant = {
                    'id': variant_id,
                    'variant': old_variant.variant,
                    'variant_type': self.STR_TO_VARIANT_TYPE[old_variant.variant[:3]],
                    'location': old_variant.atts['position'],
                    'chromosome': old_variant.atts['chr'],
                    'effects_details': old_variant.atts['effectGene'],
                    'n_par_called': old_variant.atts['all.nParCalled'],
                    'n_alt_alls': old_variant.atts['all.nAltAlls'],
                    'prcnt_par_called': old_variant.atts['all.prcntParCalled'],
                    'alt_freq': old_variant.atts['all.altFreq']
                }
                variants.append(variant)
                # -------------------
                # numeric attributes
                for key in self.NUMERIC_ATTRIBUTES:
                    value = old_variant.atts.get(key, None)
                    if value is not None and value != '':
                        numeric_attributes.append({
                            'variant_id': variant_id,
                            'name': self.NUMERIC_ATTRIBUTES[key],
                            'value': value
                        })
                # -------------------
                # effects
                for gene_effect in [gene_effect.split(':')
                                    for gene_effect
                                    in old_variant.atts['effectGene'].split('|')]:
                    effect_type = gene_effect[-1]
                    if len(gene_effect) == 1:
                        gene_symbol = None
                    else:
                        gene_symbol = gene_effect[0]

                    # -------------------
                    # gene
                    if gene_symbol in gene_ids:
                        gene_id = gene_ids[gene_symbol]
                    elif gene_symbol is not None:
                        gene_id = gene_id_seq
                        gene_ids[gene_symbol] = gene_id
                        gene_id_seq += 1
                        genes.append({
                            'id': gene_id,
                            'symbol': gene_symbol
                        })
                    else:
                        gene_id = None

                    effect_id = effect_id_seq
                    effect_id_seq += 1
                    effects.append({
                        'id': effect_id,
                        'variant_id': variant_id,
                        'gene_id': gene_id,
                        'effect_type': EffectType(effect_type)
                    })
                    # -------------------
                    # worst effect id
                    if effect_type == old_variant.atts['effectType']:
                        variant['worst_effect_id'] = effect_id

            family_size = len(old_variant.memberInOrder)

            if old_variant.familyId in family_ids:
                family_id = family_ids[old_variant.familyId]
            else:
                family_id = family_id_seq
                family_ids[old_variant.familyId] = family_id
                family_id_seq += 1
                # -------------------
                # family
                families.append({
                    'id': family_id,
                    'family_ext_id': old_variant.familyId,
                    # TODO kids_count will work only for core families
                    'kids_count': family_size - 2
                })

                for index, member in enumerate(old_variant.memberInOrder):
                    person_id = person_id_seq
                    person_ids[member.personId] = person_id
                    person_id_seq += 1
                    # --------------------
                    # person
                    people.append({
                        'id': person_id,
                        'gender': Gender(member.gender)
                    })
                    # --------------------
                    # family member
                    family_members.append({
                        'family_id': family_id,
                        'person_id': person_id,
                        'order_in_family': index,
                        'role_in_family': FamilyRole[member.role]
                    })

            # ---------------------
            # family variant
            family_variant = {
                'family_id': family_id,
                'variant_id': variant_id,
                'present_in_affected': False,
                'present_in_unaffected': False,
                'present_in_mom': False,
                'present_in_dad': False,
                'best_state': old_variant.bestStStr,
                'counts': old_variant.countsStr,
            }
            family_variants.append(family_variant)

            for index, member in enumerate(old_variant.memberInOrder):
                alt_allele_count = old_variant.variant_count_in_person(index)
                # ----------------------
                # person variant
                person_variants.append({
                    'variant_id': variant_id,
                    'person_id': person_ids[member.personId],
                    'alt_allele_count': alt_allele_count,
                })
                if member.role == 'prb' and alt_allele_count > 0:
                    family_variant['present_in_affected'] = True
                elif member.role == 'sib' and alt_allele_count > 0:
                    family_variant['present_in_unaffected'] = True
                elif member.role == 'mom' and alt_allele_count > 0:
                    family_variant['present_in_mom'] = True
                elif member.role == 'dad' and alt_allele_count > 0:
                    family_variant['present_in_dad'] = True

            if count % 5000 == 0:
                session.bulk_insert_mappings(Variant, variants)
                session.bulk_insert_mappings(NumericAttribute, numeric_attributes)
                session.bulk_insert_mappings(Effect, effects)
                session.bulk_insert_mappings(FamilyVariant, family_variants)
                session.bulk_insert_mappings(PersonVariant, person_variants)

                LOGGER.debug('Transferred {} variants.'.format(count))

                variants = []
                numeric_attributes = []
                effects = []
                family_variants = []
                person_variants = []

                if len(people) >= 5000:
                    session.bulk_insert_mappings(Gene, genes)
                    session.bulk_insert_mappings(Family, families)
                    session.bulk_insert_mappings(Person, people)
                    session.bulk_insert_mappings(FamilyMember, family_members)

                    LOGGER.debug('Transferred genes, families, people and members.')

                    genes = []
                    families = []
                    people = []
                    family_members = []

        session.bulk_insert_mappings(Gene, genes)
        session.bulk_insert_mappings(Family, families)
        session.bulk_insert_mappings(Person, people)
        session.bulk_insert_mappings(FamilyMember, family_members)
        LOGGER.debug('Transferred genes, families, people and members.')

        session.bulk_insert_mappings(Variant, variants)
        session.bulk_insert_mappings(NumericAttribute, numeric_attributes)
        session.bulk_insert_mappings(Effect, effects)
        session.bulk_insert_mappings(FamilyVariant, family_variants)
        session.bulk_insert_mappings(PersonVariant, person_variants)

        session.commit()
        session.close()

    NUMERIC_ATTRIBUTES = {
        'SSC-freq' : AttributeName.ssc_freq,
        'EVS-freq' : AttributeName.evs_freq,
        'E65-freq' : AttributeName.e65_freq,
    }
