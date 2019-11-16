import os
import numpy as np
import pandas as pd


class VariantsLoader:

    def __init__(self):
        pass

    def full_variants_iterator(self):
        raise NotImplementedError()


class RawVariantsLoader:

    SEP1 = '!'
    SEP2 = '|'
    SEP3 = ':'

    @staticmethod
    def convert_array_of_strings(token):
        if not token:
            return None
        token = token.strip()
        words = [w.strip() for w in token.split(RawVariantsLoader.SEP1)]
        return words

    @staticmethod
    def convert_string(token):
        if not token:
            return None
        return token

    @staticmethod
    def _build_annotation_filename(filename):
        return "{}-eff.txt".format(os.path.splitext(filename)[0])

    @staticmethod
    def has_annotation_file(annotation_filename):
        return os.path.exists(annotation_filename)

    @classmethod
    def load_annotation_file(cls, filename, sep='\t'):
        assert os.path.exists(filename)
        with open(filename, 'r') as infile:
            annot_df = pd.read_csv(
                infile, sep=sep, index_col=False,
                dtype={
                    'chrom': str,
                    'position': np.int32,
                },
                converters={
                    'cshl_variant': cls.convert_string,
                    'effect_gene_genes':
                    cls.convert_array_of_strings,
                    'effect_gene_types':
                    cls.convert_array_of_strings,
                    'effect_details_transcript_ids':
                    cls.convert_array_of_strings,
                    'effect_details_details':
                    cls.convert_array_of_strings,
                },
                encoding="utf-8"
            )
        for col in ['alternative', 'effect_type']:
            annot_df[col] = annot_df[col].astype(object). \
                where(pd.notnull(annot_df[col]), None)
        return annot_df

    @staticmethod
    def save_annotation_file(annot_df, filename, sep="\t"):
        def convert_array_of_strings_to_string(a):
            if not a:
                return None
            return RawVariantsLoader.SEP1.join(a)

        vars_df = annot_df.copy()
        vars_df['effect_gene_genes'] = vars_df['effect_gene_genes'].\
            apply(convert_array_of_strings_to_string)
        vars_df['effect_gene_types'] = vars_df['effect_gene_types'].\
            apply(convert_array_of_strings_to_string)
        vars_df['effect_details_transcript_ids'] = \
            vars_df['effect_details_transcript_ids'].\
            apply(convert_array_of_strings_to_string)
        vars_df['effect_details_details'] = \
            vars_df['effect_details_details'].\
            apply(convert_array_of_strings_to_string)
        vars_df.to_csv(
            filename,
            index=False,
            sep=sep
        )
