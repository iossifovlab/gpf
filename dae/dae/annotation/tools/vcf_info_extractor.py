import re
from dae.annotation.tools.annotator_base import AnnotatorBase


class VCFInfoExtractor(AnnotatorBase):

    def __init__(self, config):
        super(VCFInfoExtractor, self).__init__(config)

    def collect_annotator_schema(self, schema):
        for info_key, output_col in self.config.columns_config.items():
            schema.create_column(output_col, 'str')

    def line_annotation(self, annotation_line):
        info = annotation_line['INFO']
        for info_key, output_col in self.config.columns_config.items():
            annotation_line[output_col] = None
            match = re.search(r'\b({})\b'.format(info_key), info)
            if match is None:
                continue
            val_beg_index = match.start() + len(info_key)
            val_end_index = info.find(';', val_beg_index)
            if val_end_index == -1:
                val_end_index = len(info)
            annotation_line[output_col] = info[val_beg_index+1:val_end_index]
