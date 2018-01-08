'''[VariantView]

[A proxy class for SQLAlchemy Variant object complying to the legacy Variant API]
'''
from variant_db.model import *


# TODO check this against newer version in branch that adds support for non family variants
def normal_allele_count(chromosome, location, gender):
    if chromosome == 'X' and (location < 60001
            or (location > 2699520 and location < 154931044)
            or location > 155260560):

        if gender == Gender.male:
            return 1
        else:
            return 2
    elif chromosome == 'Y':
        if gender == Gender.male:
            return 1
        elif gender == Gender.female:
            return 0
    return 2

def is_child(family_member):
    return family_member.role_in_family == FamilyRole.sib \
        or family_member.role_in_family == FamilyRole.prb \
        or family_member.role_in_family == FamilyRole.child

def is_parent(family_member):
    return family_member.role_in_family == FamilyRole.dad \
        or family_member.role_in_family == FamilyRole.mom

class VariantView(object):

    def __init__(self, study, variant, family):
        self._variant = variant
        self._family = family
        self.study = study
        self.atts = {}
        # TODO put _variant.numeric_attributes in atts with some key mapping

    @property
    def familyId(self):
        return self._family.family_ext_id

    @property
    def studyName(self):
        # TODO
        return self.study.name

    @property
    def location(self):
        return '{}:{}'.format(self._variant.chromosome, self._variant.location)

    @property
    def variant(self):
        return self._variant.variant

    @property
    def bestStStr(self):
        # TODO
        return None

    @property
    def bestSt(self):
        # TODO
        return None

    @property
    def countsStr(self):
        # TODO ???
        return None

    @property
    def counts(self):
        # TODO
        return None

    @property
    def geneEffect(self):
        gene_effects = []
        for effect in self._variant.effects:
            if effect.gene is None:
                gene_effects.append({ 'eff': effect.effect_type.name, 'sym': '', 'symu': '' })
            else:
                gene_effects.append({
                    'eff': effect.effect_type.name,
                    'sym': effect.gene.symbol,
                    'symu': effect.gene.symbol.upper()
                })
        return gene_effects

    @property
    def requestedGeneEffects(self):
        return self.geneEffect

    @property
    def effectType(self):
        return self._variant.worst_effect.effect_type.name

    @property
    def memberInOrder(self):
        return self._family.members

    @property
    def inChS(self):
        childStr = ''
        for member in self._family.members:
            if is_child(member) and member.person.alt_allele_count_for(self._variant.id) > 0:
                childStr += member.role_in_family.name + member.person.gender.value
        return childStr

    @property
    def fromParentS(self):
        parentStr = ''
        for member in self._family.members:
            if is_parent(member) and member.person.alt_allele_count_for(self._variant.id) > 0:
                parentStr += member.role_in_family.name
        return parentStr

    def pedigree_v3(self, legend):
        def get_color(p):
            # TODO
            return '#FFFFFF'

        denovo_parent = self.denovo_parent()

        # TODO may be we should store and use original person id
        result = []
        
        dad_id, mom_id = '', ''
        for member in self.memberInOrder:
            person_list = [self.familyId, member.person_id,
                member.person.gender.value, get_color(member),
                member.person.alt_allele_count_for(self._variant.id),
                # TODO don't know the meaning of this
                0]
            if is_child(member):
                person_list[2:2] += [dad_id, mom_id]
            else:
                person_list[2:2] += ['', '']
                if member.role_in_family == FamilyRole.mom:
                    mom_id = member.person_id
                elif member.role_in_family == FamilyRole.dad:
                    dad_id = member.person_id
            result.append(person_list)
        return result

    def denovo_parent(self):
        # TODO
        return None   

    def __eq__(self, other):
        return (self.variant == other.variant and self.location == other.location
            and self.familyId == other.familyId)

    def __lt__(self, other):
        return self.sort_key < other.sort_key

    CHROMOSOMES_ORDER = dict(
        {str(x): '0' + str(x) for x in range(1, 10)}.items() +
        {str(x): str(x) for x in range(10, 23)}.items() +
        { 'X': '23', 'Y': '24' }.items())

    @property
    def sort_key(self):
        return (self.CHROMOSOMES_ORDER.get(self._variant.chromosome, '99' + self._variant.chromosome),
            self._variant.location)