from __future__ import print_function

import sys
import os
import glob

from box import Box

from variants.attributes import VariantType

from annotation.tools.annotator_base import VariantAnnotatorBase, \
    CompositeVariantAnnotator
from annotation.tools.annotator_config import VariantAnnotatorConfig

from annotation.tools.score_file_io import DirectAccess, \
    IterativeAccess


class VariantScoreAnnotatorBase(VariantAnnotatorBase):

    def __init__(self, config):
        super(VariantScoreAnnotatorBase, self).__init__(config)

        self._init_score_file()

        assert len(self.config.native_columns) >= 1
        self.score_names = self.config.native_columns

        assert all([
            sn in self.score_file.score_names for sn in self.score_names]), \
            (self.score_names, self.score_file.score_names,
             self.score_file.filename)

    def _init_score_file(self):
        assert self.config.options.scores_file, \
            [self.config.name, self.config.annotator_name]

        scores_filename = os.path.abspath(self.config.options.scores_file)
        assert os.path.exists(scores_filename), scores_filename

        if self.config.options.direct:
            self.score_file = DirectAccess(
                self.config.options,
                scores_filename,
                self.config.options.scores_config_file)
        else:
            self.score_file = IterativeAccess(
                self.config.options,
                scores_filename,
                self.config.options.scores_config_file)
        self.score_file._setup()

        self.no_score_value = self.score_file.config.noScoreValue
        if self.no_score_value.lower() in set(['na', 'none']):
            self.no_score_value = None

    def collect_annotator_schema(self, schema):
        super(VariantScoreAnnotatorBase, self).collect_annotator_schema(schema)
        for native, output in self.config.columns_config.items():
            type_name = self.score_file.schema.columns[native].type_name
            schema.create_column(output, type_name)
            # schema.columns[output] = self.score_file.schema.columns[native]

    def _scores_not_found(self, aline):
        values = {
            self.config.columns_config[score_name]:
            self.no_score_value
            for score_name in self.score_names}
        aline.update(values)

    def _fetch_scores(self, variant):
        scores = None
        if variant.variant_type == VariantType.substitution:
            scores = self.score_file.fetch_scores(
                variant.chromosome,
                variant.position,
                variant.position
            )
        elif variant.variant_type in set([
                VariantType.insertion, VariantType.deletion,
                VariantType.complex]):

            scores = self.score_file.fetch_scores(
                variant.chromosome,
                variant.position,
                variant.position + len(variant.reference)
            )
        else:
            print("Unexpected variant type: {}, {}".format(
                variant, variant.variant_type
            ), file=sys.stderr)
        return scores


class PositionScoreAnnotator(VariantScoreAnnotatorBase):

    def __init__(self, config):
        super(PositionScoreAnnotator, self).__init__(config)

    def do_annotate(self, aline, variant):
        if variant is None:
            self._scores_not_found(aline)
            return

        scores = self._fetch_scores(variant)

        if not scores:
            self._scores_not_found(aline)
            return

        counts = scores['COUNT']
        total_count = sum(counts)

        for score_name in self.score_names:
            column_name = self.config.columns_config[score_name]
            values = scores[score_name]
            assert len(values) > 0
            if len(values) == 1:
                aline[column_name] = float(values[0])
            else:
                total_sum = sum([
                    c * float(v) for (c, v) in zip(counts, values)])
                aline[column_name] = total_sum / total_count


class NPScoreAnnotator(VariantScoreAnnotatorBase):

    def __init__(self, config):
        super(NPScoreAnnotator, self).__init__(config)
        assert self.score_file.ref_name is not None
        assert self.score_file.alt_name is not None
        self.ref_name = self.score_file.ref_name
        self.alt_name = self.score_file.alt_name
        self.chr_name = self.score_file.chr_name
        self.pos_begin_name = self.score_file.pos_begin_name

    def _aggregate_substitution(self, variant, scores_df):
        assert variant.variant_type == VariantType.substitution

        res = {}
        matched = (scores_df[self.ref_name] == variant.reference) & \
            (scores_df[self.alt_name] == variant.alternative)
        matched_df = scores_df[matched]
        if len(matched_df) == 0:
            self._scores_not_found(res)
        else:
            for score_name in self.score_names:
                column_name = self.config.columns_config[score_name]
                res[column_name] = matched_df[score_name].mean()
        return res

    def _aggregate_indel(self, variant, scores_df):
        assert variant.variant_type in set([
            VariantType.insertion, VariantType.deletion,
            VariantType.complex])

        aggregate = {
            sn: 'max' for sn in self.score_names
        }

        aggregate['COUNT'] = 'max'
        group_df = scores_df.groupby(
            by=[self.chr_name, self.pos_begin_name]).agg(aggregate)
        count = group_df['COUNT'].sum()
        res = {}
        for score_name in self.score_names:
            column_name = self.config.columns_config[score_name]
            total_df = group_df[score_name] * group_df['COUNT']
            res[column_name] = total_df.sum()/count

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

            agg = self._aggregate_substitution(variant, scores_df)
            aline.update(agg)

        elif variant.variant_type in set([
                VariantType.insertion, VariantType.deletion,
                VariantType.complex]):

            agg = self._aggregate_indel(variant, scores_df)
            aline.update(agg)

        else:
            print("Unexpected variant type: {}, {}".format(
                variant, variant.variant_type
            ), file=sys.stderr)
            self._scores_not_found(aline)


class PositionMultiScoreAnnotator(CompositeVariantAnnotator):

    def __init__(self, config):
        super(PositionMultiScoreAnnotator, self).__init__(config)
        assert self.config.options.scores_directory is not None

        for score_name in self.config.columns_config.keys():
            annotator = self._build_annotator_for(score_name)
            self.add_annotator(annotator)

    def _get_score_file(self, score_name):
        dirname = "{}/{}".format(
            os.path.abspath(self.config.options.scores_directory),
            score_name)
        globname = "{}/{}*gz".format(dirname, score_name)
        filenames = glob.glob(globname)
        assert len(filenames) == 1
        return filenames[0]

    def _build_annotator_for(self, score_name):
        assert os.path.exists(self.config.options.scores_directory), \
            self.config.options.scores_directory

        score_filename = self._get_score_file(score_name)
        options = Box(
            self.config.options.to_dict(),
            default_box=True, default_box_attr=None)
        options.scores_file = score_filename
        columns_config = {
            score_name: self.config.columns_config[score_name]
        }

        variant_config = VariantAnnotatorConfig(
            name="{}.{}".format(self.config.name, score_name),
            annotator_name="score_annotator.VariantScoreAnnotator",
            options=options,
            columns_config=columns_config,
            virtuals=[]
        )

        annotator = PositionScoreAnnotator(variant_config)
        return annotator
