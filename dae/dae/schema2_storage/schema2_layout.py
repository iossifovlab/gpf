import logging
from dataclasses import dataclass

from dae.utils import fs_utils

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Schema2DatasetLayout:
    """Schema2 dataset layout data class."""

    study: str
    pedigree: str
    summary: str | None
    family: str | None
    meta: str
    base_dir: str | None = None

    def has_variants(self) -> bool:
        return self.summary is not None and self.family is not None


def load_schema2_dataset_layout(study_dir: str) -> Schema2DatasetLayout:
    """
    Create dataset layout for a given directory.

    Assumes that the dataset already exists, therefore it should check whether
    summary and family tables exist.
    """
    summary_path = fs_utils.join(study_dir, "summary")
    summary = summary_path if fs_utils.exists(summary_path) else None

    family_path = fs_utils.join(study_dir, "family")
    family = family_path if fs_utils.exists(family_path) else None

    return Schema2DatasetLayout(
        study_dir,
        fs_utils.join(study_dir, "pedigree", "pedigree.parquet"),
        summary,
        family,
        fs_utils.join(study_dir, "meta", "meta.parquet"))


def create_schema2_dataset_layout(study_dir: str) -> Schema2DatasetLayout:
    """
    Create dataset layout for a given directory.

    Used for creating new datasets, where all tables should exist.
    """
    summary = fs_utils.join(study_dir, "summary")
    family = fs_utils.join(study_dir, "family")
    return Schema2DatasetLayout(
        study_dir,
        fs_utils.join(study_dir, "pedigree", "pedigree.parquet"),
        summary,
        family,
        fs_utils.join(study_dir, "meta", "meta.parquet"))
