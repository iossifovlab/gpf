import logging
from contextlib import contextmanager

import pandas as pd
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker, aliased, joinedload, subqueryload

from transmitted.base_query import TransmissionConfig
from Variant import Variant as VariantView
#from variant_db.variant_view_model import VariantView
from variant_db.model import *

LOGGER = logging.getLogger(__name__)

Session = sessionmaker()

class VariantQuery(TransmissionConfig):

    def __init__(self, study, call_set=None):
        super(VariantQuery, self).__init__(study, call_set)
        self.study = study

        db = self._get_params('db')
        user = self._get_params('user')
        password = self._get_params('pass')
        host = self._get_params('host')
        port = self._get_params('port')
        if port is None:
            port = 3306

        self.db_engine = create_engine(
            #'mysql+mysqldb://{}:{}@{}:{}/{}'.format('seqpipe', 'lae0suNu', '127.0.0.1', '3306', 'variant_db')
            'mysql+mysqldb://{}:{}@{}:{}/{}'.format(user, password, host, port, db)
        )

    @contextmanager
    def session(self):
        session = Session(bind=self.db_engine.connect())
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _build_effect_where(query, effects=None, gene_symbols=None):
        query = query.join(Variant.effects).join(Effect.gene)
        if effects is not None:
            query = query.filter(Effect.effect_type.in_(
                [EffectType(effect) for effect in effects]))
        if gene_symbols is not None:
            query = query.filter(Gene.symbol.in_(
                [symbol.upper() for symbol in gene_symbols]))
        return query

    @staticmethod
    def _build_genomic_scores_where(query, genomic_scores):
        column_names = {
            'SSC-freq': 'ssc_freq',
            'EVS-freq': 'evs_freq',
            'E65-freq': 'e65_freq'
        }
        for score in genomic_scores:
            print("adding score filter")
            attribute = aliased(NumericAttribute)
            attribute_name = AttributeName(column_names[score['metric']])
            query = query.join(attribute, Variant.numeric_attributes)\
                .filter(attribute.name == attribute_name)
            if score['min'] != float("-inf"):
                query = query.filter(attribute.value >= score['min'])
            if score['max'] != float("inf"):
                query = query.filter(attribute.value < score['max'])
        return query

    @staticmethod
    def _build_present_in_child_where(query, present_in_child):
        if present_in_child is None:
            return query
        or_conditions = []
        if 'affected only' in present_in_child:
            or_conditions.append(and_(FamilyVariant.present_in_affected == True,
                FamilyVariant.present_in_unaffected == False))
        if 'unaffected only' in present_in_child:
            or_conditions.append(and_(FamilyVariant.present_in_affected == False,
                FamilyVariant.present_in_unaffected == True))
        if 'affected and unaffected' in present_in_child:
            or_conditions.append(and_(FamilyVariant.present_in_affected == True,
                FamilyVariant.present_in_unaffected == True))
        if 'neither' in present_in_child:
            or_conditions.append(and_(FamilyVariant.present_in_affected == False,
                FamilyVariant.present_in_unaffected == False))
        return query.filter(or_(*or_conditions))

    def get_transmitted_variants(self, **kwargs):
        return self.find_variants(**kwargs)

    def find_variants(self, **kwargs):
        with self.session() as session:
            query = session.query(Variant, FamilyVariant, Family.family_ext_id, Effect.effect_type).\
                order_by(Variant.chromosome, Variant.location).\
                filter(and_(Variant.id == FamilyVariant.variant_id,
                    FamilyVariant.family_id == Family.id,
                    Variant.id == Effect.variant_id))

            if 'genomicScores' in kwargs:
                query = self._build_genomic_scores_where(query, kwargs['genomicScores'])
            if 'presentInChild' in kwargs:
                query = self._build_present_in_child_where(query, kwargs['presentInChild'])
            if 'geneSyms' in kwargs or 'effectTypes' in kwargs:
                query = self._build_effect_where(query, kwargs.get('effectTypes'),
                    kwargs.get('geneSyms'))

            data_frame = pd.read_sql(query.statement, query.session.bind)
            data_frame.rename(columns={'effect_type' : 'effectType'}, inplace=True)
            for row in data_frame.to_dict('records'):
                #LOGGER.debug('Reading row {} from data frame'.format(index))
                row['effectType'] = row['effectType'].value
                row['location'] = '{}:{}'.format(row['chromosome'], row['location'])
                v = VariantView(row,
                    familyIdAtt="family_ext_id",
                    bestStAtt="best_state",
                    effectGeneAtt="effects_details",
                    altFreqPrcntAtt="alt_freq")
                v.study = self.study
                if row['alt_freq'] == 1:
                    v.popType = "ultraRare"
                else:
                    v.popType = "common"
                yield v
