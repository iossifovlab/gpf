import sys
import os
import glob
from box import Box

from annotation.tools.annotator_base import VariantAnnotatorBase, \
    CompositeVariantAnnotator
from annotation.tools.annotator_config import Line, VariantAnnotatorConfig

from annotation.tools.annotate_score_base import DirectAccess, \
    IterativeAccess


class VariantScoreAnnotator(VariantAnnotatorBase):

    def __init__(self, config):
        super(VariantScoreAnnotator, self).__init__(config)

        self._init_score_file()

        if self.config.options.search_columns is not None and \
                self.config.options.search_columns != '':
            self.search_columns = self.config.options.search_columns.split(',')
        else:
            self.search_columns = []

        assert len(self.config.native_columns) >= 1
        self.score_names = self.config.native_columns

    def _init_score_file(self):
        if not self.config.options.scores_file:
            print("You should provide a score file location.", file=sys.stderr)
            sys.exit(1)

        scores_filename = os.path.abspath(self.config.options.scores_file)
        assert os.path.exists(scores_filename), scores_filename

        if self.config.options.direct:
            self.score_file = DirectAccess(
                scores_filename,
                self.config.options.scores_config_file)
        else:
            self.score_file = IterativeAccess(
                scores_filename,
                self.config.options.scores_config_file,
                self.config.options.region)

    def _scores_not_found(self, aline):
        values = {
            self.config.columns_config[score_name]:
            self.score_file.config.noScoreValue
            for score_name in self.score_names}
        aline.columns.update(values)

    def _scores_no_search(self, aline, scores_df):
        for score_name in self.score_names:
            column_name = self.config.columns_config[score_name]
            aline.columns[column_name] = scores_df[score_name].mean()

    def _scores_with_search(self, aline, scores_df):
        assert len(self.search_columns) == len(self.score_file.search_columns)

        match_expr = None
        for col_index in range(len(self.search_columns)):
            line_column = self.search_columns[col_index]
            score_column = self.score_file.search_columns[col_index]
            expr = scores_df[score_column] == aline.columns[line_column]
            if match_expr is None:
                match_expr = expr
            else:
                match_expr = match_expr & expr
        matched_df = scores_df[match_expr]
        if len(matched_df) == 0:
            self._scores_not_found(aline)
        else:
            self._scores_no_search(aline, matched_df)

    def line_annotation(self, aline, variant=None):
        assert variant is not None
        assert isinstance(aline, Line)
        chrom = aline.columns[self.config.options.c]
        pos = aline.columns[self.config.options.p]

        scores_df = self.score_file.fetch_score_lines(
            chrom,
            pos,
            pos
        )

        if len(scores_df) == 0:
            self._scores_not_found(aline)
        elif not self.search_columns or not self.score_file.search_columns:
            self._scores_no_search(aline, scores_df)
        else:
            self._scores_with_search(aline, scores_df)


class VariantMultiScoreAnnotator(CompositeVariantAnnotator):

    def __init__(self, config):
        super(VariantMultiScoreAnnotator, self).__init__(config)
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
        assert os.path.exists(self.config.options.scores_directory)

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

        annotator = VariantScoreAnnotator(variant_config)
        return annotator

