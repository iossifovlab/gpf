import pathlib
import textwrap
from dataclasses import dataclass, asdict
from typing import Any, Optional

import jinja2
import yaml

from dae.utils.dict_utils import recursive_dict_update
from dae.testing import setup_directories
from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.import_tools.cli import run_with_project
from dae.studies.study import GenotypeData


@dataclass
class StudyInputLayout:
    study_id: str
    pedigree: pathlib.Path
    vcf: list[pathlib.Path]
    denovo: list[pathlib.Path]
    dae: list[pathlib.Path]
    cnv: list[pathlib.Path]


def update_study_config(
        gpf_instance, study_id: str,
        study_config_update: dict[str, Any]):
    """Update study configuration."""
    config_path = pathlib.Path(gpf_instance.dae_dir) / \
        "studies" / \
        study_id / \
        f"{study_id}.yaml"
    with open(config_path, "r", encoding="utf") as infile:
        config = yaml.safe_load(infile.read())
    config = recursive_dict_update(config, study_config_update)
    builder = StudyConfigBuilder(config)
    with open(config_path, "wt", encoding="utf8") as outfile:
        outfile.write(builder.build_config())


def setup_import_project_config(
    root_path: pathlib.Path, study: StudyInputLayout,
    gpf_instance,
    project_config_update: Optional[dict[str, Any]] = None,
    project_config_overwrite: Optional[dict[str, Any]] = None
) -> pathlib.Path:
    """Set up import project config."""
    params = asdict(study)
    params["work_dir"] = str(root_path / "work_dir")
    params["storage_id"] = gpf_instance\
        .genotype_storages\
        .get_default_genotype_storage()\
        .storage_id

    content = jinja2.Template(textwrap.dedent("""
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
    project_config = yaml.safe_load(content)
    if project_config_overwrite:
        project_config.update(project_config_overwrite)
    if project_config_update:
        project_config = recursive_dict_update(
            project_config, project_config_update)
    setup_directories(
        root_path / "import_project" / "import_config.yaml",
        yaml.dump(project_config, default_flow_style=False))
    return root_path / "import_project" / "import_config.yaml"


def setup_import_project(
        root_path: pathlib.Path, study: StudyInputLayout, gpf_instance,
        project_config_update: Optional[dict[str, Any]] = None,
        project_config_overwrite: Optional[dict[str, Any]] = None):
    """Set up an import project for a study and imports it."""
    project_config = setup_import_project_config(
        root_path, study, gpf_instance,
        project_config_update=project_config_update,
        project_config_overwrite=project_config_overwrite)

    # pylint: disable=import-outside-toplevel
    from dae.import_tools.import_tools import ImportProject
    project = ImportProject.build_from_file(
        project_config,
        gpf_instance=gpf_instance)
    return project


def vcf_import(
        root_path: pathlib.Path,
        study_id: str,
        ped_path: pathlib.Path, vcf_paths: list[pathlib.Path],
        gpf_instance,
        project_config_update: Optional[dict[str, Any]] = None,
        project_config_overwrite: Optional[dict[str, Any]] = None):
    """Import a VCF study and return the import project."""
    study = StudyInputLayout(study_id, ped_path, vcf_paths, [], [], [])
    project = setup_import_project(
        root_path, study, gpf_instance,
        project_config_update=project_config_update,
        project_config_overwrite=project_config_overwrite)
    return project


def vcf_study(
    root_path: pathlib.Path,
    study_id: str,
    ped_path: pathlib.Path, vcf_paths: list[pathlib.Path],
    gpf_instance,
    project_config_update: Optional[dict[str, Any]] = None,
    project_config_overwrite: Optional[dict[str, Any]] = None,
    study_config_update: Optional[dict[str, Any]] = None
) -> GenotypeData:
    """Import a VCF study and return the imported study."""
    project = vcf_import(
        root_path, study_id, ped_path, vcf_paths, gpf_instance,
        project_config_update=project_config_update,
        project_config_overwrite=project_config_overwrite)
    run_with_project(project)
    if study_config_update:
        update_study_config(
            gpf_instance, study_id, study_config_update)

    gpf_instance.reload()
    return gpf_instance.get_genotype_data(study_id)


def denovo_import(
        root_path: pathlib.Path,
        study_id: str,
        ped_path: pathlib.Path, denovo_paths: list[pathlib.Path],
        gpf_instance,
        project_config_update: Optional[dict[str, Any]] = None,
        project_config_overwrite: Optional[dict[str, Any]] = None):
    """Import a de Novo study and return the import project."""
    study = StudyInputLayout(study_id, ped_path, [], denovo_paths, [], [])
    project = setup_import_project(
        root_path, study, gpf_instance,
        project_config_update=project_config_update,
        project_config_overwrite=project_config_overwrite)
    return project


def denovo_study(
        root_path: pathlib.Path,
        study_id: str,
        ped_path: pathlib.Path, denovo_paths: list[pathlib.Path],
        gpf_instance,
        project_config_update: Optional[dict[str, Any]] = None,
        project_config_overwrite: Optional[dict[str, Any]] = None,
        study_config_update: Optional[dict[str, Any]] = None):
    """Import a de Novo study and return the imported study."""
    project = denovo_import(
        root_path, study_id, ped_path, denovo_paths, gpf_instance,
        project_config_update=project_config_update,
        project_config_overwrite=project_config_overwrite)
    run_with_project(project)
    if study_config_update:
        update_study_config(
            gpf_instance, study_id, study_config_update)

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


def study_update(gpf_instance, study, study_config_update: dict[str, Any]):
    update_study_config(gpf_instance, study.study_id, study_config_update)
    gpf_instance.reload()
    return gpf_instance.get_genotype_data(study.study_id)
