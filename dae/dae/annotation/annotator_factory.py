import logging

from box import Box

from dae.annotation.annotator_base import Annotator

from .score_annotator import PositionScoreAnnotator, \
    NPScoreAnnotator
from .allele_score_annotator import AlleleScoreAnnotator
from .effect_annotator import EffectAnnotatorAdapter
from .lift_over_annotator import LiftOverAnnotator


logger = logging.getLogger(__name__)


class AnnotatorFactory:
    SCORE_ANNOTATOR_NAMES = {
        "position_score": PositionScoreAnnotator,
        "np_score": NPScoreAnnotator,
        "allele_score": AlleleScoreAnnotator
    }

    @classmethod
    def build_score_annotator(cls, pipeline, config):
        assert config.annotator_type in {
            "np_score", "position_score", "allele_score"}, config

        resource = pipeline.repository.get_resource(config.resource_id)
        assert resource is not None

        clazz = cls.SCORE_ANNOTATOR_NAMES.get(config.annotator_type)
        assert clazz is not None
        return clazz(config, resource)

    @classmethod
    def build_effect_annotator(cls, pipeline, config):

        if config.get("genome") is None:
            genome = pipeline.context.get_reference_genome()
            if genome is None:
                logger.error(
                    "can't create effect annotator: config has no "
                    "reference genome specified and genome is missing "
                    "in the context")
                raise ValueError(
                    "can't create effect annotator: "
                    "genome is missing in config and context")
        else:
            genome_id = config.genome
            genome = pipeline.repository.get_resource(genome_id)

        if config.get("gene_models") is None:
            gene_models = pipeline.context.get_gene_models()
            if gene_models is None:
                raise ValueError(
                    "can't create effect annotator: "
                    "gene models are missing in config and context")
        else:
            gene_models = pipeline.repository.get_resource(
                config.gene_models)
            if gene_models is None:
                raise ValueError(
                    f"can't find gene models {config.gene_models} "
                    f"in the specified repository "
                    f"{pipeline.repository.repo_id}")
        return EffectAnnotatorAdapter(config, genome, gene_models)

    @classmethod
    def build_liftover_annotator(cls, pipeline, config):
        assert config.annotator_type == "liftover_annotator"

        chain = pipeline.repository.get_resource(config.chain)
        if chain is None:
            raise ValueError(
                f"can't create liftover annotator; "
                f"can't find liftover chain {config.chain}")

        target_genome = pipeline.repository.get_resource(config.target_genome)
        if target_genome is None:
            raise ValueError(
                f"can't create liftover annotator; "
                f"can't find liftover target genome: "
                f"{config.target_genome}")

        return LiftOverAnnotator(config, chain, target_genome)

    @classmethod
    def build(cls, pipeline, config: Box) -> Annotator:

        if config.annotator_type in {
                "np_score", "position_score", "allele_score"}:
            return cls.build_score_annotator(pipeline, config)
        elif config.annotator_type == "effect_annotator":
            return cls.build_effect_annotator(pipeline, config)
        elif config.annotator_type == "liftover_annotator":
            return cls.build_liftover_annotator(pipeline, config)

        logger.error(f"unexpected annotator type: {config}")
        raise ValueError(f"unexpected annotator type: {config}")
