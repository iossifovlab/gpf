"""Restrict the data of a dataset to the studies that a user may access.

A user has a partial grant on a dataset when the user holds grants on
some of the child studies of the dataset, but holds neither the dataset
itself nor all of its child studies. Under a partial grant, a route
serves only the data of the allowed child studies.
"""
from collections.abc import Iterable
from typing import cast

from django.conf import settings
from django.contrib.auth.models import User
from gpf_instance.gpf_instance import WGPFInstance
from rest_framework.exceptions import PermissionDenied
from studies.study_wrapper import WDAEAbstractStudy

from datasets_api.models import DatasetHierarchy
from datasets_api.permissions import (
    IsDatasetAllowed,
    get_user_groups,
    get_wdae_children,
    get_wdae_dataset,
)
from gpf.pedigrees.families_data import FamiliesData
from gpf.pedigrees.loader import FamiliesLoader
from gpf.person_sets.person_sets import PersonSetCollection
from gpf.pheno.pheno_data import (
    PhenotypeData,
    PhenotypeGroup,
    PhenotypeStudy,
    RestrictedPhenotypeGroup,
)
from gpf.studies.study import GenotypeData


def _sees_all_studies(user: User) -> bool:
    return bool(
        settings.DISABLE_PERMISSIONS
        or user.is_superuser
        or user.is_staff
        or "admin" in get_user_groups(user),
    )


def get_partial_grant_studies(
    instance_id: str, user: User, dataset_id: str,
) -> set[str] | None:
    """Return the allowed child studies under a partial grant.

    Return ``None`` when the user has no partial grant on the dataset:
    the user holds the dataset itself or all of its child studies, or
    the dataset is a study without children.
    """
    if _sees_all_studies(user):
        return None
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None or DatasetHierarchy.is_study(instance_id, dataset):
        return None

    child_studies = {
        child.dataset_id
        for child in get_wdae_children(instance_id, dataset_id)
        if DatasetHierarchy.is_study(instance_id, child)
    }
    allowed = child_studies & set(
        IsDatasetAllowed.permitted_datasets(user, instance_id))
    if child_studies <= allowed:
        return None
    return allowed


def _allowed_studies(
    gpf_instance: WGPFInstance, study_ids: Iterable[str],
) -> list[GenotypeData]:
    studies = []
    for study_id in sorted(study_ids):
        study = gpf_instance.get_genotype_data(study_id)
        if study is None:
            continue
        if study.is_remote:
            # The families of a remote study are not available here.
            raise PermissionDenied
        studies.append(study)
    return studies


def _allowed_study_families(
    gpf_instance: WGPFInstance, study_ids: Iterable[str],
) -> list[FamiliesData]:
    families = []
    for study_id in sorted(study_ids):
        study = gpf_instance.get_wdae_wrapper(study_id)
        if study is None:
            continue
        if getattr(study, "is_remote", False) or (
            study.is_genotype and study.genotype_data.is_remote
        ):
            # The families of a remote study are not available here.
            raise PermissionDenied
        families.append(study.families)
    return families


def _combine_families(families: list[FamiliesData]) -> FamiliesData:
    if not families:
        return FamiliesData.from_families({})
    result = families[0]
    for other in families[1:]:
        result = FamiliesData.combine(result, other, forced=True)
    return result


def get_partial_grant_families(
    gpf_instance: WGPFInstance,
    user: User,
    dataset_id: str,
) -> FamiliesData | None:
    """Return the families of the allowed child studies.

    Return ``None`` when the user has no partial grant on the dataset.
    A family that occurs in more than one child study holds only the
    members of the allowed child studies.
    """
    allowed = get_partial_grant_studies(
        gpf_instance.instance_id, user, dataset_id,
    )
    if allowed is None:
        return None
    return _combine_families(_allowed_study_families(gpf_instance, allowed))


def get_granted_families(
    gpf_instance: WGPFInstance,
    user: User,
    genotype_data: GenotypeData,
) -> FamiliesData:
    """Return the families of the genotype data that the user may see."""
    families = get_partial_grant_families(
        gpf_instance, user, genotype_data.study_id,
    )
    if families is None:
        return genotype_data.families
    return families


def get_fully_granted_family_ids(
    family_ids: Iterable[str],
    granted: FamiliesData,
    dataset_families: FamiliesData,
) -> list[str]:
    """Keep the ids of the families that the user sees whole.

    A family that also holds persons of a child study outside the grant
    is left out, because the dataset classified it by those persons.
    """
    return [
        family_id for family_id in family_ids
        if family_id in granted
        and family_id in dataset_families
        and set(granted[family_id].persons)
        == set(dataset_families[family_id].persons)
    ]


def families_to_tsv_lines(families: FamiliesData) -> list[str]:
    """Return the families as the lines of a pedigree TSV file.

    Return no lines when there are no families.
    """
    if len(families) == 0:
        return []
    tsv = FamiliesLoader.to_tsv(families)
    return [f"{ln}\n" for ln in tsv.strip().split("\n")]


def get_granted_person_set_collection(
    gpf_instance: WGPFInstance,
    user: User,
    genotype_data: GenotypeData,
    collection_id: str,
) -> PersonSetCollection | None:
    """Return the person set collection that the user may see.

    Under a partial grant, the collection holds only the persons of the
    allowed child studies. Return ``None`` when the collection does not
    exist.
    """
    psc = genotype_data.person_set_collections.get(collection_id)
    if psc is None:
        return None
    allowed = get_partial_grant_studies(
        gpf_instance.instance_id, user, genotype_data.study_id,
    )
    if allowed is None:
        return psc

    studies = _allowed_studies(gpf_instance, allowed)
    collections = [
        study_psc
        for study in studies
        if (study_psc := study.get_person_set_collection(collection_id))
        is not None
    ]
    if not collections:
        return None
    if len(studies) == 1:
        return collections[0]
    return PersonSetCollection.combine(
        collections,
        _combine_families([study.families for study in studies]),
    )


def _phenotype_leaves(pheno: PhenotypeData) -> list[PhenotypeStudy]:
    if isinstance(pheno, PhenotypeGroup):
        return pheno.get_leaves()
    return [cast(PhenotypeStudy, pheno)]


def _is_remote(gpf_instance: WGPFInstance, data_id: str) -> bool:
    wrapper = gpf_instance.get_wdae_wrapper(data_id)
    if wrapper is None:
        return False
    return bool(getattr(wrapper, "is_remote", False)) or (
        wrapper.is_genotype and wrapper.genotype_data.is_remote
    )


def _allowed_pheno_ids(
    gpf_instance: WGPFInstance, allowed: Iterable[str],
) -> set[str]:
    """Map the allowed child studies to the phenotype data they reach.

    An allowed phenotype child reaches itself. An allowed genotype child
    reaches the phenotype data that its own configuration names.
    """
    pheno_ids: set[str] = set()
    for study_id in allowed:
        if _is_remote(gpf_instance, study_id):
            # The phenotype data of a remote child is not available here.
            raise PermissionDenied
        genotype_data = gpf_instance.get_genotype_data(study_id)
        if genotype_data is not None:
            pheno_id = genotype_data.config.get("phenotype_data")
            if pheno_id:
                pheno_ids.add(str(pheno_id))
        elif gpf_instance.has_phenotype_data(study_id):
            pheno_ids.add(study_id)
    return pheno_ids


def get_granted_phenotype_data(
    gpf_instance: WGPFInstance,
    user: User,
    study: WDAEAbstractStudy,
) -> PhenotypeData:
    """Return the phenotype data of the study that the user may see.

    Return the phenotype data of the study when the user has no partial
    grant. Under a partial grant, return a new object that holds only
    the phenotype leaves that the allowed child studies reach. Raise
    ``PermissionDenied`` when no leaf remains or when a child is remote.
    """
    phenotype_data = study.phenotype_data
    allowed = get_partial_grant_studies(
        gpf_instance.instance_id, user, study.study_id,
    )
    if allowed is None:
        return phenotype_data
    if getattr(study, "is_remote", False):
        raise PermissionDenied

    allowed_leaf_ids: set[str] = set()
    for pheno_id in _allowed_pheno_ids(gpf_instance, allowed):
        if _is_remote(gpf_instance, pheno_id):
            raise PermissionDenied
        if not gpf_instance.has_phenotype_data(pheno_id):
            continue
        allowed_leaf_ids.update(
            leaf.pheno_id for leaf in _phenotype_leaves(
                gpf_instance.get_phenotype_data(pheno_id)))

    leaves = [
        leaf for leaf in _phenotype_leaves(phenotype_data)
        if leaf.pheno_id in allowed_leaf_ids
    ]
    if not leaves:
        raise PermissionDenied
    if len(leaves) == 1:
        return leaves[0]
    assert isinstance(phenotype_data, PhenotypeGroup)
    return RestrictedPhenotypeGroup(phenotype_data, leaves)
