from dae.annotation.tools.annotator_base import AnnotatorBase


class CleanupAnnotator(AnnotatorBase):

    def __init__(self, config, genomes_db):
        super(CleanupAnnotator, self).__init__(config, genomes_db)
        # TODO Fix this - should be split in the configuration schema!
        self.cleanup_columns = self.config.columns.cleanup.split(',')
        self.cleanup_columns = [
            col.strip() for col in self.cleanup_columns
        ]

    def collect_annotator_schema(self, schema):
        for column in self.cleanup_columns:
            schema.remove_column(column)

    def line_annotation(self, annotation_line):
        for column in self.cleanup_columns:
            if column in annotation_line:
                del(annotation_line[column])
