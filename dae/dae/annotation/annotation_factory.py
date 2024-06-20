"""Factory for creation of annotation pipeline."""

import logging
from collections import Counter
from pathlib import Path
from typing import Callable, Optional

from dae.annotation.annotation_config import (
    AnnotationConfigParser,
    AnnotationConfigurationError,
    RawPipelineConfig,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
    AnnotatorInfo,
    AttributeInfo,
    InputAnnotableAnnotatorDecorator,
    ReannotationPipeline,
    ValueTransformAnnotatorDecorator,
)
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import (
    GenomicResourceRepo,
)

logger = logging.getLogger(__name__)


_ANNOTATOR_FACTORY_REGISTRY: dict[
    str, Callable[[AnnotationPipeline, AnnotatorInfo], Annotator]] = {}
_EXTENTIONS_LOADED = False


def _load_annotator_factory_plugins() -> None:
    # pylint: disable=global-statement
    global _EXTENTIONS_LOADED
    if _EXTENTIONS_LOADED:
        return
    # pylint: disable=import-outside-toplevel
    from importlib_metadata import entry_points
    discovered_entries = entry_points(group="dae.annotation.annotators")
    for entry in discovered_entries:
        annotator_type = entry.name
        factory = entry.load()
        if annotator_type in _ANNOTATOR_FACTORY_REGISTRY:
            logger.warning(
                "overwriting annotator type: %s", annotator_type)
        _ANNOTATOR_FACTORY_REGISTRY[annotator_type] = factory
    _EXTENTIONS_LOADED = True


def get_annotator_factory(
    annotator_type: str,
) -> Callable[[AnnotationPipeline, AnnotatorInfo], Annotator]:
    """Find and return a factory function for creation of an annotator type.

    If the specified annotator type is not found, this function raises
    `ValueError` exception.

    :return: the annotator factory for the specified annotator type.
    :raises ValueError: when can't find an annotator  factory for the
        specified annotator type.
    """
    _load_annotator_factory_plugins()
    if annotator_type not in _ANNOTATOR_FACTORY_REGISTRY:
        raise ValueError(f"unsupported annotator type: {annotator_type}")
    return _ANNOTATOR_FACTORY_REGISTRY[annotator_type]


def get_available_annotator_types() -> list[str]:
    """Return the list of all registered annotator factory types."""
    _load_annotator_factory_plugins()
    return list(_ANNOTATOR_FACTORY_REGISTRY.keys())


def register_annotator_factory(
    annotator_type: str,
    factory: Callable[[AnnotationPipeline, AnnotatorInfo], Annotator],
) -> None:
    """Register additional annotator factory.

    By default all genotype storage factories should be registered at
    `[dae.genotype_storage.factories]` extenstion point. All registered
    factories are loaded automatically. This function should be used if you
    want to bypass extension point mechanism and register addition genotype
    storage factory programatically.
    """
    _load_annotator_factory_plugins()
    if annotator_type in _ANNOTATOR_FACTORY_REGISTRY:
        logger.warning("overwriting annotator type: %s", annotator_type)
    _ANNOTATOR_FACTORY_REGISTRY[annotator_type] = factory


def build_annotation_pipeline(
        pipeline_config: Optional[list[AnnotatorInfo]] = None,
        pipeline_config_raw: Optional[RawPipelineConfig] = None,
        pipeline_config_file: Optional[str] = None,
        pipeline_config_str: Optional[str] = None,
        grr_repository: Optional[GenomicResourceRepo] = None,
        grr_repository_file: Optional[str] = None,
        grr_repository_definition: Optional[dict] = None,
        *,
        allow_repeated_attributes: bool = False,
        work_dir: Optional[Path] = None,
) -> AnnotationPipeline:
    """Build an annotation pipeline."""
    if not grr_repository:
        grr_repository = build_genomic_resource_repository(
            definition=grr_repository_definition,
            file_name=grr_repository_file)
    else:
        assert grr_repository_file is None
        assert grr_repository_definition is None

    preambule = None
    if pipeline_config_file is not None:
        assert pipeline_config is None
        assert pipeline_config_raw is None
        assert pipeline_config_str is None
        preambule, pipeline_config = AnnotationConfigParser.parse_config_file(
            pipeline_config_file, grr=grr_repository)
    elif pipeline_config_str is not None:
        assert pipeline_config_raw is None
        assert pipeline_config is None
        preambule, pipeline_config = AnnotationConfigParser.parse_str(
            pipeline_config_str, grr=grr_repository)
    elif pipeline_config_raw is not None:
        assert pipeline_config is None
        preambule, pipeline_config = AnnotationConfigParser.parse_raw(
            pipeline_config_raw, grr=grr_repository)
    assert pipeline_config is not None

    pipeline = AnnotationPipeline(grr_repository)
    pipeline.preambule = preambule

    try:
        for idx, annotator_config in enumerate(pipeline_config):
            if work_dir is not None:
                annotator_config.parameters._data["work_dir"] = work_dir / \
                    f"A{idx}_{annotator_config.type}"
                annotator_config.parameters._used_keys.add("work_dir")
            builder = get_annotator_factory(annotator_config.type)
            annotator = builder(pipeline, annotator_config)
            annotator = InputAnnotableAnnotatorDecorator.decorate(annotator)
            annotator = ValueTransformAnnotatorDecorator.decorate(annotator)
            check_for_unused_parameters(annotator_config)
            check_for_repeated_attributes_in_annotator(annotator_config)
            pipeline.add_annotator(annotator)
    except ValueError as value_error:
        raise AnnotationConfigurationError(
            f"The {annotator_config.annotator_id} annotator"
            f" configuration is incorrect: ",
            value_error) from value_error

    check_for_repeated_attributes_in_pipeline(
        pipeline, allow_repeated_attributes=allow_repeated_attributes,
    )

    return pipeline


def copy_annotation_pipeline(
    pipeline: AnnotationPipeline,
) -> AnnotationPipeline:
    """Copy an annotation pipeline instance."""
    infos = []
    for annotator in pipeline.annotators:
        src = annotator.get_info()
        attributes = [
            AttributeInfo(
                src_attr.name,
                src_attr.source,
                src_attr.internal,
                src_attr.parameters._data,  # noqa pylint: disable=W0212
                src_attr.type,
                src_attr.description,
                src_attr.documentation,
            ) for src_attr in src.attributes
        ]
        infos.append(AnnotatorInfo(
            src.type,
            attributes,
            src.parameters._data,  # noqa pylint: disable=W0212
            "",
            None,
            src.annotator_id,
        ))
    return build_annotation_pipeline(
        pipeline_config=infos,
        grr_repository=pipeline.repository,
    )


def copy_reannotation_pipeline(
    pipeline: ReannotationPipeline,
) -> ReannotationPipeline:
    """Copy a reannotation pipeline instance."""
    return ReannotationPipeline(
        copy_annotation_pipeline(pipeline.pipeline_new),
        copy_annotation_pipeline(pipeline.pipeline_old),
    )


def check_for_repeated_attributes_in_annotator(
    annotator_config: AnnotatorInfo,
) -> None:
    """Check for repeated attributes in annotator configuration."""
    annotator_names_list = [att.name for att in annotator_config.attributes]
    annotator_names_set = set(annotator_names_list)
    if len(annotator_names_set) < len(annotator_names_list):
        repeated_annotator_names = ",".join(sorted(
            [att for att, cnt in Counter(annotator_names_list).items()
             if cnt > 1]))
        raise ValueError("The annotator has repeated attributes: "
                         f"{repeated_annotator_names}")


def check_for_repeated_attributes_in_pipeline(
    pipeline: AnnotationPipeline, *, allow_repeated_attributes: bool = False,
) -> None:
    """Check for repeated attributes in pipeline configuration."""
    pipeline_names_set = Counter(att.name for att in pipeline.get_attributes())
    repeated_attributes = {
        att for att, cnt in Counter(pipeline_names_set).items() if cnt > 1
    }

    if not repeated_attributes:
        return

    if allow_repeated_attributes:
        resolve_repeated_attributes(pipeline, repeated_attributes)
        return

    overlaps: dict[str, list[str]] = {}
    # reversed so that it follows the order of the pipeline config
    for annotator in reversed(pipeline.annotators):
        annotator_id = annotator.get_info().annotator_id
        for attr in annotator.attributes:
            if attr.name in repeated_attributes:
                overlaps.setdefault(attr.name, []).append(annotator_id)
    raise AnnotationConfigurationError(
        f"Repeated attributes in pipeline were found - {overlaps}",
    )


def resolve_repeated_attributes(
    pipeline: AnnotationPipeline, repeated_attributes: set[str],
) -> None:
    """Resolve repeated attributes in pipeline configuration via renaming."""
    for rep in repeated_attributes:
        for annotator in pipeline.annotators:
            for attribute in annotator.attributes:
                if attribute.name == rep:
                    attribute.name = \
                        f"{attribute.name}_{annotator.get_info().annotator_id}"


def check_for_unused_parameters(info: AnnotatorInfo) -> None:
    """Check annotator configuration for unused parameters."""
    unused_annotator_parameters = info.parameters.get_unused_keys()
    if unused_annotator_parameters:
        raise ValueError("The are unused annotator parameters: "
                         f"{unused_annotator_parameters}")

    for att in info.attributes:
        unused_params = att.parameters.get_unused_keys()
        if unused_params:
            raise ValueError("There are unused annotator attribute "
                             f"parameters: {','.join(sorted(unused_params))}")
