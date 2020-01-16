from collections import OrderedDict


def _section_tree(config):
    section_tree = OrderedDict()
    for option in config.keys():
        option_leaf = section_tree
        option_tokens = option.split('.')
        for token in option_tokens[0:-1]:
            option_leaf = option_leaf.setdefault(token, OrderedDict())
        option_leaf[option_tokens[-1]] = config.get(option)
    return section_tree


def parser_to_dict(config):
    config = OrderedDict(
        (section, OrderedDict(config.items(section)))
        for section in config.sections()
    )

    sections_result = OrderedDict()
    for section in config.keys():
        sections_result[section] = _section_tree(config[section])

    result = _section_tree(sections_result)

    return result


def flatten_dict(input_dict, sep='.'):
    res = {}
    for key, value in input_dict.items():
        if type(value) is dict and len(value):
            for key_2, value_2 in flatten_dict(value).items():
                res[key + sep + key_2] = value_2
        else:
            res[key] = value
    return res


IMPALA_RESERVED_WORDS = (
    'abs', 'acos', 'add', 'aggregate', 'all',
    'allocate', 'alter', 'analytic', 'and', 'anti',
    'any', 'api_version', 'are', 'array', 'array_agg',
    'array_max_cardinality', 'as', 'asc', 'asensitive', 'asin',
    'asymmetric', 'at', 'atan', 'atomic', 'authorization',
    'avg', 'avro', 'backup', 'begin', 'begin_frame',
    'begin_partition', 'between', 'bigint', 'binary', 'blob',
    'block_size', 'boolean', 'both', 'break', 'browse',
    'bulk', 'by', 'cache', 'cached', 'call',
    'called', 'cardinality', 'cascade', 'cascaded', 'case',
    'cast', 'ceil', 'ceiling', 'change', 'char',
    'char_length', 'character', 'character_length', 'check', 'checkpoint',
    'class', 'classifier', 'clob', 'close', 'close_fn',
    'clustered', 'coalesce', 'collate', 'collect', 'column',
    'columns', 'comment', 'commit', 'compression', 'compute',
    'condition', 'conf', 'connect', 'constraint', 'contains',
    'continue', 'convert', 'copy', 'corr', 'corresponding',
    'cos', 'cosh', 'count', 'covar_pop', 'covar_samp',
    'create', 'cross', 'cube', 'cume_dist', 'current',
    'current_catalog', 'current_date', 'current_default_transform_group',
    'current_path', 'current_role', 'current_row', 'current_schema',
    'current_time', 'current_timestamp', 'current_transform_group_for_type',
    'current_user', 'cursor', 'cycle', 'data', 'database',
    'databases', 'date', 'datetime', 'day', 'dayofweek',
    'dbcc', 'deallocate', 'dec', 'decfloat', 'decimal',
    'declare', 'default', 'define', 'delete', 'delimited',
    'dense_rank', 'deny', 'deref', 'desc', 'describe',
    'deterministic', 'disconnect', 'disk', 'distinct', 'distributed',
    'div', 'double', 'drop', 'dump', 'dynamic',
    'each', 'element', 'else', 'empty', 'encoding',
    'end', 'end', 'end_frame', 'end_partition', 'equals',
    'errlvl', 'escape', 'escaped', 'every', 'except',
    'exchange', 'exec', 'execute', 'exists', 'exit',
    'exp', 'explain', 'extended', 'external', 'extract',
    'false', 'fetch', 'fields', 'file', 'filefactor',
    'fileformat', 'files', 'filter', 'finalize_fn', 'first',
    'first_value', 'float', 'floor', 'following', 'for',
    'foreign', 'format', 'formatted', 'frame_row', 'free',
    'freetext', 'from', 'full', 'function', 'functions',
    'fusion', 'get', 'global', 'goto', 'grant',
    'group', 'grouping', 'groups', 'hash', 'having',
    'hold', 'holdlock', 'hour', 'identity', 'if',
    'ignore', 'ilike', 'import', 'in', 'incremental',
    'index', 'indicator', 'init_fn', 'initial', 'inner',
    'inout', 'inpath', 'insensitive', 'insert', 'int',
    'integer', 'intermediate', 'intersect', 'intersection', 'interval',
    'into', 'invalidate', 'iregexp', 'is', 'join',
    'json_array', 'json_arrayagg', 'json_exists', 'json_object',
    'json_objectagg', 'json_query', 'json_table', 'json_table_primitive',
    'json_value', 'key',
    'kill', 'kudu', 'lag', 'language', 'large',
    'last', 'last_value', 'lateral', 'lead', 'leading',
    'left', 'less', 'like', 'like_regex', 'limit',
    'lineno', 'lines', 'listagg', 'ln', 'load',
    'local', 'localtime', 'localtimestamp', 'location', 'log',
    'log10', 'lower', 'macro', 'map', 'match',
    'match_number', 'match_recognize', 'matches', 'max', 'member',
    'merge', 'merge_fn', 'metadata', 'method', 'min',
    'minute', 'mod', 'modifies', 'module', 'month',
    'more', 'multiset', 'national', 'natural', 'nchar',
    'nclob', 'new', 'no', 'nocheck', 'nonclustered',
    'none', 'normalize', 'not', 'nth_value', 'ntile',
    'null', 'nullif', 'nulls', 'numeric', 'occurrences_regex',
    'octet_length', 'of', 'off', 'offset', 'offsets',
    'old', 'omit', 'on', 'one', 'only',
    'open', 'option', 'or', 'order', 'out',
    'outer', 'over', 'overlaps', 'overlay', 'overwrite',
    'parameter', 'parquet', 'parquetfile', 'partialscan', 'partition',
    'partitioned', 'partitions', 'pattern', 'per', 'percent',
    'percent_rank', 'percentile_cont', 'percentile_disc', 'period', 'pivot',
    'plan', 'portion', 'position', 'position_regex', 'power',
    'precedes', 'preceding', 'precision', 'prepare', 'prepare_fn',
    'preserve', 'primary', 'print', 'proc', 'procedure',
    'produced', 'ptf', 'public', 'purge', 'raiseerror',
    'range', 'rank', 'rcfile', 'read', 'reads',
    'readtext', 'real', 'reconfigure', 'recover', 'recursive',
    'reduce', 'ref', 'references', 'referencing', 'refresh',
    'regexp', 'regr_avgx', 'regr_avgy', 'regr_count', 'regr_intercept',
    'regr_r2', 'regr_slope', 'regr_sxx', 'regr_sxy', 'regr_syy',
    'release', 'rename', 'repeatable', 'replace', 'replication',
    'restore', 'restrict', 'result', 'return', 'returns',
    'revert', 'revoke', 'right', 'rlike', 'role',
    'roles', 'rollback', 'rollup', 'row', 'row_number',
    'rowcount', 'rows', 'rule', 'running', 'save',
    'savepoint', 'schema', 'schemas', 'scope', 'scroll',
    'search', 'second', 'securityaudit', 'seek', 'select',
    'semi', 'sensitive', 'sequencefile', 'serdeproperties', 'serialize_fn',
    'session_user', 'set', 'setuser', 'show', 'shutdown',
    'similar', 'sin', 'sinh', 'skip', 'smallint',
    'some', 'sort', 'specific', 'specifictype', 'sql',
    'sqlexception', 'sqlstate', 'sqlwarning', 'sqrt', 'start',
    'static', 'statistics', 'stats', 'stddev_pop', 'stddev_samp',
    'stored', 'straight_join', 'string', 'struct', 'submultiset',
    'subset', 'substring', 'substring_regex', 'succeeds', 'sum',
    'symbol', 'symmetric', 'system', 'system_time', 'system_user',
    'table', 'tables', 'tablesample', 'tan', 'tanh',
    'tblproperties', 'terminated', 'textfile', 'textsize', 'then',
    'time', 'timestamp', 'timezone_hour', 'timezone_minute', 'tinyint',
    'to', 'top', 'trailing', 'tran', 'transform',
    'translate', 'translate_regex', 'translation', 'treat', 'trigger',
    'trim', 'trim_array', 'true', 'truncate', 'try_convert',
    'uescape', 'unbounded', 'uncached', 'union', 'unique',
    'uniquejoin', 'unknown', 'unnest', 'unpivot', 'update',
    'update_fn', 'updatetext', 'upper', 'upsert', 'use',
    'user', 'using', 'utc_tmestamp', 'value', 'value_of',
    'values', 'var_pop', 'var_samp', 'varbinary', 'varchar',
    'varying', 'versioning', 'view', 'views', 'waitfor',
    'when', 'whenever', 'where', 'while', 'width_bucket',
    'window', 'with', 'within', 'without', 'writetext', 'year',
)
