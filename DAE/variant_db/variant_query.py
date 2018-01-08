import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker, aliased, joinedload, subqueryload, selectinload

from transmitted.base_query import TransmissionConfig
from variant_db.variant_view_model import VariantView

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
        print(or_conditions)
        return query.filter(or_(*or_conditions))

    def get_transmitted_variants(self, **kwargs):
        return self.find_variants(**kwargs)

    def find_variants(self, **kwargs):
        with self.session() as session:
            query = session.query(Variant, FamilyVariant).\
                order_by(Variant.chromosome, Variant.location).\
                filter(Variant.id == FamilyVariant.variant_id).\
                        options(joinedload(Variant.worst_effect).\
                                joinedload(Effect.gene)).\
                        options(selectinload(Variant.effects).\
                                joinedload(Effect.gene)).\
                        options(joinedload(FamilyVariant.family).\
                                selectinload(Family.members).\
                                joinedload(FamilyMember.person).\
                                selectinload(Person.person_variants))

            if kwargs.get('genomicScores', False):
                query = self._build_genomic_scores_where(query, kwargs['genomicScores'])
            if kwargs.get('presentInChild', False):
                query = self._build_present_in_child_where(query, kwargs['presentInChild'])
            
            for variant, family_variant in query:
                yield VariantView(self.study, variant, family_variant.family)
