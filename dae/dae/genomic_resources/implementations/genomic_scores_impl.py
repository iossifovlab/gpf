from __future__ import annotations

import logging
import textwrap
import json
from typing import Any, Optional, cast, Iterable

from jinja2 import Template

from dae.genomic_resources.repository import GenomicResourceRepo

from dae.task_graph.graph import Task, TaskGraph
from dae.utils.regions import Region, split_into_regions, \
    get_chromosome_length_tabix
from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.reference_genome import ReferenceGenome, \
    build_reference_genome_from_resource
from dae.genomic_resources.resource_implementation import \
    GenomicResourceImplementation, \
    InfoImplementationMixin
from dae.genomic_resources.genomic_position_table.table_inmemory import \
    InmemoryGenomicPositionTable
from dae.genomic_resources.genomic_position_table import \
    TabixGenomicPositionTable

from dae.genomic_resources.histogram import \
    NumberHistogramConfig, CategoricalHistogramConfig, \
    NullHistogramConfig, HistogramConfig, \
    NullHistogram, Histogram, \
    HistogramError, \
    build_empty_histogram, \
    build_default_histogram_conf
from dae.genomic_resources.statistics.min_max import MinMaxValue
from dae.genomic_resources.genomic_scores import GenomicScore, \
    build_score_from_resource


logger = logging.getLogger(__name__)


class GenomicScoreImplementation(
    GenomicResourceImplementation,
    InfoImplementationMixin
):
    # pylint: disable=too-many-public-methods
    """Genomic scores base class."""

    def __init__(self, resource: GenomicResource):
        super().__init__(resource)
        self.score: GenomicScore = build_score_from_resource(resource)

    def get_config_histograms(self) -> dict[str, Any]:
        """Collect all configurations of histograms for the genomic score."""
        result: dict[str, Any] = {}
        for score_id, score_def in self.score.score_definitions.items():
            result[score_id] = score_def.hist_conf

        return result

    def get_template(self) -> Template:
        return Template(textwrap.dedent("""
        {% extends base %}
        {% block content %}

        {% set impl = data.genomic_scores %}
        {% set scores = impl.score %}

        <h1>Scores</h1>

        <table border="1">
        <tr>
        <th>id</th>
        <th>type</th>
        <th>default annotation</th>
        <th>description</th>
        <th>histogram</th>
        <th>range</th>
        </tr>

        {%- for score_id, score in scores.score_definitions.items() -%}

        <tr class="score-definition">

        <td>{{ score_id }}</td>

        <td>{{ score.value_type }}</td>

        {% set d_atts = scores.get_default_annotation_attribute(score_id) %}
        <td>
            <p>{{ d_atts }}</p>
        </td>

        <td>{{ score.desc }}</td>

        <td>
        {% set hist = impl.score.get_score_histogram(score_id) %}
        {%- if hist.type != 'null_histogram' %}
        {% set hist_image_file =
            impl.score.get_histogram_image_filename(score_id) %}
        <img src="{{ hist_image_file }}"
            alt="{{ "HISTOGRAM FOR " + score_id }}"
            title={{ score_id }}
            width="200">
        {%- else -%}
        NO HISTOGRAM
        {%- endif -%}
        </td>

        <td>

        {%- if hist.type != 'null_histogram' %}
        {{ hist.values_domain() }}
        {%- else -%}
        NO DOMAIN
        {%- endif -%}

        </td>

        </tr>
        {%- endfor %}

        </table>

        {% endblock %}
        """))

    def _get_template_data(self) -> dict[str, Any]:
        return {"genomic_scores": self}

    def get_info(self) -> str:
        return InfoImplementationMixin.get_info(self)

    def add_statistics_build_tasks(
        self,
        task_graph: TaskGraph,
        **kwargs: Any
    ) -> list[Task]:
        with self.score.open():
            region_size = kwargs.get("region_size", 1_000_000)
            grr = kwargs.get("grr")

            all_min_max_scores = []
            all_hist_confs: dict[str, HistogramConfig] = {}

            impl = build_score_implementation_from_resource(self.resource)
            for score_id, score_def in impl.score.score_definitions.items():
                if score_def.hist_conf is not None:
                    hist_conf = score_def.hist_conf
                else:
                    hist_conf = build_default_histogram_conf(
                        score_def.value_type)
                if isinstance(hist_conf, NullHistogramConfig):
                    all_hist_confs[score_id] = hist_conf
                    continue

                if isinstance(hist_conf, CategoricalHistogramConfig):
                    all_hist_confs[score_id] = hist_conf
                    continue

                assert isinstance(hist_conf, NumberHistogramConfig)
                if not hist_conf.has_view_range():
                    all_min_max_scores.append(score_id)
                all_hist_confs[score_id] = hist_conf

            min_max_task = None
            if all_min_max_scores:
                _, min_max_task = self._add_min_max_tasks(
                    task_graph, all_min_max_scores, region_size, grr)

            _, _, save_task = self._add_histogram_tasks(
                task_graph, all_hist_confs, min_max_task, region_size, grr)

            return [save_task]

    _REF_GENOME_CACHE: dict[str, Any] = {}

    @property
    def files(self) -> set[str]:
        files = set()
        files.add(self.score.table.definition.filename)
        if isinstance(self.score.table, TabixGenomicPositionTable):
            files.add(f"{self.score.table.definition.filename}.tbi")
        return files

    @staticmethod
    def _get_reference_genome_cached(
        grr: Optional[GenomicResourceRepo], genome_id: Optional[str]
    ) -> Optional[ReferenceGenome]:
        if genome_id is None or grr is None:
            return None
        if genome_id in GenomicScoreImplementation._REF_GENOME_CACHE:
            return cast(
                ReferenceGenome,
                GenomicScoreImplementation._REF_GENOME_CACHE[genome_id]
            )
        try:
            ref_genome = build_reference_genome_from_resource(
                grr.get_resource(genome_id)
            )
            logger.info(
                "Using reference genome label <%s> ",
                genome_id,
            )
        except FileNotFoundError:
            logger.warning(
                "Couldn't find reference genome %s",
                genome_id,
            )
            return None
        ref_genome.open()
        GenomicScoreImplementation._REF_GENOME_CACHE[genome_id] = ref_genome
        return ref_genome

    def _get_chrom_regions(
        self, region_size: int, grr: Optional[GenomicResourceRepo] = None
    ) -> list[Region]:
        regions = []
        ref_genome_id = cast(
            str,
            self.resource.get_labels().get("reference_genome")
        )
        ref_genome = self._get_reference_genome_cached(grr, ref_genome_id)
        for chrom in self.score.get_all_chromosomes():
            if ref_genome is not None and chrom in ref_genome.chromosomes:
                chrom_length = ref_genome.get_chrom_length(chrom)
            else:
                if isinstance(self.score.table, InmemoryGenomicPositionTable):
                    # raise ValueError("In memory tables are not supported")
                    chrom_length = \
                        max(line.pos_end
                            for line in
                            self.score.table.get_records_in_region(chrom))
                else:
                    assert isinstance(self.score.table,
                                      TabixGenomicPositionTable)
                    assert self.score.table.pysam_file is not None
                    fchrom = self.score.table.unmap_chromosome(chrom)
                    if fchrom is not None:
                        chrom_length = get_chromosome_length_tabix(
                            self.score.table.pysam_file, fchrom)
                if chrom_length is None:
                    logger.warning(
                        "unable to find chromosome length for %s", chrom)
                    continue

            regions.extend(
                split_into_regions(
                    chrom,
                    chrom_length,
                    region_size
                )
            )
        return regions

    @property
    def resource_id(self) -> str:
        return self.score.resource_id

    def _add_min_max_tasks(
        self,
        graph: TaskGraph,
        score_ids: Iterable[str],
        region_size: int,
        grr: Optional[GenomicResourceRepo] = None
    ) -> tuple[list[Task], Task]:
        """
        Add and return calculation, merging and saving tasks for min max.

        The tasks are returned in a triple containing a list of calculation
        tasks, the merge task and the save task.
        """
        min_max_tasks = []
        regions = self._get_chrom_regions(region_size, grr)
        for region in regions:
            chrom = region.chrom
            start = region.start
            end = region.stop
            min_max_tasks.append(graph.create_task(
                f"{self.resource_id}_calculate_min_max_{chrom}_{start}_{end}",
                GenomicScoreImplementation._do_min_max,
                [self.resource, score_ids, chrom, start, end],
                []
            ))
        merge_task = graph.create_task(
            f"{self.resource_id}_merge_min_max",
            GenomicScoreImplementation._merge_min_max,
            [score_ids, *min_max_tasks],
            min_max_tasks
        )
        return min_max_tasks, merge_task

    @staticmethod
    def _do_min_max(
        resource: GenomicResource,
        score_ids: Iterable[str],
        chrom: str, start: int, end: int
    ) -> dict[str, MinMaxValue]:
        impl = build_score_implementation_from_resource(resource)
        result = {
            scr_id: MinMaxValue(scr_id)
            for scr_id in score_ids
        }
        with impl.score.open():
            for rec in impl.score.fetch_region(chrom, start, end, score_ids):
                for score_id in score_ids:
                    result[score_id].add_value(rec[score_id])  # type: ignore
        return result

    @staticmethod
    def _merge_min_max(
        score_ids: Iterable[str],
        *calculate_tasks: dict[str, MinMaxValue]
    ) -> dict[str, Any]:
        res: dict[str, Optional[MinMaxValue]] = {
            score_id: None for score_id in score_ids}
        for score_id in score_ids:
            for min_max_region in calculate_tasks:
                if res[score_id] is None:
                    res[score_id] = min_max_region[score_id]
                else:
                    assert res[score_id] is not None
                    res[score_id].merge(  # type: ignore
                        min_max_region[score_id])
        return res

    @staticmethod
    def _update_hist_confs(
        all_hist_confs: dict[str, HistogramConfig],
        minmax_task: Optional[dict[str, MinMaxValue]]
    ) -> dict[str, HistogramConfig]:

        if minmax_task is None:
            return all_hist_confs

        for score_id, min_max in minmax_task.items():
            hist_conf = all_hist_confs[score_id]
            assert isinstance(hist_conf, NumberHistogramConfig)
            assert not hist_conf.has_view_range()
            hist_conf.view_range = (min_max.min, min_max.max)
        return all_hist_confs

    def _add_histogram_tasks(
        self, graph: TaskGraph, all_hist_confs: dict[str, HistogramConfig],
        minmax_task: Optional[Task],
        region_size: int, grr: Optional[GenomicResourceRepo] = None
    ) -> tuple[list[Task], Task, Task]:
        """
        Add histogram tasks for specific score id.

        The histogram tasks are dependant on the provided minmax task.
        """
        regions = self._get_chrom_regions(region_size, grr)
        if minmax_task is None:
            update_hist_confs_deps = []
        else:
            update_hist_confs_deps = [minmax_task]
        update_hist_confs = graph.create_task(
            f"{self.resource_id}_update_hist_confs",
            GenomicScoreImplementation._update_hist_confs,
            [all_hist_confs, minmax_task],
            update_hist_confs_deps
        )

        histogram_tasks = []
        for region in regions:
            chrom = region.chrom
            start = region.start
            end = region.stop
            histogram_tasks.append(graph.create_task(
                f"{self.resource_id}_calculate_histogram_"
                f"{chrom}_{start}_{end}",
                GenomicScoreImplementation._do_histogram,
                [self.resource, update_hist_confs, chrom, start, end],
                [update_hist_confs]
            ))
        merge_task = graph.create_task(
            f"{self.resource_id}_merge_histograms",
            GenomicScoreImplementation._merge_histograms,
            [self.resource, update_hist_confs, *histogram_tasks],
            [update_hist_confs, *histogram_tasks]
        )
        save_task = graph.create_task(
            f"{self.resource_id}_save_histograms",
            GenomicScoreImplementation._save_histograms,
            [self.resource, merge_task],
            [merge_task]
        )
        return histogram_tasks, merge_task, save_task

    @staticmethod
    def _do_histogram(
        resource: GenomicResource,
        all_hist_confs: dict[str, HistogramConfig],
        chrom: str, start: int, end: int
    ) -> dict[str, Histogram]:
        impl = build_score_implementation_from_resource(resource)
        result: dict[str, Histogram] = {}

        for score_id, hist_conf in all_hist_confs.items():
            if isinstance(hist_conf, NullHistogramConfig):
                continue
            result[score_id] = build_empty_histogram(hist_conf)

        score_ids = list(result.keys())
        with impl.score.open():
            for rec in impl.score.fetch_region(chrom, start, end, score_ids):
                for scr_id in score_ids:
                    try:
                        result[scr_id].add_value(rec[scr_id])  # type: ignore
                    except TypeError as err:
                        logger.error(
                            "Failed adding value %s to histogram of %s; "
                            "%s:%s-%s", rec[scr_id], resource.resource_id,
                            chrom, start, end)
                        result[scr_id] = NullHistogram(
                            NullHistogramConfig(str(err))
                        )
                    except HistogramError as err:
                        logger.warning(
                            "Histogram for %s nullified",
                            scr_id
                        )
                        result[scr_id] = NullHistogram(
                            NullHistogramConfig(str(err))
                        )
        return result

    @staticmethod
    def _merge_histograms(
        resource: GenomicResource, all_hist_confs: dict[str, HistogramConfig],
        *calculated_histograms: dict[str, Any]
    ) -> dict[str, Histogram]:
        result: dict[str, Histogram] = {}
        for score_id, hist_conf in all_hist_confs.items():
            result[score_id] = build_empty_histogram(hist_conf)

        for score_id, hist_conf in all_hist_confs.items():
            if isinstance(hist_conf, NullHistogramConfig):
                continue
            try:
                for histogram_region in calculated_histograms:
                    if score_id not in histogram_region:
                        logger.warning(
                            "region has no histogram for score %s in %s",
                            score_id, resource.resource_id)
                        continue
                    hist = histogram_region[score_id]
                    if isinstance(result[score_id], NullHistogram):
                        continue
                    if isinstance(hist, NullHistogram):
                        result[score_id] = NullHistogram(NullHistogramConfig(
                            f"Histogram for {score_id} nullified for a "
                            f"region"))
                    else:
                        result[score_id].merge(hist)

            except HistogramError as err:
                logger.error(
                    "Histogram for %s nullified",
                    score_id
                )
                result[score_id] = NullHistogram(
                    NullHistogramConfig(str(err)))
        return result

    @staticmethod
    def _save_histograms(
        resource: GenomicResource, merged_histograms: dict[str, Histogram]
    ) -> dict[str, Histogram]:
        impl = build_score_implementation_from_resource(resource)
        proto = resource.proto
        for score_id, score_histogram in merged_histograms.items():
            with proto.open_raw_file(
                resource,
                impl.score.get_histogram_filename(score_id),
                mode="wt"
            ) as outfile:
                outfile.write(score_histogram.serialize())

            if not isinstance(score_histogram, NullHistogram):
                with proto.open_raw_file(
                    resource,
                    impl.score.get_histogram_image_filename(score_id),
                    mode="wb"
                ) as outfile:
                    score_histogram.plot(outfile, score_id)
        return merged_histograms

    def calc_info_hash(self) -> bytes:
        """Compute and return the info hash."""
        return b"infohash"

    def calc_statistics_hash(self) -> bytes:
        """
        Compute the statistics hash.

        This hash is used to decide whether the resource statistics should be
        recomputed.
        """
        manifest = self.resource.get_manifest()
        config = self.get_config()
        histograms = [
            self.score.get_score_histogram(score_id) for score_id in
            self.get_config_histograms()
        ]
        return json.dumps({
            "config": {
                "scores": config.get("scores", {}),
                "histograms": list(
                    hist.to_dict()
                    for hist in histograms if hist is not None),
                "table": {
                    "config": self.score.table.definition,
                    "files_md5": {file_name: manifest[file_name].md5
                                  for file_name in sorted(self.files)}
                }
            },
            "score_config": [
                (score_def.score_id,
                 score_def.value_type,
                 score_def.col_name,
                 score_def.col_index,
                 str(sorted(score_def.na_values))
                 )
                for score_def in self.score.score_definitions.values()]
        }, indent=2).encode()


def build_score_implementation_from_resource(
    resource: GenomicResource
) -> GenomicScoreImplementation:
    return GenomicScoreImplementation(resource)
