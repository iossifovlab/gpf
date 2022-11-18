import pathlib
import textwrap
from dataclasses import dataclass, asdict

import jinja2

from dae.testing import setup_directories


@dataclass
class StudyLayout:
    study_id: str
    pedigree: pathlib.Path
    vcf: list[pathlib.Path]
    denovo: list[pathlib.Path]
    dae: list[pathlib.Path]
    cnv: list[pathlib.Path]


def data_import(
        root_path: pathlib.Path, study: StudyLayout, gpf_instance,
        study_config=None):
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

    if study_config:
        setup_directories(
            root_path / "studies" / study.study_id,
            {
                f"{study.study_id}.yaml": study_config
            }
        )
    return project


def vcf_import(
        root_path: pathlib.Path,
        study_id: str,
        ped_path: pathlib.Path, vcf_paths: list[pathlib.Path],
        gpf_instance,
        study_config: str = None):
    """Import a VCF study and return the import project."""
    study = StudyLayout(study_id, ped_path, vcf_paths, [], [], [])
    project = data_import(root_path, study, gpf_instance, study_config)
    return project


def vcf_study(
        root_path: pathlib.Path,
        study_id: str,
        ped_path: pathlib.Path, vcf_paths: list[pathlib.Path],
        gpf_instance,
        study_config: str = None):
    """Import a VCF study and return the imported study."""
    vcf_import(
        root_path, study_id, ped_path, vcf_paths, gpf_instance, study_config)
    gpf_instance.reload()
    return gpf_instance.get_genotype_data(study_id)


def denovo_import(
        root_path: pathlib.Path,
        study_id: str,
        ped_path: pathlib.Path, denovo_paths: list[pathlib.Path],
        gpf_instance, study_config=None):
    """Import a de Novo study and return the import project."""
    study = StudyLayout(study_id, ped_path, [], denovo_paths, [], [])
    project = data_import(root_path, study, gpf_instance, study_config)
    return project


def denovo_study(
        root_path: pathlib.Path,
        study_id: str,
        ped_path: pathlib.Path, denovo_paths: list[pathlib.Path],
        gpf_instance,
        study_config: str = None):
    """Import a de Novo study and return the imported study."""
    denovo_import(
        root_path, study_id, ped_path, denovo_paths, gpf_instance,
        study_config=study_config)
    gpf_instance.reload()
    return gpf_instance.get_genotype_data(study_id)


def setup_dataset(dataset_id, gpf_instance, *studies):
    """Create and register a dataset dataset_id with studies."""
    # pylint: disable=import-outside-toplevel
    from box import Box
    from dae.studies.study import GenotypeDataGroup

    dataset = GenotypeDataGroup(
        Box({"id": dataset_id}, default_box=True), studies)
    # pylint: disable=protected-access
    gpf_instance._variants_db.register_genotype_data(dataset)

    return dataset
