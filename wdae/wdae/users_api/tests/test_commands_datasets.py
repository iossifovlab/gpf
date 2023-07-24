# pylint: disable=W0621,C0114,C0116,W0212,W0613
import tempfile

from django.core.management import call_command
from django.contrib.auth.models import Group

from datasets_api.models import Dataset
from users_api.management.commands.datasets_export import Command


def test_datasets_export(wdae_gpf_instance, fixtures_wgpf_instance):
    expected_output = """dataset,groups
person_sets_study_1,any_dataset;person_sets_study_1
fake_study,any_dataset;fake_study
quads_in_parent,any_dataset;quads_in_parent
inheritance_trio,any_dataset;inheritance_trio
quads_variant_types,any_dataset;quads_variant_types
Study3,any_dataset;Study3
f1_trio,any_dataset;f1_trio
quads_two_families,any_dataset;quads_two_families
person_sets_study_3,any_dataset;person_sets_study_3
person_sets_study_2,any_dataset;person_sets_study_2
comp,any_dataset;comp
quads_f1,any_dataset;quads_f1
f3_triple,any_dataset;f3_triple
Study1,any_dataset;Study1
quads_f2,any_dataset;quads_f2
f2_recurrent,any_dataset;f2_recurrent
study4,any_dataset;study4
f1_study,any_dataset;f1_study
Study2,any_dataset;Study2
quads_in_child,any_dataset;quads_in_child
f1_group,any_dataset;f1_group
quads_composite_ds,any_dataset;quads_composite_ds
quads_f1_ds,any_dataset;quads_f1_ds
person_sets_dataset_1,any_dataset;person_sets_dataset_1
f2_group,any_dataset;f2_group
quads_in_child_ds,any_dataset;quads_in_child_ds
quads_variant_types_ds,any_dataset;quads_variant_types_ds
quads_in_parent_ds,any_dataset;quads_in_parent_ds
person_sets_dataset_2,any_dataset;person_sets_dataset_2
quads_f2_ds,any_dataset;quads_f2_ds
f3_group,any_dataset;f3_group
composite_dataset_ds,any_dataset;composite_dataset_ds
quads_two_families_ds,any_dataset;quads_two_families_ds
inheritance_trio_ds,any_dataset;inheritance_trio_ds
Dataset2,any_dataset;Dataset2
Dataset3,any_dataset;Dataset3
Dataset1,any_dataset;Dataset1
Dataset4,any_dataset;Dataset4
TEST_REMOTE_iossifov_2014,any_dataset;TEST_REMOTE_iossifov_2014
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
        command = Command(gpf_instance=fixtures_wgpf_instance)
        call_command(command, file=temp.name)
        assert set(temp.read().split()) == set(expected_output.split())


def test_datasets_restore(db):
    comp, _ = Dataset.objects.get_or_create(dataset_id="comp")
    comp.groups.add(Group.objects.create(name="any_dataset"))
    comp.groups.add(Group.objects.create(name="comp"))
    input_csv = """dataset,groups
comp,any_dataset;comp;new_test_group
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
        temp.write(input_csv)
        temp.seek(0)
        call_command("datasets_restore", file=temp.name)
        # I needed to refresh the dataset object, otherwise
        # its groups are empty
        comp = Dataset.objects.get(dataset_id="comp")
        assert Group.objects.filter(name="new_test_group").exists()
        assert {group.name for group in comp.groups.all()} == {
            "any_dataset",
            "comp",
            "new_test_group"
        }
