from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.family import Family, FamilyTag, Person

from federation.rest_api_client import RESTClient


def build_remote_families(
    remote_study_id: str,
    rest_client: RESTClient,
) -> FamiliesData:
    """Construct remote genotype data families."""
    families = {}
    families_details = rest_client.get_all_family_details(
        remote_study_id,
    )

    result = FamiliesData()

    for family in families_details:
        family_id = family["family_id"]
        person_jsons = family["members"]
        family_members = []
        for person_json in person_jsons:
            person = Person(**person_json)
            family_members.append(person)
            result.persons_by_person_id[person.person_id].append(person)
            result.persons[person.fpid] = person

        family_obj = Family.from_persons(family_members)
        for tag in family["tags"]:
            family_obj.set_tag(FamilyTag.from_label(tag))
        families[family_id] = family_obj

    # Setting the families directly since we can assume that
    # the remote has carried out all necessary transformations
    result._families = families  # noqa: SLF001

    return result
