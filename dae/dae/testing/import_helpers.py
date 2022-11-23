import pathlib
import textwrap
from dataclasses import dataclass, asdict

import jinja2
import yaml

from dae.testing import setup_directories


@dataclass
class StudyLayout:
    study_id: str
    pedigree: pathlib.Path
    vcf: list[pathlib.Path]
    denovo: list[pathlib.Path]
    dae: list[pathlib.Path]
    cnv: list[pathlib.Path]


def update_study_config(gpf_instance, study_id: str, study_config_update: str):
    """Update study configuration."""
    config_path = pathlib.Path(gpf_instance.dae_dir) / \
        "studies" / \
        study_id / \
        f"{study_id}.yaml"
    with open(config_path, "r", encoding="utf") as infile:
        config = yaml.safe_load(infile.read())
    config_update = yaml.safe_load(study_config_update)
    config.update(config_update)
    with open(config_path, "wt", encoding="utf8") as outfile:
        outfile.write(yaml.safe_dump(config))


def data_import(
        root_path: pathlib.Path, study: StudyLayout, gpf_instance,
        study_config_update: str = ""):
    """Set up an import project for a study and imports it."""
    params = asdict(study)
    params["work_dir"] = str(root_path / "work_dir")
    params["storage_id"] = gpf_instance\
        .genotype_storages\
        .get_default_genotype_storage()\
        .storage_id

    project_config = jinja2.Template(textwrap.dedent("""
        id: {{ study_id}}
        processing_config:
          work_dir: {{ work_dir }}
        input:
          pedigree:
            file: {{ pedigree }}
        {% if vcf %}
          vcf:
            files:
            {% for vcf_path in vcf %}
             - {{ vcf_path }}
            {% endfor %}
            denovo_mode: denovo
            omission_mode: omission
        {% endif %}
        {% if denovo %}
          denovo:
            files:
            {% for denovo_path in denovo %}
            - {{ denovo_path }}
            {% endfor %}
        {% endif %}
        destination:
          storage_id: {{ storage_id}}
        """)).render(params)

    setup_directories(
        root_path / "import_project" / "import_config.yaml",
        project_config)

    # pylint: disable=import-outside-toplevel
    from dae.import_tools.import_tools import ImportProject, run_with_project
    project = ImportProject.build_from_file(
        root_path / "import_project" / "import_config.yaml",
        gpf_instance=gpf_instance)
    run_with_project(project)

    if study_config_update:
        update_study_config(gpf_instance, study.study_id, study_config_update)

    return project


def vcf_import(
        root_path: pathlib.Path,
        study_id: str,
        ped_path: pathlib.Path, vcf_paths: list[pathlib.Path],
        gpf_instance,
        study_config_update: str = ""):
    """Import a VCF study and return the import project."""
    study = StudyLayout(study_id, ped_path, vcf_paths, [], [], [])
    project = data_import(root_path, study, gpf_instance, study_config_update)
    return project


def vcf_study(
        root_path: pathlib.Path,
        study_id: str,
        ped_path: pathlib.Path, vcf_paths: list[pathlib.Path],
        gpf_instance,
        study_config_update: str = ""):
    """Import a VCF study and return the imported study."""
    vcf_import(
        root_path, study_id, ped_path, vcf_paths, gpf_instance,
        study_config_update)
    gpf_instance.reload()
    return gpf_instance.get_genotype_data(study_id)


def denovo_import(
        root_path: pathlib.Path,
        study_id: str,
        ped_path: pathlib.Path, denovo_paths: list[pathlib.Path],
        gpf_instance, study_config_update: str = ""):
    """Import a de Novo study and return the import project."""
    study = StudyLayout(study_id, ped_path, [], denovo_paths, [], [])
    project = data_import(root_path, study, gpf_instance, study_config_update)
    return project


def denovo_study(
        root_path: pathlib.Path,
        study_id: str,
        ped_path: pathlib.Path, denovo_paths: list[pathlib.Path],
        gpf_instance,
        study_config_update: str = ""):
    """Import a de Novo study and return the imported study."""
    denovo_import(
        root_path, study_id, ped_path, denovo_paths, gpf_instance,
        study_config_update)
    gpf_instance.reload()
    return gpf_instance.get_genotype_data(study_id)


def setup_dataset(
        dataset_id, gpf_instance, *studies,
        dataset_config_udate: str = ""):
    """Create and register a dataset dataset_id with studies."""
    # pylint: disable=import-outside-toplevel
    from box import Box
    from dae.studies.study import GenotypeDataGroup

    dataset_config = {
        "id": dataset_id
    }
    if dataset_config_udate:
        config_update = yaml.safe_load(dataset_config_udate)
        dataset_config.update(config_update)

    dataset = GenotypeDataGroup(
        Box(dataset_config, default_box=True), studies)
    # pylint: disable=protected-access
    gpf_instance._variants_db.register_genotype_data(dataset)

    return dataset


def study_update(gpf_instance, study, study_config_update: str):
    update_study_config(gpf_instance, study.study_id, study_config_update)
    gpf_instance.reload()
    return gpf_instance.get_genotype_data(study.study_id)
