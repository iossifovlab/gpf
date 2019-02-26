import argparse
import os.path
from annotation.annotation_pipeline import PipelineConfig
from box import Box
from collections import OrderedDict
import configparser

from configurable_entities.configuration import DAEConfig
from common.config import flatten_dict
import sys


class PipelineConfigWrapper(PipelineConfig):

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

    @staticmethod
    def build(config_file):
        options = Box({}, default_box=True, default_box_attr=None)

        dae_config = DAEConfig()
        defaults = dae_config.annotation_defaults

        configuration = PipelineConfig._parse_pipeline_config(
            config_file, defaults
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
            section_config = result._parse_config_section(
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
                ConfigGenerator.group_and_format(slots, width=2)
            generated_score_groups.append(
                'scores{}'.format(score_group_counter))

        # write genomic scores options
        generated_config_dict['GENOMIC_SCORES_COLUMNS'] = \
            ConfigGenerator.group_and_format(generated_score_groups +
                                             self.pipeline_config.all_scores)
        generated_config_dict['GENOMIC_SCORES_PREVIEW'] = \
            ConfigGenerator.group_and_format(generated_score_groups)
        generated_config_dict['GENOMIC_SCORES_DOWNLOAD'] = \
            ConfigGenerator.group_and_format(self.pipeline_config.all_scores)

        generated_config = \
            configparser.ConfigParser(allow_no_value=True,
                                      interpolation=None)
        generated_config.optionxform = str
        with open(template_name, 'r', encoding='utf8') as template:
            generated_config.read_file(template)

        generated_config['dataset'].update(
                flatten_dict(generated_config_dict))
        generated_config.write(sys.stdout)

    def generate_genomic_scores(self):
        default_dir = '%(wd)s/genomicScores'

        generated_config = \
            configparser.ConfigParser(allow_no_value=True,
                                      interpolation=None)
        generated_config.optionxform = str

        generated_config.add_section('genomicScores')
        generated_config['genomicScores']['dir'] = default_dir

        def write_section(config, score, xscale):
            sec = config['genomicScores.{}'.format(score)]
            sec['file'] = (config['genomicScores']['dir']
                           + '/'
                           + score)
            sec['desc'] = self.pipeline_config.browser_name(score)
            sec['bins'] = '101'
            sec['help_file'] = sec['file'] + '.md'
            sec['yscale'] = 'log'
            sec['xscale'] = xscale

        for score in self.pipeline_config.freq_scores:
            generated_config.add_section('genomicScores.{}'.format(score))
            write_section(generated_config, score, 'log')
        for score in self.pipeline_config.non_freq_scores:
            generated_config.add_section('genomicScores.{}'.format(score))
            write_section(generated_config, score, 'linear')

        generated_config.write(sys.stdout)


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
