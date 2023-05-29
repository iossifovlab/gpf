import abc
from typing import Optional, Any

from dae.annotation.annotatable import Annotatable, VCFAllele
from dae.annotation.annotation_pipeline import Annotator
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.annotation_pipeline import AnnotatorInfo
from dae.annotation.annotation_factory import AnnotationConfigParser

from dae.genomic_resources.repository import GenomicResource

from dae.genomic_resources.genomic_scores import GenomicScore
from dae.genomic_resources.genomic_scores import \
    build_allele_score_from_resource
from dae.genomic_resources.genomic_scores import \
    build_position_score_from_resource
from dae.genomic_resources.genomic_scores import \
    build_np_score_from_resource
from dae.genomic_resources.genomic_scores import PositionScoreQuery
from dae.genomic_resources.genomic_scores import NPScoreQuery
from dae.genomic_resources.genomic_scores import AlleleScoreQuery


def get_genomic_resource(pipeline: AnnotationPipeline, info: AnnotatorInfo,
                         resource_type: str) -> GenomicResource:
    if "resource_id" not in info.parameters:
        raise ValueError(f"The {info} has not 'resource_id' parameters")
    resource_id = info.parameters["resource_id"]
    resource = pipeline.repository.get_resource(resource_id)
    if resource.get_type() != resource_type:
        raise ValueError(f"The {info} requires 'resource_id' to point to a "
                         "resource of type position_score.")
    return resource


class GenomicScoreAnnotatorBase(Annotator):

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo,
                 score: GenomicScore):

        info.resources.append(score.resource)
        if not info.attributes:
            info.attributes = AnnotationConfigParser.parse_raw_attributes(
                score.get_default_annotation_attributes())

        for attribute_config in info.attributes:
            score_config = score.get_score_config(attribute_config.source)
            if score_config is None:
                message = f"The score '{attribute_config.source}' is " + \
                          f"unknown in '{score.resource.get_id()}' " + \
                          "resource!"
                raise ValueError(message)
            attribute_config.type = score_config.type
            attribute_config.description = score_config.desc

            hist_url = f"{score.resource.get_url()}" + \
                       f"/statistics/histogram_{score}.png"
            attribute_config.documentation = attribute_config.description + \
                "\n\n" + score_config.desc + "\n\n" + \
                f"![HISTOGRAM]({hist_url})"
        super().__init__(pipeline, info)

        self.score = score
        self.simple_score_queries = [attr.source for attr in info.attributes]
        self._region_length_cutoff = info.parameters.get(
            "region_length_cutoff", 500_000)

    def open(self):
        self.score.open()
        return super().open()

    def close(self):
        self.score.close()
        super().close()


class PositionScoreAnnotatorBase(GenomicScoreAnnotatorBase):

    @abc.abstractmethod
    def _fetch_substitution_scores(self, allele: VCFAllele) \
            -> Optional[list[Any]]:
        pass

    @abc.abstractmethod
    def _fetch_aggregated_scores(self, chrom, pos_begin, pos_end) -> list[Any]:
        pass

    def annotate(self, annotatable: Annotatable, _: dict[str, Any]) \
            -> dict[str, Any]:

        if annotatable is None:
            return self._empty_result()

        if annotatable.chromosome not in \
                self.score.get_all_chromosomes():
            return self._empty_result()

        if annotatable.type == Annotatable.Type.SUBSTITUTION:
            assert isinstance(annotatable, VCFAllele)
            scores = self._fetch_substitution_scores(annotatable)
        else:
            if len(annotatable) > self._region_length_cutoff:
                scores = None
            else:
                scores = self._fetch_aggregated_scores(
                    annotatable.chrom, annotatable.pos, annotatable.pos_end)
        if not scores:
            return self._empty_result()

        return dict(zip([att.name for att in self.attributes], scores))


def build_position_score_annotator(pipeline: AnnotationPipeline,
                                   info: AnnotatorInfo) -> Annotator:
    return PositionScoreAnnotator(pipeline, info)


class PositionScoreAnnotator(PositionScoreAnnotatorBase):

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):

        resource = get_genomic_resource(pipeline, info, "position_score")
        self.position_score = build_position_score_from_resource(resource)
        super().__init__(pipeline, info, self.position_score)

        self.position_score_queries = \
            [PositionScoreQuery(att_info.source,
                                att_info.parameters.get(
                                    "position_aggregator"))
                for att_info in info.attributes]

    def _fetch_substitution_scores(self, allele: VCFAllele) \
            -> Optional[list[Any]]:
        return self.position_score.fetch_scores(
            allele.chromosome, allele.position, self.simple_score_queries)

    def _fetch_aggregated_scores(self, chrom, pos_begin, pos_end) -> list[Any]:
        scores_agg = self.position_score.fetch_scores_agg(
            chrom, pos_begin, pos_end, self.position_score_queries
        )
        return [sagg.get_final() for sagg in scores_agg]


def build_np_score_annotator(pipeline: AnnotationPipeline,
                             info: AnnotatorInfo) -> Annotator:
    return NPScoreAnnotator(pipeline, info)


class NPScoreAnnotator(PositionScoreAnnotatorBase):
    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):
        resource = get_genomic_resource(pipeline, info, "np_score")
        self.np_score = build_np_score_from_resource(resource)
        super().__init__(pipeline, info, self.np_score)
        self.np_score_queries = \
            [NPScoreQuery(att_info.source,
                          att_info.parameters.get("position_aggregator"),
                          att_info.parameters.get("nucleotide_aggregator"))
                for att_info in info.attributes]

    def _fetch_substitution_scores(self, allele: VCFAllele):
        return self.np_score.fetch_scores(allele.chromosome, allele.position,
                                          allele.reference, allele.alternative,
                                          self.simple_score_queries)

    def _fetch_aggregated_scores(self, chrom, pos_begin, pos_end) -> list[Any]:
        scores_agg = self.np_score.fetch_scores_agg(chrom, pos_begin, pos_end,
                                                    self.np_score_queries)
        return [sagg.get_final() for sagg in scores_agg]


def build_allele_score_annotator(pipeline: AnnotationPipeline,
                                 info: AnnotatorInfo) -> Annotator:
    return AlleleScoreAnnotator(pipeline, info)


class AlleleScoreAnnotator(GenomicScoreAnnotatorBase):
    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):
        resource = get_genomic_resource(pipeline, info, "allele_score")
        self.allele_score = build_allele_score_from_resource(resource)
        super().__init__(pipeline, info, self.allele_score)
        self.allele_score_queries = \
            [AlleleScoreQuery(att_info.source,
                              att_info.parameters.get("position_aggregator"),
                              att_info.parameters.get("allele_aggregator"))
                for att_info in info.attributes]

    def _fetch_vcf_allele_score(self, allele: VCFAllele) \
            -> Optional[list[Any]]:
        return self.allele_score.fetch_scores(
            allele.chromosome, allele.position, allele.reference,
            allele.alternative, self.simple_score_queries)

    def _fetch_aggregated_scores(self, annotatable: Annotatable) -> list[Any]:
        scores_agg = self.allele_score.fetch_scores_agg(
            annotatable.chrom, annotatable.pos, annotatable.pos_end,
            self.allele_score_queries)
        return [sagg.get_final() for sagg in scores_agg]

    def annotate(self, annotatable: Annotatable, _: dict[str, Any]) \
            -> dict[str, Any]:

        if annotatable is None:
            return self._empty_result()

        if annotatable.chromosome not in self.score.get_all_chromosomes():
            return self._empty_result()

        if isinstance(annotatable, VCFAllele):
            scores = self._fetch_vcf_allele_score(annotatable)
        else:
            if len(annotatable) > self._region_length_cutoff:
                scores = None
            else:
                scores = self._fetch_aggregated_scores(annotatable)

        if scores is None:
            return self._empty_result()

        return dict(zip([att.name for att in self.attributes], scores))
