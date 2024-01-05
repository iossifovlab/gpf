"""This contains the implementation of the three score annotators.

Genomic score annotators defined are positions_score, np_score,
and allele_score.
"""
import logging
import abc
import textwrap
from typing import Callable, Optional, Any, cast

from dae.annotation.annotatable import Annotatable, VCFAllele
from dae.annotation.annotation_pipeline import Annotator, AttributeInfo
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.annotation_pipeline import AnnotatorInfo
from dae.annotation.annotation_factory import AnnotationConfigParser
from dae.genomic_resources.aggregators import validate_aggregator

from dae.genomic_resources.repository import GenomicResource

from dae.genomic_resources.genomic_scores import GenomicScore, ScoreDef
from dae.genomic_resources.genomic_scores import \
    PositionScoreQuery, NPScoreQuery, AlleleScoreQuery, ScoreQuery, \
    PositionScore, NPScore, AlleleScore


logger = logging.getLogger(__name__)


def get_genomic_resource(
        pipeline: AnnotationPipeline, info: AnnotatorInfo,
        resource_type: str) -> GenomicResource:
    """Return genomic score resource used for given genomic score annotator."""
    if "resource_id" not in info.parameters:
        raise ValueError(f"The {info} has not 'resource_id' parameters")
    resource_id = info.parameters["resource_id"]
    resource = pipeline.repository.get_resource(resource_id)
    if resource.get_type() != resource_type:
        raise ValueError(f"The {info} requires 'resource_id' to point to a "
                         "resource of type position_score.")
    return resource


class GenomicScoreAnnotatorBase(Annotator):
    """Genomic score base annotator."""

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo,
                 score: GenomicScore):

        super().__init__(pipeline, info)

        self.score = score
        self._region_length_cutoff = info.parameters.get(
            "region_length_cutoff", 500_000)

        info.resources.append(score.resource)
        if not info.attributes:
            info.attributes = AnnotationConfigParser.parse_raw_attributes(
                score.get_default_annotation_attributes())

        for attribute_info in info.attributes:
            score_def = score.get_score_definition(attribute_info.source)
            if score_def is None:
                message = f"The score '{attribute_info.source}' is " + \
                          f"unknown in '{score.resource.get_id()}' " + \
                          "resource!"
                raise ValueError(message)
            attribute_info.type = score_def.value_type
            attribute_info.description = score_def.desc

            self._create_the_attribute_documentation(attribute_info)
        self.simple_score_queries: list[str] = [
            attr.source for attr in info.attributes]

    def open(self) -> Annotator:
        self.score.open()
        return self

    def is_open(self) -> bool:
        return self.score.is_open()

    def _collect_score_queries(self) -> list[ScoreQuery]:
        return []

    def close(self) -> None:
        self.score.close()
        super().close()

    def _create_the_attribute_documentation(
        self, attribute_info: AttributeInfo
    ) -> None:
        hist_url = self.score.get_histogram_image_url(attribute_info.source)
        score_def = self.score.get_score_definition(attribute_info.source)
        assert score_def is not None
        # pylint: disable=protected-access
        attribute_info._documentation = f"""
{attribute_info.description}

![HISTOGRAM]({hist_url})

small values: {score_def.small_values_desc},
large_values {score_def.large_values_desc}
        """

    def _build_score_aggregator_documentation(
        self, attribute_info: AttributeInfo,
        aggregator: str,
        attribute_conf_agg: Optional[str]
    ) -> str:
        """Collect score aggregator documentation."""
        default_aggregators = {
            "position_aggregator": {
                "float": "mean",
                "int": "mean",
                "str": "concatenate"
            },
            "nucleotide_aggregator": {
                "float": "max",
                "int": "max",
                "str": "concatenate"
            },
            "allele_aggregator": {
                "float": "max",
                "int": "max",
                "str": "concatenate"
            }
        }
        aggregators_score_def_att: \
            dict[str, Callable[[ScoreDef], Optional[str]]] = {
                "position_aggregator":
                lambda sc: sc.pos_aggregator,
                "nucleotide_aggregator":
                lambda sc: sc.nuc_aggregator,
                "allele_aggregator":
                lambda sc: sc.allele_aggregator
            }
        if attribute_conf_agg is None:
            score_def = self.score.get_score_definition(attribute_info.source)
            assert score_def is not None
            value = aggregators_score_def_att[aggregator](
                cast(ScoreDef, score_def))
            if value is not None:
                value_str = f"`{value}`"
            else:
                value = default_aggregators[aggregator][score_def.value_type]
                value_str = f"`{value}` [type default]"
        else:
            value_str = attribute_conf_agg
        return f"**{aggregator}**: {value_str}"

    def add_score_aggregator_documentation(
            self, attribute_info: AttributeInfo,
            aggregator: str,
            attribute_conf_agg: Optional[str]) -> None:
        """Collect score aggregator documentation."""
        # pylint: disable=protected-access
        aggregator_doc = self._build_score_aggregator_documentation(
            attribute_info, aggregator, attribute_conf_agg)

        attribute_info._documentation = \
            f"{attribute_info.documentation}\n\n{aggregator_doc}"

    @abc.abstractmethod
    def build_score_aggregator_documentation(
        self, attr_info: AttributeInfo
    ) -> list[str]:
        """Construct score aggregator documentation."""


class PositionScoreAnnotatorBase(GenomicScoreAnnotatorBase):
    """Defines position score base annotator class."""

    @abc.abstractmethod
    def _fetch_substitution_scores(self, allele: VCFAllele) \
            -> Optional[list[Any]]:
        pass

    @abc.abstractmethod
    def _fetch_aggregated_scores(
            self, chrom: str, pos_begin: int, pos_end: int) -> list[Any]:
        pass

    def annotate(
        self, annotatable: Optional[Annotatable], _: dict[str, Any]
    ) -> dict[str, Any]:

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
    """This class implements the position_score annotator.

    The position_score
    annotator requires the resrouce_id parameter, whose value must be an id
    of a genomic resource of type position_score.

    The position_score resource provides a set of scores (see …) that the
    position_score annotator uses as attributes to assign to the annotatable.

    The position_score annotator recognized one attribute level parameter
    called position_aggregator that controls how the position scores are
    aggregator for annotates that ref to a region of the reference genome.
    """

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):

        resource = get_genomic_resource(pipeline, info, "position_score")
        self.position_score = PositionScore(resource)
        super().__init__(pipeline, info, self.position_score)

        self.position_score_queries = []
        info.documentation += textwrap.dedent("""

* Annotator to use with genomic scores depending on genomic position like
  phastCons, phyloP, FitCons2, etc.

* <a href="https://www.iossifovlab.com/gpfuserdocs/administration/annotation_tools.html#position-score" target="_blank">More info</a>

""")  # noqa

        for att_info in info.attributes:
            pos_aggregator = att_info.parameters.get("position_aggregator")
            if pos_aggregator:
                validate_aggregator(pos_aggregator)
            self.position_score_queries.append(
                PositionScoreQuery(att_info.source, pos_aggregator))

            self.add_score_aggregator_documentation(
                att_info, "position_aggregator", pos_aggregator)

    def build_score_aggregator_documentation(
        self, attr_info: AttributeInfo
    ) -> list[str]:
        """Collect score aggregator documentation."""
        # pylint: disable=protected-access
        pos_aggregator = attr_info.parameters.get("position_aggregator")

        doc = self._build_score_aggregator_documentation(
            attr_info, "position_aggregator", pos_aggregator)
        return [doc]

    def _fetch_substitution_scores(self, allele: VCFAllele) \
            -> Optional[list[Any]]:
        return self.position_score.fetch_scores(
            allele.chromosome, allele.position, self.simple_score_queries)

    def _fetch_aggregated_scores(
            self, chrom: str, pos_begin: int, pos_end: int) -> list[Any]:
        scores_agg = self.position_score.fetch_scores_agg(
            chrom, pos_begin, pos_end, self.position_score_queries
        )
        return [sagg.get_final() for sagg in scores_agg]


def build_np_score_annotator(pipeline: AnnotationPipeline,
                             info: AnnotatorInfo) -> Annotator:
    return NPScoreAnnotator(pipeline, info)


class NPScoreAnnotator(PositionScoreAnnotatorBase):
    """This class implements np_score annotator."""

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):
        resource = get_genomic_resource(pipeline, info, "np_score")
        self.np_score = NPScore(resource)
        super().__init__(pipeline, info, self.np_score)

        self.np_score_queries = []
        info.documentation += textwrap.dedent("""

* Annotator to use with genomic scores depending on genomic position and
  nucleotide change like CADD, MPC, etc.

* <a href="https://www.iossifovlab.com/gpfuserdocs/administration/annotation_tools.html#np-score" target="_blank">More info</a>

""")  # noqa

        for att_info in info.attributes:
            pos_agg = att_info.parameters.get("position_aggregator")
            nuc_agg = att_info.parameters.get("nucleotide_aggregator")

            for agg in [pos_agg, nuc_agg]:
                if agg:
                    validate_aggregator(agg)
            self.np_score_queries.append(
                NPScoreQuery(att_info.source, pos_agg, nuc_agg))
            self.add_score_aggregator_documentation(
                att_info, "position_aggregator", pos_agg)
            self.add_score_aggregator_documentation(
                att_info, "nucleotide_aggregator", nuc_agg)

    def build_score_aggregator_documentation(
        self, attr_info: AttributeInfo
    ) -> list[str]:
        """Collect score aggregator documentation."""
        # pylint: disable=protected-access
        pos_aggregator = attr_info.parameters.get("position_aggregator")
        pos_doc = self._build_score_aggregator_documentation(
            attr_info, "position_aggregator", pos_aggregator)

        nuc_aggregator = attr_info.parameters.get("nucleotide_aggregator")
        nuc_doc = self._build_score_aggregator_documentation(
            attr_info, "nucleotide_aggregator", nuc_aggregator
        )
        return [pos_doc, nuc_doc]

    def _fetch_substitution_scores(
            self, allele: VCFAllele) -> Optional[list[Any]]:
        return self.np_score.fetch_scores(allele.chromosome, allele.position,
                                          allele.reference, allele.alternative,
                                          self.simple_score_queries)

    def _fetch_aggregated_scores(
            self, chrom: str, pos_begin: int, pos_end: int) -> list[Any]:
        scores_agg = self.np_score.fetch_scores_agg(chrom, pos_begin, pos_end,
                                                    self.np_score_queries)
        return [sagg.get_final() for sagg in scores_agg]


def build_allele_score_annotator(pipeline: AnnotationPipeline,
                                 info: AnnotatorInfo) -> Annotator:
    return AlleleScoreAnnotator(pipeline, info)


class AlleleScoreAnnotator(GenomicScoreAnnotatorBase):
    """This class implements allele_score annotator."""

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):
        resource = get_genomic_resource(pipeline, info, "allele_score")
        self.allele_score = AlleleScore(resource)
        super().__init__(pipeline, info, self.allele_score)
        self.allele_score_queries = []
        info.documentation += textwrap.dedent("""

* Annotator to use with scores that depend on allele like
  variant frequencies, etc.

* <a href="https://www.iossifovlab.com/gpfuserdocs/administration/annotation_tools.html#allele-score" target="_blank">More info</a>

""")  # noqa

        for att_info in info.attributes:
            pos_agg = att_info.parameters.get("position_aggregator")
            all_agg = att_info.parameters.get("allele_aggregator")

            for agg in [pos_agg, all_agg]:
                if agg:
                    validate_aggregator(agg)
            self.allele_score_queries.append(
                AlleleScoreQuery(att_info.source, pos_agg, all_agg))
            self.add_score_aggregator_documentation(
                att_info, "position_aggregator", pos_agg)
            self.add_score_aggregator_documentation(
                att_info, "allele_aggregator", all_agg)

    def build_score_aggregator_documentation(
        self, attr_info: AttributeInfo
    ) -> list[str]:
        """Collect score aggregator documentation."""
        # pylint: disable=protected-access
        pos_aggregator = attr_info.parameters.get("position_aggregator")
        pos_doc = self._build_score_aggregator_documentation(
            attr_info, "position_aggregator", pos_aggregator)

        allele_aggregator = attr_info.parameters.get("allele_aggregator")
        allele_doc = self._build_score_aggregator_documentation(
            attr_info, "allele_aggregator", allele_aggregator
        )
        return [pos_doc, allele_doc]

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

    def annotate(
        self, annotatable: Optional[Annotatable], _: dict[str, Any]
    ) -> dict[str, Any]:

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
