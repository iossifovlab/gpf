import sys
import os
import glob

from dae.configuration.gpf_config_parser import GPFConfigParser

from dae.variants.attributes import VariantType

from dae.annotation.tools.annotator_base import (
    VariantAnnotatorBase,
    CompositeVariantAnnotator,
)
from dae.annotation.tools.annotator_config import AnnotationConfigParser
from dae.annotation.tools.score_file_io import ScoreFile


class VariantScoreAnnotatorBase(VariantAnnotatorBase):
    def __init__(self, config, genomes_db):
        super(VariantScoreAnnotatorBase, self).__init__(config, genomes_db)

        self._init_score_file()

        assert len(self.config.native_columns) >= 1
        self.score_names = self.config.native_columns

        assert all(
            [sn in self.score_file.score_names for sn in self.score_names]
        ), (
            self.score_names,
            self.score_file.score_names,
            self.score_file.score_filename,
        )

    def _init_score_file(self):
        assert self.config.options.scores_file, self.config.annotator

        scores_filename = os.path.abspath(self.config.options.scores_file)
        assert os.path.exists(scores_filename), scores_filename

        self.score_file = ScoreFile(
            scores_filename, self.config.options.scores_config_file
        )

    def collect_annotator_schema(self, schema):
        super(VariantScoreAnnotatorBase, self).collect_annotator_schema(schema)
        for native, output in self.config.columns.field_values_iterator():
            type_name = self.score_file.schema.columns[native].type_name
            schema.create_column(output, type_name)

    def _scores_not_found(self, aline):
        values = {
            getattr(
                self.config.columns, score_name
            ): self.score_file.no_score_value
            for score_name in self.score_names
        }
        aline.update(values)

    def _fetch_scores(self, variant):
        scores = None
        if variant.variant_type == VariantType.substitution:
            scores = self.score_file.fetch_scores(
                variant.chromosome, variant.position, variant.position
            )
        elif variant.variant_type in set(
            [VariantType.insertion, VariantType.deletion, VariantType.comp]
        ):
            scores = self.score_file.fetch_scores(
                variant.chromosome,
                variant.position,
                variant.position + len(variant.reference),
            )
        elif VariantType.is_cnv(variant.variant_type):
            scores = self.score_file.fetch_scores(
                variant.chromosome,
                variant.position,
                variant.end_position,
            )
        else:
            print(
                f"Unexpected variant type in score annotation: "
                f"{variant}, {variant.variant_type}",
                file=sys.stderr,
            )
        return scores


class PositionScoreAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, config, genomes_db):
        super(PositionScoreAnnotator, self).__init__(config, genomes_db)

    def do_annotate(self, aline, variant):
        if variant is None:
            self._scores_not_found(aline)
            return

        scores = self._fetch_scores(variant)

        if not scores:
            self._scores_not_found(aline)
            return

        scores_df = self.score_file.scores_to_dataframe(scores)
        counts = scores["COUNT"]
        total_count = sum(counts)

        for score_name in self.score_names:
            column_name = getattr(self.config.columns, score_name)
            values = scores_df[score_name]
            assert len(values) > 0
            if len(values) == 1:
                aline[column_name] = values[0]
            elif VariantType.is_cnv(variant.variant_type):
                aline[column_name] = values.max()
            else:
                total_sum = sum(
                    [c * v for (c, v) in zip(counts, values)]
                )
                aline[column_name] = total_sum / total_count


class NPScoreAnnotator(VariantScoreAnnotatorBase):
    def __init__(self, config, genomes_db):
        super(NPScoreAnnotator, self).__init__(config, genomes_db)
        self.ref_name = self.score_file.ref_name
        self.alt_name = self.score_file.alt_name
        self.chr_name = self.score_file.chr_name
        self.pos_begin_name = self.score_file.pos_begin_name

    def _aggregate_substitution(self, variant, scores_df):
        assert self.score_file.ref_name is not None
        assert self.score_file.alt_name is not None
        assert variant.variant_type == VariantType.substitution

        res = {}
        matched = (scores_df[self.ref_name] == variant.reference) & (
            scores_df[self.alt_name] == variant.alternative
        )
        matched_df = scores_df[matched]
        if len(matched_df) == 0:
            self._scores_not_found(res)
        else:
            for score_name in self.score_names:
                column_name = getattr(self.config.columns, score_name)
                res[column_name] = matched_df[score_name].mean()
        return res

    def _aggregate_indel(self, variant, scores_df):
        assert variant.variant_type in set(
            [VariantType.insertion, VariantType.deletion, VariantType.comp]
        )

        aggregate = {sn: "max" for sn in self.score_names}

        aggregate["COUNT"] = "max"
        group_df = scores_df.groupby(
            by=[self.chr_name, self.pos_begin_name]
        ).agg(aggregate)
        count = group_df["COUNT"].sum()
        res = {}
        for score_name in self.score_names:
            column_name = getattr(self.config.columns, score_name)
            total_df = group_df[score_name] * group_df["COUNT"]
            res[column_name] = total_df.sum() / count

        return res

    def _aggregate_cnv(self, variant, scores_df):
        assert VariantType.is_cnv(variant.variant_type)
        res = dict()
        for score_name in self.score_names:
            column_name = getattr(self.config.columns, score_name)
            res[column_name] = scores_df[score_name].max()
        return res

    def do_annotate(self, aline, variant):
        if variant is None:
            self._scores_not_found(aline)
            return

        scores = self._fetch_scores(variant)

        if not scores:
            self._scores_not_found(aline)
            return

        scores_df = self.score_file.scores_to_dataframe(scores)

        if variant.variant_type == VariantType.substitution:
            aline.update(self._aggregate_substitution(variant, scores_df))
        elif variant.variant_type in set(
            [VariantType.insertion, VariantType.deletion, VariantType.comp]
        ):
            aline.update(self._aggregate_indel(variant, scores_df))
        elif VariantType.is_cnv(variant.variant_type):
            aline.update(self._aggregate_cnv(variant, scores_df))
        else:
            print(
                "Unexpected variant type: {}, {}".format(
                    variant, variant.variant_type
                ),
                file=sys.stderr,
            )
            self._scores_not_found(aline)


class PositionMultiScoreAnnotator(CompositeVariantAnnotator):
    def __init__(self, config, genomes_db):
        super(PositionMultiScoreAnnotator, self).__init__(config, genomes_db)
        assert self.config.options.scores_directory is not None

        for score_name in self.config.columns._fields:
            annotator = self._build_annotator_for(score_name)
            self.add_annotator(annotator)

    def _get_score_file(self, score_name):
        dirname = "{}/{}".format(
            os.path.abspath(self.config.options.scores_directory), score_name
        )
        globname = "{}/{}*gz".format(dirname, score_name)
        filenames = glob.glob(globname)
        assert len(filenames) == 1
        return filenames[0]

    def _build_annotator_for(self, score_name):
        assert os.path.exists(
            self.config.options.scores_directory
        ), self.config.options.scores_directory

        score_filename = self._get_score_file(score_name)

        options = GPFConfigParser.modify_tuple(
            self.config.options, {"scores_file": score_filename}
        )
        columns = {score_name: getattr(self.config.columns, score_name)}

        variant_config = AnnotationConfigParser.parse_section(
            GPFConfigParser._dict_to_namedtuple(
                {
                    "options": options,
                    "columns": columns,
                    "annotator": "score_annotator.VariantScoreAnnotator",
                    "virtual_columns": [],
                }
            )
        )

        annotator = PositionScoreAnnotator(variant_config, self.genomes_db)
        return annotator
