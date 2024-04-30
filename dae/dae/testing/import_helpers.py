from __future__ import annotations

import pathlib
import textwrap
from dataclasses import asdict, dataclass
from typing import Any, Optional

import jinja2
import yaml
from box import Box

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.gpf_instance import GPFInstance
from dae.import_tools.cli import run_with_project
from dae.import_tools.import_tools import ImportProject
from dae.studies.study import GenotypeData, GenotypeDataGroup
from dae.testing import setup_directories
from dae.utils.dict_utils import recursive_dict_update


@dataclass
class StudyInputLayout:
    study_id: str
    pedigree: pathlib.Path
    vcf: list[pathlib.Path]
    denovo: list[pathlib.Path]
    dae: list[pathlib.Path]
    cnv: list[pathlib.Path]


def update_study_config(
        gpf_instance: GPFInstance, study_id: str,
        study_config_update: dict[str, Any]) -> None:
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
    gpf_instance: GPFInstance,
    project_config_update: Optional[dict[str, Any]] = None,
    project_config_overwrite: Optional[dict[str, Any]] = None,
    project_config_replace: Optional[dict[str, Any]] = None,
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
        {% if cnv %}
          cnv:
            files:
            {% for cnv_path in cnv %}
            - {{ cnv_path }}
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
    if project_config_replace:
        project_config = project_config_replace

    setup_directories(
        root_path / "import_project" / "import_config.yaml",
        yaml.dump(project_config, default_flow_style=False))
    return root_path / "import_project" / "import_config.yaml"


def setup_import_project(
    root_path: pathlib.Path, study: StudyInputLayout,
    gpf_instance: GPFInstance,
    project_config_update: Optional[dict[str, Any]] = None,
    project_config_overwrite: Optional[dict[str, Any]] = None,
    project_config_replace: Optional[dict[str, Any]] = None,
) -> ImportProject:
    """Set up an import project for a study and imports it."""
    project_config = setup_import_project_config(
        root_path, study, gpf_instance,
        project_config_update=project_config_update,
        project_config_overwrite=project_config_overwrite,
        project_config_replace=project_config_replace)

    # pylint: disable=import-outside-toplevel
    project = ImportProject.build_from_file(
        project_config,
        gpf_instance=gpf_instance)
    return project


def pedigree_import(
    root_path: pathlib.Path,
    study_id: str,
    ped_path: pathlib.Path,
    gpf_instance: GPFInstance,
    project_config_update: Optional[dict[str, Any]] = None,
    project_config_overwrite: Optional[dict[str, Any]] = None,
    project_config_replace: Optional[dict[str, Any]] = None,
) -> ImportProject:
    """Import a VCF study and return the import project."""
    study = StudyInputLayout(study_id, ped_path, [], [], [], [])
    return setup_import_project(
        root_path, study, gpf_instance,
        project_config_update=project_config_update,
        project_config_overwrite=project_config_overwrite,
        project_config_replace=project_config_replace)


def vcf_import(
    root_path: pathlib.Path,
    study_id: str,
    ped_path: pathlib.Path, vcf_paths: list[pathlib.Path],
    gpf_instance: GPFInstance,
    project_config_update: Optional[dict[str, Any]] = None,
    project_config_overwrite: Optional[dict[str, Any]] = None,
    project_config_replace: Optional[dict[str, Any]] = None,
) -> ImportProject:
    """Import a VCF study and return the import project."""
    study = StudyInputLayout(study_id, ped_path, vcf_paths, [], [], [])
    project = setup_import_project(
        root_path, study, gpf_instance,
        project_config_update=project_config_update,
        project_config_overwrite=project_config_overwrite,
        project_config_replace=project_config_replace)
    return project


def vcf_study(
    root_path: pathlib.Path,
    study_id: str,
    ped_path: pathlib.Path,
    vcf_paths: list[pathlib.Path],
    gpf_instance: GPFInstance,
    project_config_update: Optional[dict[str, Any]] = None,
    project_config_overwrite: Optional[dict[str, Any]] = None,
    study_config_update: Optional[dict[str, Any]] = None,
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
    gpf_instance: GPFInstance,
    project_config_update: Optional[dict[str, Any]] = None,
    project_config_overwrite: Optional[dict[str, Any]] = None,
) -> ImportProject:
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
    gpf_instance: GPFInstance,
    project_config_update: Optional[dict[str, Any]] = None,
    project_config_overwrite: Optional[dict[str, Any]] = None,
    study_config_update: Optional[dict[str, Any]] = None,
) -> GenotypeData:
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


def cnv_import(
    root_path: pathlib.Path,
    study_id: str,
    ped_path: pathlib.Path, cnv_paths: list[pathlib.Path],
    gpf_instance: GPFInstance,
    project_config_update: Optional[dict[str, Any]] = None,
    project_config_overwrite: Optional[dict[str, Any]] = None,
) -> ImportProject:
    """Import a de Novo study and return the import project."""
    study = StudyInputLayout(study_id, ped_path, [], [], [], cnv_paths)
    project = setup_import_project(
        root_path, study, gpf_instance,
        project_config_update=project_config_update,
        project_config_overwrite=project_config_overwrite)
    return project


def cnv_study(
    root_path: pathlib.Path,
    study_id: str,
    ped_path: pathlib.Path, cnv_paths: list[pathlib.Path],
    gpf_instance: GPFInstance,
    project_config_update: Optional[dict[str, Any]] = None,
    project_config_overwrite: Optional[dict[str, Any]] = None,
    study_config_update: Optional[dict[str, Any]] = None,
) -> GenotypeData:
    """Import a de Novo study and return the imported study."""
    project = cnv_import(
        root_path, study_id, ped_path, cnv_paths, gpf_instance,
        project_config_update=project_config_update,
        project_config_overwrite=project_config_overwrite)
    run_with_project(project)
    if study_config_update:
        update_study_config(
            gpf_instance, study_id, study_config_update)

    gpf_instance.reload()
    return gpf_instance.get_genotype_data(study_id)


def setup_dataset(
        dataset_id: str,
        gpf_instance: GPFInstance,
        *studies: GenotypeData,
        dataset_config_update: str = "") -> GenotypeDataGroup:
    """Create and register a dataset dataset_id with studies."""
    dataset_config = {
        "id": dataset_id,
    }
    if dataset_config_update:
        config_update = yaml.safe_load(dataset_config_update)
        dataset_config.update(config_update)

    dataset = GenotypeDataGroup(
        Box(dataset_config, default_box=True), studies)
    # pylint: disable=protected-access
    gpf_instance._variants_db.register_genotype_data(dataset)

    return dataset


def study_update(
    gpf_instance: GPFInstance,
    study: GenotypeData, study_config_update: dict[str, Any],
) -> GenotypeData:
    update_study_config(gpf_instance, study.study_id, study_config_update)
    gpf_instance.reload()
    return gpf_instance.get_genotype_data(study.study_id)
