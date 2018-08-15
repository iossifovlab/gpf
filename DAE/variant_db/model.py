import enum

from sqlalchemy import Column, Boolean, Integer, Float, String, \
    Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy


class Gender(enum.Enum):
    male = 'M'
    female = 'F'
    unknown = 'U'


class FamilyRole(enum.Enum):
    unknown = 0
    mom = 10
    dad = 20
    step_mom = 23
    step_dad = 13
    parent = 1
    prb = 30
    sib = 40
    child = 50
    spouse = 2
    maternal_cousin = 14
    paternal_cousin = 24
    maternal_uncle = 11
    maternal_aunt = 12
    paternal_uncle = 21
    paternal_aunt = 22
    maternal_half_sibling = 41
    paternal_half_sibling = 42
    maternal_grandmother = -11
    maternal_grandfather = -12
    paternal_grandmother = -21
    paternal_grandfather = -22


class VariantType(enum.Enum):
    substitution = 1
    deletion = 2
    insertion = 3
    cnv = 4
    complex = 5


class EffectType(enum.Enum):
    nonsense = 'nonsense'
    frame_shift = 'frame-shift'
    splice_site = 'splice-site'
    missense = 'missense'
    no_frame_shift = 'no-frame-shift'
    no_frame_shift_new_stop = 'no-frame-shift-newStop'
    no_start = 'noStart'
    no_end = 'noEnd'
    synonymous = 'synonymous'
    non_coding = 'non-coding'
    non_coding_intron = 'non-coding-intron'
    intron = 'intron'
    intergenic = 'intergenic'
    prime3_utr = "3'UTR"
    prime5_utr = "5'UTR"
    prime3_utr_intron = "3'UTR-intron"
    prime5_utr_intron = "5'UTR-intron"
    cnv_plus = 'CNV+'
    cnv_minus = 'CNV-'
    cds = 'CDS'


class AttributeName(enum.Enum):
    ssc_freq = "ssc_freq"
    evs_freq = "evs_freq"
    e65_freq = "e65_freq"


Base = declarative_base()


class Variant(Base):
    __tablename__ = 'variant'
    id = Column(Integer, primary_key=True)
    # TODO how long the varchar 256?
    variant = Column(String(256), nullable=False)
    variant_type = Column(Enum(VariantType), index=True, nullable=False)
    chromosome = Column(String(2), nullable=False)
    location = Column(Integer, nullable=False)
    location_end = Column(Integer)
    worst_effect_id = Column(ForeignKey('effect.id'))
    effects_details = Column(String(1024))
    n_par_called = Column(Integer, index=True)
    n_alt_alls = Column(Integer, index=True)
    prcnt_par_called = Column(Float, index=True)
    alt_freq = Column(Float, index=True)

    __table_args__ = (
        # TODO shall we include the location_end?
        # problem is if location_end is null
        # solution: we can store location_end (equal to location) for non CNV
        # variants
        UniqueConstraint('chromosome', 'location', 'variant_type',
                         'variant', name='chr_loc_var_uidx'),
    )


class NumericAttribute(Base):
    __tablename__ = 'numeric_attribute'
    variant_id = Column(Integer, ForeignKey('variant.id'), primary_key=True)
    name = Column(Enum(AttributeName), primary_key=True)
    value = Column(Float, nullable=False)

    __table_args__ = (
        Index('name_value_idx', 'name', 'value'),
    )


Variant.numeric_attributes = relationship(
    'NumericAttribute',
    collection_class=attribute_mapped_collection('name'),
    cascade='all, delete-orphan'
)

Variant.numeric_values = association_proxy(
    'numeric_attributes', 'value',
    creator=lambda k, v: NumericAttribute(name=k, value=v)
)


class Gene(Base):
    __tablename__ = 'gene'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(32), unique=True, nullable=False)


class Effect(Base):
    __tablename__ = 'effect'
    id = Column(Integer, primary_key=True)
    variant_id = Column(Integer, ForeignKey('variant.id'), nullable=False)
    gene_id = Column(Integer, ForeignKey('gene.id'))
    effect_type = Column(Enum(EffectType), nullable=False)

    gene = relationship('Gene')


Variant.effects = relationship(
    'Effect', primaryjoin=Variant.id == Effect.variant_id)
Variant.worst_effect = relationship(
    'Effect', primaryjoin=Variant.worst_effect_id == Effect.id,
    post_update=True)


class Family(Base):
    __tablename__ = 'family'
    id = Column(Integer, primary_key=True)
    family_ext_id = Column(String(64), unique=True)
    kids_count = Column(Integer)


class FamilyVariant(Base):
    __tablename__ = 'family_variant'
    variant_id = Column(Integer, ForeignKey('variant.id'), primary_key=True)
    family_id = Column(Integer, ForeignKey('family.id'), primary_key=True)
    present_in_affected = Column(Boolean, nullable=False)
    present_in_unaffected = Column(Boolean, nullable=False)
    present_in_mom = Column(Boolean, nullable=False)
    present_in_dad = Column(Boolean, nullable=False)
    best_state = Column(String(256), nullable=False)
    counts = Column(String(256), nullable=False)

    family = relationship('Family')
    variant = relationship('Variant')


class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    # TODO add person_ext_id
    gender = Column(Enum(Gender), nullable=False)

    person_variants = relationship('PersonVariant')

    def alt_allele_count_for(self, variant_id):
        for person_variant in self.person_variants:
            if person_variant.variant_id == variant_id:
                return person_variant.alt_allele_count
        return 0


class FamilyMember(Base):
    __tablename__ = 'family_member'
    family_id = Column(Integer, ForeignKey('family.id'), primary_key=True)
    person_id = Column(Integer, ForeignKey('person.id'), primary_key=True)
    order_in_family = Column(Integer, nullable=False)
    role_in_family = Column(Enum(FamilyRole), nullable=False)

    person = relationship('Person')


Family.members = relationship(
    'FamilyMember', order_by=FamilyMember.order_in_family)


class PersonVariant(Base):
    __tablename__ = 'person_variant'
    variant_id = Column(Integer, ForeignKey('variant.id'), primary_key=True)
    person_id = Column(Integer, ForeignKey('person.id'), primary_key=True)
    alt_allele_count = Column(Integer, nullable=False)
    # TODO counts column

    variant = relationship('Variant')
    person = relationship('Person')
