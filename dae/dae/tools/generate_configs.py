import argparse
import os
import sys
import glob

from box import Box
from collections import OrderedDict

from dae.annotation.tools.annotator_config import AnnotationConfigParser, \
    VariantAnnotatorConfig

from dae.configuration.configuration import DAEConfigParser
from dae.configuration.dae_config_parser import CaseSensitiveConfigParser
from dae.configuration.utils import parser_to_dict, flatten_dict


class PipelineConfigWrapper(VariantAnnotatorConfig):

    non_freq_scores = []
    freq_scores = []
    score_groups = {'ungrouped': []}
    score_genotype_browser_names = {}

    def __init__(self, name, annotator_name, options,
                 columns_config, virtuals):
        super(PipelineConfigWrapper, self).__init__(
            name, annotator_name, options,
            columns_config, virtuals
        )

    @classmethod
    def build(cls, config_file):
        options = Box({}, default_box=True, default_box_attr=None)

        dae_config = DAEConfigParser.read_and_parse_file_configuration()
        defaults = dae_config.annotation_defaults

        configuration = \
            AnnotationConfigParser.read_and_parse_file_configuration(
                config_file, dae_config.dae_data_dir, defaults
            )

        result = PipelineConfigWrapper(
            name="pipeline",
            annotator_name="annotation_pipeline.Pipeline",
            options=options,
            columns_config=OrderedDict(),
            virtuals=[]
        )
        result.pipeline_sections = []

        for section_name, section_config in configuration.items():
            section_config = cls.parse_section(
                section_name, section_config, options)
            result.pipeline_sections.append(section_config)

        result._collect_score_names()
        result._collect_score_groups()
        return result

    @property
    def all_scores(self):
        return self.non_freq_scores + self.freq_scores

    @staticmethod
    def get_string_identifier(string):
        res = ""
        for char in string:
            if (char >= 'A' and char <= 'Z') or \
               (char >= 'a' and char <= 'z') or \
               (char == '_'):
                res += char
            else:
                break
        return res

    @staticmethod
    def collect_similar(term, input_list):
        return [item for item in input_list if term in item]

    def _collect_score_names(self):
        for section in self.pipeline_sections:
            if 'frequency_annotator' in section.annotator_name:
                self.freq_scores += section.output_columns
            elif 'score_annotator' in section.annotator_name:
                self.non_freq_scores += section.output_columns

    def _collect_score_groups(self):
        assert self.freq_scores or self.non_freq_scores
        if self.freq_scores:
            self.score_groups['Frequency'] = self.freq_scores
        if self.non_freq_scores:
            for score_name in self.non_freq_scores:
                identifier = \
                    PipelineConfigWrapper.get_string_identifier(score_name)
                group = \
                    PipelineConfigWrapper.collect_similar(identifier,
                                                          self.non_freq_scores)
                if len(group) > 1:
                    if identifier not in self.score_groups:
                        self.score_groups[identifier] = group
                else:
                    self.score_groups['ungrouped'].append(score_name)

    def score_dirs(self):
        for section in self.pipeline_sections:
            if section.annotator_name == \
                    'score_annotator.PositionMultiScoreAnnotator':
                for score in section.output_columns:
                    yield section.options.scores_directory + \
                          '/' + score
            elif 'score_annotator' in section.annotator_name or \
                 'frequency_annotator' in section.annotator_name:
                yield os.path.split(section.options.scores_file)[0]

    def set_genotype_browser_names(self, names_list):
        for pair in names_list:
            pair = pair.split(':')
            self.score_genotype_browser_names[pair[0]] = pair[1]

    def browser_name(self, score):
        return self.score_genotype_browser_names.get(score, score)


class ConfigGenerator(object):

    template_formatted_score = '{score}:{name}:%%.3f'

    def __init__(self, config_path, **kwargs):
        config_abspath = os.path.abspath(config_path)
        assert os.path.exists(config_abspath)
        self.pipeline_config = PipelineConfigWrapper.build(config_abspath)

    @staticmethod
    def group_and_format(items, width=5, sep=',', tabs=1):
        grouped = []
        while True:
            if len(items) > width:
                group = items[:width]
                grouped.append(sep.join(group))
                items = items[width:]
            else:
                grouped.append(sep.join(items))
                break
        group_sep = sep
        if tabs:
            group_sep += '\n' + ('\t' * tabs)
        return group_sep.join(grouped)

    def generate_default_config(self):
        template_name = 'template_defaultConfiguration.conf'

        assert self.pipeline_config

        generated_config_dict = {'genotypeBrowser': {'genotype': {}}}

        # write genotypeBrowser scores
        for score in self.pipeline_config.all_scores:
            option = generated_config_dict['genotypeBrowser']['genotype'].\
                     setdefault(score, {})
            option['name'] = self.pipeline_config.browser_name(score)
            option['source'] = score

        # write genotypeBrowser score groups
        score_group_counter = 0
        generated_score_groups = []
        for group in self.pipeline_config.score_groups:
            if group == 'ungrouped':
                continue
            score_group_counter += 1
            option = generated_config_dict['genotypeBrowser']['genotype'].\
                setdefault('scores{}'.format(score_group_counter), {})
            option['name'] = group

            slots = []
            for score_name in self.pipeline_config.score_groups[group]:
                browser_name = self.pipeline_config.browser_name(score_name)
                slots.append(
                    self.template_formatted_score.format(score=score_name,
                                                         name=browser_name))

            option['slots'] = \
                ConfigGenerator.group_and_format(slots, width=1)
            generated_score_groups.append(
                'scores{}'.format(score_group_counter))

        # write genomic scores options
        generated_config_dict['GENOMIC_SCORES_COLUMNS'] = \
            ConfigGenerator.group_and_format(self.pipeline_config.all_scores)
        generated_config_dict['GENOMIC_SCORES_PREVIEW'] = \
            ConfigGenerator.group_and_format(generated_score_groups)
        generated_config_dict['GENOMIC_SCORES_DOWNLOAD'] = \
            ConfigGenerator.group_and_format(self.pipeline_config.all_scores)

        generated_config = CaseSensitiveConfigParser(
            allow_no_value=True, interpolation=None)
        with open(template_name, 'r', encoding='utf8') as template:
            generated_config.read_file(template)

        generated_config['genomicScores'] = {}
        generated_config['genomicScores'].update(
                flatten_dict(generated_config_dict))
        generated_config.write(sys.stdout)

    def generate_genomic_scores(self):
        default_dir = '%(wd)s/genomicScores'

        generated_config = CaseSensitiveConfigParser(
            allow_no_value=True, interpolation=None)

        generated_config.add_section('genomicScores')
        generated_config['genomicScores']['dir'] = default_dir

        for score_dir in self.pipeline_config.score_dirs():
            for conf in ConfigGenerator.get_score_config(score_dir):
                if 'histograms' in conf:
                    hist_dict = parser_to_dict(conf)['histograms']
                    for score_col in hist_dict:
                        if score_col == 'default':
                            continue
                        sec_name = 'genomicScores.{}'.format(score_col)
                        sec = OrderedDict()
                        if 'default' in hist_dict:
                            sec.update(hist_dict['default'])
                        sec.update(hist_dict[score_col])
                        sec['file'] = os.path.join(default_dir, sec['file'])
                        generated_config[sec_name] = sec

        generated_config.write(sys.stdout)

    @staticmethod
    def get_score_config(score_dir):
        for conf_file_path in glob.glob(os.path.join(score_dir, '*.conf')):
            conf = CaseSensitiveConfigParser()
            with open(conf_file_path, 'r') as conf_file:
                conf.read_file(conf_file)
            yield conf


if __name__ == '__main__':
    parser = \
        argparse.ArgumentParser(description='Generate various configurations '
                                            'from an annotation config.')
    parser.add_argument('config', help='annotation config to use')
    parser.add_argument('--generate', help='type of config to generate',
                        action='append')
    parser.add_argument('--use-name',
                        help=('use a specific name in the genotype browser\n'
                              'for the given score\n'),
                        metavar='ANNOTATION_NAME:SPECIAL_NAME',
                        action='append')
    args = parser.parse_args()

    config_gen = ConfigGenerator(args.config)

    if args.use_name:
        config_gen.pipeline_config.set_genotype_browser_names(args.use_name)

    for conf_type in args.generate:
        if conf_type == 'defaultConfiguration':
            config_gen.generate_default_config()
        elif conf_type == 'genomicScores':
            config_gen.generate_genomic_scores()
        else:
            print('Unrecognized config type {} to generate!'.format(conf_type))
