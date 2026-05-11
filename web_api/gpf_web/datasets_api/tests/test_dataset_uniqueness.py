# PascalCase locals (PreDataset etc.) are the standard Django
# historical-models pattern — the names rebind model classes at a
# specific migration state, so C0103 is added to the file-level disable.
# pylint: disable=W0621,C0103,C0114,C0116,W0212,W0613
from collections.abc import Callable

import pytest
from django.contrib.auth.models import Group
from django.db import IntegrityError, connection, models, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.state import StateApps

from datasets_api.models import Dataset, DatasetHierarchy


@pytest.fixture
def migrate_to(transactional_db: None) -> Callable:  # noqa: ARG001
    def _migrate_to(target: list[tuple[str, str]]) -> StateApps:
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(target)
        return executor.loader.project_state(target).apps
    return _migrate_to


def test_dataset_id_is_unique_at_db_level(db: None) -> None:  # noqa: ARG001
    Dataset.objects.create(dataset_id="study_x")
    with pytest.raises(IntegrityError), transaction.atomic():
        Dataset.objects.create(dataset_id="study_x")


# Race protection comes from the DB-level unique constraint, not from
# app-level locking. The serial-repeat tests below guard the public
# contract — don't replace the DB constraint with a Python lock.


def test_recreate_dataset_perm_is_idempotent(db: None) -> None:  # noqa: ARG001
    Dataset.recreate_dataset_perm("study_x")
    Dataset.recreate_dataset_perm("study_x")

    assert Dataset.objects.filter(dataset_id="study_x").count() == 1
    survivor = Dataset.objects.get(dataset_id="study_x")
    assert {g.name for g in survivor.groups.all()} == {
        "any_dataset", "study_x",
    }


def test_recreate_dataset_perm_after_external_insert(
    db: None,  # noqa: ARG001
) -> None:
    Dataset.objects.create(dataset_id="study_x")

    Dataset.recreate_dataset_perm("study_x")

    assert Dataset.objects.filter(dataset_id="study_x").count() == 1
    survivor = Dataset.objects.get(dataset_id="study_x")
    assert Group.objects.filter(name="study_x").exists()
    assert {g.name for g in survivor.groups.all()} == {
        "any_dataset", "study_x",
    }


def test_migration_dedupes_dataset_rows_and_folds_groups(
    migrate_to: Callable,
) -> None:
    pre = migrate_to([("datasets_api", "0008_datasethierarchy_instance_id")])
    PreDataset = pre.get_model("datasets_api", "Dataset")
    PreGroup = pre.get_model("auth", "Group")

    survivor = PreDataset.objects.create(dataset_id="dup")
    duplicate = PreDataset.objects.create(dataset_id="dup")
    g_only_in_survivor = PreGroup.objects.create(name="g_survivor_only")
    g_only_in_duplicate = PreGroup.objects.create(name="g_duplicate_only")
    g_in_both = PreGroup.objects.create(name="g_both")
    survivor.groups.add(g_only_in_survivor, g_in_both)
    duplicate.groups.add(g_only_in_duplicate, g_in_both)

    post = migrate_to([
        ("datasets_api", "0009_dataset_dataset_id_unique")])
    PostDataset = post.get_model("datasets_api", "Dataset")

    rows = list(PostDataset.objects.filter(dataset_id="dup"))
    assert len(rows) == 1
    survived = rows[0]
    assert survived.pk == survivor.pk
    assert {g.name for g in survived.groups.all()} == {
        "g_survivor_only", "g_duplicate_only", "g_both",
    }


def test_migration_repoints_hierarchy_fks_to_survivor(
    migrate_to: Callable,
) -> None:
    pre = migrate_to([("datasets_api", "0008_datasethierarchy_instance_id")])
    PreDataset = pre.get_model("datasets_api", "Dataset")
    PreHierarchy = pre.get_model("datasets_api", "DatasetHierarchy")

    survivor = PreDataset.objects.create(dataset_id="dup")
    duplicate = PreDataset.objects.create(dataset_id="dup")
    other = PreDataset.objects.create(dataset_id="other")
    PreHierarchy.objects.create(
        instance_id="i1", ancestor=duplicate, descendant=other, direct=True,
    )
    PreHierarchy.objects.create(
        instance_id="i1", ancestor=other, descendant=duplicate, direct=False,
    )

    post = migrate_to([
        ("datasets_api", "0009_dataset_dataset_id_unique")])
    PostHierarchy = post.get_model("datasets_api", "DatasetHierarchy")

    edges = list(PostHierarchy.objects.filter(instance_id="i1"))
    assert len(edges) == 2
    survivor_pk = survivor.pk
    other_pk = other.pk
    pairs = {(e.ancestor_id, e.descendant_id, e.direct) for e in edges}
    assert pairs == {
        (survivor_pk, other_pk, True),
        (other_pk, survivor_pk, False),
    }


# Identifier-field type regression (iossifovlab/gpf#836).
#
# These were ``TextField`` originally, which makes MySQL refuse to put a
# UNIQUE constraint on the column ("BLOB/TEXT column used in key
# specification without a key length"). The fields must be CharField with
# a bounded ``max_length`` for the schema to apply on MySQL.


def _field(model: type[models.Model], name: str) -> models.Field:
    return model._meta.get_field(name)  # type: ignore[return-value]


def test_dataset_id_is_charfield_255_and_unique() -> None:
    field = _field(Dataset, "dataset_id")
    assert isinstance(field, models.CharField), (
        f"dataset_id must be CharField, got {type(field).__name__}"
    )
    assert field.max_length == 255
    assert field.unique is True


def test_dataset_name_is_charfield_255() -> None:
    field = _field(Dataset, "dataset_name")
    assert isinstance(field, models.CharField), (
        f"dataset_name must be CharField, got {type(field).__name__}"
    )
    assert field.max_length == 255


def test_datasethierarchy_instance_id_is_charfield_255() -> None:
    field = _field(DatasetHierarchy, "instance_id")
    assert isinstance(field, models.CharField), (
        f"instance_id must be CharField, got {type(field).__name__}"
    )
    assert field.max_length == 255


def test_migration_0010_leaves_models_as_charfield_255(
    migrate_to: Callable,
) -> None:
    """Running through 0010 lands on CharField(255) for all three IDs."""
    post = migrate_to([
        ("datasets_api", "0010_identifier_fields_to_charfield"),
    ])
    PostDataset = post.get_model("datasets_api", "Dataset")
    PostHierarchy = post.get_model("datasets_api", "DatasetHierarchy")

    dataset_id = PostDataset._meta.get_field("dataset_id")
    assert isinstance(dataset_id, models.CharField)
    assert dataset_id.max_length == 255
    assert dataset_id.unique is True

    dataset_name = PostDataset._meta.get_field("dataset_name")
    assert isinstance(dataset_name, models.CharField)
    assert dataset_name.max_length == 255

    instance_id = PostHierarchy._meta.get_field("instance_id")
    assert isinstance(instance_id, models.CharField)
    assert instance_id.max_length == 255
