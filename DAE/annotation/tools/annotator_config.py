from importlib import import_module


class AnnotatorConfig(object):

    def __init__(
            self, name, annotator_name, options,
            columns_config, virtuals):
        self.name = name
        self.annotator_name = annotator_name
        self.options = options
        self.columns_config = columns_config

        self.native_columns = list(columns_config.keys())
        self.virtual_columns = list(virtuals)
        assert all([
            c in self.columns_config.values()
            for c in self.virtual_columns])

        self.output_columns = [
            c for c in self.columns_config.values()
            if c not in self.virtual_columns
        ]

    @staticmethod
    def _split_class_name(class_fullname):
        splitted = class_fullname.split('.')
        module_path = splitted[:-1]
        assert len(module_path) >= 1
        if len(module_path) == 1:
            res = ["annotation", "tools"]
            res.extend(module_path)
            module_path = res

        module_name = '.'.join(module_path)
        class_name = splitted[-1]

        return module_name, class_name

    @staticmethod
    def _name_to_class(class_fullname):
        module_name, class_name = \
            AnnotatorConfig._split_class_name(class_fullname)
        module = import_module(module_name)
        clazz = getattr(module, class_name)
        return clazz

    @staticmethod
    def instantiate(section_config):
        clazz = AnnotatorConfig._name_to_class(section_config.annotator_name)
        assert clazz is not None
        return clazz(section_config)

    @staticmethod
    def cli_options():
        return [
            ('infile', {
                'nargs': '?',
                'action': 'store',
                'default': '-',
                'help': 'path to input file; defaults to stdin'
            }),
            ('outfile', {
                'nargs': '?',
                'action': 'store',
                'default': '-',
                'help': 'path to output file; defaults to stdout'
            }),
            ('--mode', {
                'help': 'annotator mode; available modes are `overwrite`'
                '`replace` and `append`',
                'default': 'overwrite',
                'action': 'store'
            }),
            ('--direct', {
                'help': 'use direct access to score files',
                'default': False,
                'action': 'store_true'
            }),
            ('--region', {
                'help': 'work only in the specified region',
                'default': None,
                'action': 'store'
            }),
            ('--read-parquet', {
                'help': 'read from a parquet file',
                'action': 'store_true'
            }),
            ('--write-parquet', {
                'help': 'write to a parquet file',
                'action': 'store_true'
            })
        ]


class VariantAnnotatorConfig(AnnotatorConfig):

    def __init__(
            self, name, annotator_name, options,
            columns_config, virtuals):
        super(VariantAnnotatorConfig, self).__init__(
            name, annotator_name, options,
            columns_config, virtuals
        )
        self._setup_defaults()

    def _setup_defaults(self):
        if self.options.vcf:
            if self.options.c is None:
                self.options.c = 'CHROM'
            if self.options.p is None:
                self.options.p = 'POS'
            if self.options.r is None:
                self.options.r = 'REF'
            if self.options.a is None:
                self.options.a = 'ALT'
        else:
            if self.options.x is None and self.options.c is None:
                self.options.x = 'location'
            if self.options.v is None:
                self.options.v = 'variant'
        if self.options.Graw is None:
            from DAE import genomesDB
            self.genome_file = genomesDB.get_genome_file()
        else:
            self.genome_file = self.options.Graw
        assert self.genome_file is not None

    @staticmethod
    def cli_options():
        options = AnnotatorConfig.cli_options()

        options.extend([
            ('-c', {
                'help': 'chromosome column number/name'
            }),
            ('-p', {
                'help': 'position column number/name'
            }),
            ('-x', {
                'help': 'location (chr:position) column number/name'
            }),
            ('-v', {
                'help': 'variant (CSHL format) column number/name'
            }),
            ('-r', {
                'help': 'reference column number/name'
            }),
            ('-a', {
                'help': 'alternative column number/name'
            }),
            ('--vcf', {
                'help': 'if the variant description uses VCF convention',
                'default': False,
                'action': 'store_true'
            }),
            ('--Graw', {
                'help': 'genome file location'
            }),
        ])
        return options


class LineConfig(object):

    def __init__(self, source_header):
        self.source_header = [
            col.strip('#') for col in source_header
        ]

    def build(self, source_line):
        return dict(zip(self.source_header, source_line))

