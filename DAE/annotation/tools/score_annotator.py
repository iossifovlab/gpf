import sys
import os
import glob
import numpy as np

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

        assert len(self.config.native_columns) == 1
        self.score_name = self.config.native_columns[0]

    def _init_score_file(self):
        if not self.config.options.scores_file:
            print("You should provide a score file location.", file=sys.stderr)
            sys.exit(1)

        if self.config.options.direct:
            self.score_file = DirectAccess(
                self.config.options.scores_file,
                self.config.options.scores_config_file)
        else:
            self.score_file = IterativeAccess(
                self.config.options.scores_file,
                self.config.options.scores_config_file,
                self.config.options.region)

    def line_annotation(self, aline, variant=None):
        assert variant is not None
        assert isinstance(aline, Line)

        scores = self.score_file.fetch_score_lines(
            variant.chromosome,
            variant.position,
            variant.position
        )
        if len(scores) == 0:
            value = self.score_file.config.noScoreValue
        else:
            value = np.average(
                [float(ln.columns[self.score_name]) for ln in scores])
        aline.columns[self.config.columns_config[self.score_name]] = value


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
        print(score_filename)
        options = Box(
            self.config.options.to_dict(),
            default_box=True, default_box_attr=None)
        options.scores_file = score_filename
        columns_config = {
            score_name: self.config.columns_config[score_name]
        }
        print(options)

        variant_config = VariantAnnotatorConfig(
            name="{}.{}".format(self.config.name, score_name),
            annotator_name="score_annotator.VariantScoreAnnotator",
            options=options,
            columns_config=columns_config,
            virtuals=[]
        )

        annotator = VariantScoreAnnotator(variant_config)
        return annotator

