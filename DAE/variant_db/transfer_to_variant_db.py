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
                #'mysql+mysqldb://{}:{}@{}:{}/{}'.format('seqpipe', 'lae0suNu', '127.0.0.1', '3306', 'variant_db')
                'mysql+mysqldb://{}:{}@{}:{}/{}'.format(user, password, host, port, db)
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
        # TODO study table in the DB or separate DB for each study?
        study = vDB.get_study(study_name)
        variants_generator = study.get_transmitted_variants(limit=limit)
        count = 1
        ten_percent_count = limit / 10
        for old_v in variants_generator:
            if count % ten_percent_count == 0:
                LOGGER.debug('Transferred {}%'.format(100 * count / limit))

            count += 1

            variant = self._get_or_create_variant(old_v)
            family = self._get_or_create_family(int(old_v.familyId), old_v.memberInOrder)
            
            family_variant = FamilyVariant(
                present_in_affected = False,
                present_in_unaffected = False,
                present_in_mom = False,
                present_in_dad = False,
                best_state = old_v.bestStStr,
                counts = old_v.countsStr,
                family = family,
                variant = variant)

            for index, family_member in enumerate(family.members):
                pv = PersonVariant(alt_allele_count = old_v.variant_count_in_person(index),
                    variant = variant, person = family_member.person)
                if family_member.role_in_family == FamilyRole.prb and pv.alt_allele_count > 0:
                    family_variant.present_in_affected = True
                elif family_member.role_in_family == FamilyRole.sib and pv.alt_allele_count > 0:
                    family_variant.present_in_unaffected = True
                elif family_member.role_in_family == FamilyRole.mom and pv.alt_allele_count > 0:
                    family_variant.present_in_mom = True
                elif family_member.role_in_family == FamilyRole.dad and pv.alt_allele_count > 0:
                    family_variant.present_in_dad = True
                self.session.add(pv)

            self.session.add(family_variant)
        self.session.commit()
        self.session.close()

    NUMERIC_ATTRIBUTES = {
        'SSC-freq' : AttributeName.ssc_freq,
        'EVS-freq' : AttributeName.evs_freq,
        'E65-freq' : AttributeName.e65_freq,
    }

    @classmethod
    def _set_numeric_attributes(cls, variant, old_variant):
        for key in cls.NUMERIC_ATTRIBUTES:
            value = old_variant.atts.get(key, None)
            if value is not None:
                variant.numeric_values[cls.NUMERIC_ATTRIBUTES[key]] = value

    def _get_or_create_variant(self, old_variant):
        variant = self.session.query(Variant).filter_by(
            chromosome = old_variant.atts['chr'],
            location = old_variant.atts['position'],
            variant = old_variant.variant).first()
        if variant is not None:
            return variant

        variant = Variant(
            variant = old_variant.variant,
            variant_type = self.STR_TO_VARIANT_TYPE[old_variant.variant[:3]],
            location = old_variant.atts['position'],
            chromosome = old_variant.atts['chr'],
            effects_details = old_variant.atts['effectGene'],
            n_par_called = old_variant.atts['all.nParCalled'],
            n_alt_alls = old_variant.atts['all.nAltAlls'],
            prcnt_par_called = old_variant.atts['all.prcntParCalled'],
            alt_freq = old_variant.atts['all.altFreq']
        )
        self._set_numeric_attributes(variant, old_variant)
    
        variant.effects = []
        for gene_effect in [gene_effect.split(':')
                            for gene_effect
                            in old_variant.atts['effectGene'].split('|')]:
            if len(gene_effect) == 1:
                gene = None
                effect = gene_effect[0]
            else:
                gene = self._get_or_create_gene(gene_effect[0])
                effect = gene_effect[1]
            variant.effects.append(
                Effect(gene = gene, effect_type = EffectType(effect)))
            if effect == old_variant.atts['effectType']:
                variant.worst_effect = variant.effects[-1]

        return variant

    def _get_or_create_family(self, family_id, members):
        family = self.session.query(Family).filter_by(family_ext_id=family_id).\
            first()
        if family is not None:
            return family

        # TODO kids_count will work only for core families
        family = Family(family_ext_id = family_id, kids_count = len(members) - 2)
        family_members = []
        
        for index, member in enumerate(members):
            p = Person(gender = Gender(member.gender))
            fm = FamilyMember(person = p, order_in_family = index,
                role_in_family = FamilyRole[member.role])
            family_members.append(fm)
        family.members = family_members
        self.session.add(family)
        return family

    def _get_or_create_gene(self, symbol):
        gene = self.session.query(Gene).filter_by(symbol=symbol).first()
        if gene is not None:
            return gene

        gene = Gene(symbol=symbol)
        self.session.add(gene)
        return gene
