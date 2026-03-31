# pylint: disable=W0621,C0114,C0116,W0212,W0613
import tempfile

from datasets_api.models import Dataset
from django.contrib.auth.models import Group
from django.core.management import call_command
from gpf_instance.gpf_instance import WGPFInstance

from users_api.management.commands.datasets_export import Command


def test_datasets_export(t4c8_wgpf_instance: WGPFInstance) -> None:
    expected_output = """dataset,groups
t4c8_dataset,any_dataset;t4c8_dataset
t4c8_study_1,any_dataset;t4c8_study_1
t4c8_study_2,any_dataset;t4c8_study_2
t4c8_study_4,any_dataset;t4c8_study_4
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
        command = Command(gpf_instance=t4c8_wgpf_instance)
        call_command(command, file=temp.name)
        assert set(temp.read().split()) == set(expected_output.split())


def test_datasets_restore(db: None) -> None:  # noqa: ARG001
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
            "new_test_group",
        }
