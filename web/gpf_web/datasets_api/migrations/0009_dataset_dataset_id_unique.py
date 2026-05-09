from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps


def dedupe_datasets(
    apps: StateApps,
    schema_editor: BaseDatabaseSchemaEditor,  # noqa: ARG001
) -> None:
    Dataset = apps.get_model("datasets_api", "Dataset")
    DatasetHierarchy = apps.get_model("datasets_api", "DatasetHierarchy")

    seen: dict[str, int] = {}
    for row in Dataset.objects.order_by("pk").values("pk", "dataset_id"):
        seen.setdefault(row["dataset_id"], row["pk"])

    duplicates = list(
        Dataset.objects.exclude(pk__in=seen.values())
        .values_list("pk", "dataset_id"),
    )
    for dup_pk, dup_dataset_id in duplicates:
        survivor_pk = seen[dup_dataset_id]
        survivor = Dataset.objects.get(pk=survivor_pk)
        dup = Dataset.objects.get(pk=dup_pk)
        survivor.groups.add(*dup.groups.all())
        DatasetHierarchy.objects.filter(ancestor_id=dup_pk).update(
            ancestor_id=survivor_pk,
        )
        DatasetHierarchy.objects.filter(descendant_id=dup_pk).update(
            descendant_id=survivor_pk,
        )
        dup.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("datasets_api", "0008_datasethierarchy_instance_id"),
    ]

    operations = [
        migrations.RunPython(dedupe_datasets, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="dataset",
            name="dataset_id",
            field=models.TextField(unique=True),
        ),
    ]
