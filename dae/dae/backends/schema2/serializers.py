import functools
import operator
import itertools
import logging

import pyarrow as pa

from dae.variants.core import Allele
from dae.variants.attributes import Inheritance, \
    TransmissionType, Sex, Role, Status

logger = logging.getLogger(__name__)


class AlleleParquetSerializer:

    SUMMARY_SEARCHABLE_PROPERTIES_TYPES = {
        "bucket_index": pa.int32(),
        "summary_index": pa.int32(),
        "allele_index": pa.int32(),
        "chromosome": pa.string(),
        "position": pa.int32(),
        "end_position": pa.int32(),
        'effect_gene': pa.list_(pa.field("element", pa.struct([
             pa.field('effect_gene_symbols', pa.string()),
             pa.field('effect_types', pa.string())
        ]))),
        "variant_type": pa.int8(),
        "transmission_type": pa.int8(),
        "reference": pa.string()
    }

    FAMILY_SEARCHABLE_PROPERTIES_TYPES = {
        "bucket_index": pa.int32(),
        "summary_index": pa.int32(),
        "allele_index": pa.int32(),
        "family_index": pa.int32(),
        "family_id": pa.string(),
        "is_denovo": pa.int8(),
        "allele_in_sexes": pa.int8(),
        "allele_in_statuses": pa.int8(),
        "allele_in_roles": pa.int32(),
        "inheritance_in_members": pa.int16(),
        "allele_in_members": pa.list_(pa.string())
    }

    PRODUCT_PROPERTIES_LIST = [
        "effect_gene", "allele_in_members"
    ]

    BASE_SEARCHABLE_PROPERTIES_TYPES = {
        "bucket_index": pa.int32(),
        "chromosome": pa.string(),
        "position": pa.int32(),
        "end_position": pa.int32(),
        'effect_gene': pa.list_(pa.struct([
             pa.field('effect_gene_symbols', pa.string()),
             pa.field('effect_types', pa.string())
        ])),
        "summary_index": pa.int32(),
        "allele_index": pa.int32(),
        "variant_type": pa.int8(),
        "transmission_type": pa.int8(),
        "reference": pa.string(),
        "family_index": pa.int32(),
        "family_id": pa.string(),
        "is_denovo": pa.int8(),
        "allele_in_sexes": pa.int8(),
        "allele_in_statuses": pa.int8(), 
        "allele_in_roles": pa.int32(),
        "inheritance_in_members": pa.int16(),
        "allele_in_members": pa.string(),
    }

    LIST_TO_ROW_PROPERTIES_LISTS = [
        ["effect_gene"],
        ["allele_in_members"]
    ]

    ENUM_PROPERTIES = {
        "variant_type": Allele.Type,
        "transmission_type": TransmissionType,
        "allele_in_sexes": Sex,
        "allele_in_roles": Role,
        "allele_in_statuses": Status,
        "inheritance_in_members": Inheritance,
    }
 

    GENOMIC_SCORES_SCHEMA_CLEAN_UP = [
        "worst_effect",
        "family_bin",
        "rare",
        "genomic_scores_data",
        "frequency_bin",
        "coding",
        "position_bin",
        "chrome_bin",
        "coding2",
        "region_bin",
        "coding_bin",
        "effect_data",
        "genotype_data",
        "inheritance_data",
        "genomic_scores_data",
        "variant_sexes",
        "alternatives_data",
        "chrom",
        "best_state_data",
        "summary_variant_index",
        "effect_type",
        "effect_gene",
        "variant_inheritance",
        "allele_in_member",
        "variant_roles",
        "genetic_model_data",
        "frequency_data",
        "alternative",
        "variant_data",
        "family_variant_index"
    ]

    def __init__(self, variants_schema, extra_attributes=None):
        if variants_schema is None:
            logger.info(
                "serializer called without variants schema")
        else:
            logger.debug(
                f"serializer variants schema {variants_schema.col_names}")

        self._schema_summary = None 
        self._schema_family = None 

        additional_searchable_props = {}
        scores_searchable = {}
        scores_binary = {}
        
        if variants_schema:
            if "af_allele_freq" in variants_schema.col_names:
                additional_searchable_props["af_allele_freq"] = pa.float32()
                additional_searchable_props["af_allele_count"] = pa.int32()
                additional_searchable_props[
                    "af_parents_called_percent"
                ] = pa.float32()
                additional_searchable_props[
                    "af_parents_called_count"
                ] = pa.int32()
            for col_name in variants_schema.col_names:
                if (
                    col_name
                    not in self.BASE_SEARCHABLE_PROPERTIES_TYPES.keys()
                    and col_name not in additional_searchable_props.keys()
                    and col_name not in self.GENOMIC_SCORES_SCHEMA_CLEAN_UP
                    and col_name != "extra_attributes"
                ):
                    scores_binary[col_name] = FloatSerializer
                    scores_searchable[col_name] = pa.float32()

        self.scores_serializers = scores_binary
    
        self.searchable_properties_summary_types = {
            **self.SUMMARY_SEARCHABLE_PROPERTIES_TYPES,
            **additional_searchable_props,
            **scores_searchable
        }

        self.searchable_properties_family_types = {
            **self.FAMILY_SEARCHABLE_PROPERTIES_TYPES 
        }

        self.searchable_properties_types = {
            **self.BASE_SEARCHABLE_PROPERTIES_TYPES,
            **additional_searchable_props,
            **scores_searchable,
        }

        self.extra_attributes = []
        if extra_attributes:
            for attribute_name in extra_attributes:
                self.extra_attributes.append(attribute_name)
    
    @property 
    def schema_summary(self): 
        if self._schema_summary is None:
            fields = [pa.field(spr, pat) for spr, pat in self.SUMMARY_SEARCHABLE_PROPERTIES_TYPES.items()]
            fields.append(pa.field("summary_data", pa.string()))
            self._schema_summary = pa.schema(fields)
        return self._schema_summary 

    @property 
    def schema_family(self):
        if self._schema_family is None:
            fields = []
            for spr in self.FAMILY_SEARCHABLE_PROPERTIES_TYPES:
                field = pa.field(spr, self.FAMILY_SEARCHABLE_PROPERTIES_TYPES[spr])
                fields.append(field)

            fields.append(pa.field("family_data", pa.string()))
            self._schema_family = pa.schema(fields) 
        return self._schema_family 

    @property
    def searchable_properties_summary(self):
        return self.searchable_properties_summary_types.keys()

    @property
    def searchable_properties_family(self):
        return self.searchable_properties_family_types.keys()

    @property
    def searchable_properties(self):
        return self.searchable_properties_types.keys()

    def build_searchable_vectors_summary(self, summary_variant):
        
        vectors = dict()
        for allele in summary_variant.alleles:
            vector = []
            if allele.allele_index not in vectors:
                vectors[allele.allele_index] = []
            for spr in self.searchable_properties_summary:
                if spr in self.PRODUCT_PROPERTIES_LIST:
                    continue
                prop_value = self._get_searchable_prop_value(allele, spr)
                vector.append(prop_value)
            # vector = [vector]

            effect_types = getattr(allele, "effect_types", None)
            if effect_types is None:
                effect_types = allele.get_attribute("effect_types")
            if not len(effect_types):
                effect_types = [None]

            effect_gene_syms = getattr(allele, "effect_gene_symbols", None)
            if effect_gene_syms is None:
                effect_gene_syms = allele.get_attribute("effect_gene_symbols")
            if not len(effect_gene_syms):
                effect_gene_syms = [None]
            
            effect_gene = [{"effect_types": e[0],"effect_gene_symbols": e[1]} for e in zip(effect_types, effect_gene_syms)]
            vector.append(effect_gene)
            vector = [vector]

            vectors[allele.allele_index].append(list(vector))
            
        return {
            k: list(itertools.chain.from_iterable(v))
            for k, v in vectors.items()
        }

    def _get_searchable_prop_value(self, allele, spr):

        prop_value = getattr(allele, spr, None)
        if prop_value is None:
            prop_value = allele.get_attribute(spr)
        if prop_value and spr in self.ENUM_PROPERTIES:
            if isinstance(prop_value, list):
                prop_value = functools.reduce(
                    operator.or_,
                    [
                        enum.value
                        for enum in prop_value
                        if enum is not None
                    ],
                    0,
                )
            else:
                prop_value = prop_value.value
        return prop_value

    def build_family_allele_batch_dict(self, allele, family_data): 
        family_header = [] 
        family_properties = [] 
        
        for spr in self.FAMILY_SEARCHABLE_PROPERTIES_TYPES:
            prop_value = self._get_searchable_prop_value(allele, spr)
            
            family_header.append(spr)
            family_properties.append(prop_value) 

        allele_data = {name: [] for name in self.schema_family.names}
        for name, value in zip(family_header, family_properties): 
            allele_data[name].append(value)
        
        allele_data['family_data'] = [family_data]  
        return allele_data

    def build_summary_allele_batch_dict(self, allele, summary_data):
        summary_header = [] 
        summary_properties = []

        for spr in self.SUMMARY_SEARCHABLE_PROPERTIES_TYPES:
             
            if spr == 'effect_gene':
                effect_types = allele.get_attribute("effect_types") 
                effect_gene_syms = allele.get_attribute("effect_gene_symbols")

                if effect_types is None or not len(effect_types): effect_types = [None]
                if effect_gene_syms is None or not len(effect_gene_syms): effect_gene_syms = [None] 

                prop_value = [{"effect_types": e[0],"effect_gene_symbols": e[1]} for e in zip(effect_types, effect_gene_syms)]
            
            else:
                prop_value = self._get_searchable_prop_value(allele, spr)
            
            summary_header.append(spr) 
            summary_properties.append(prop_value)
        
        # data from schema 
        allele_data = {name: [] for name in self.schema_summary.names}
        for name, value in zip(summary_header, summary_properties): 
            allele_data[name].append(value) 
        
        # composite data from all alleles 
        allele_data['summary_data'] = [summary_data]
        return allele_data
