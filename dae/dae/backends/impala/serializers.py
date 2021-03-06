import io
import struct

import functools
import operator
import itertools
import logging

from collections import namedtuple, defaultdict

import numpy as np
import pyarrow as pa

from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant
from dae.variants.attributes import GeneticModel, Inheritance, VariantType, \
    TransmissionType, Sex, Role


logger = logging.getLogger(__name__)


# TODO: Optimize list methods to avoid redundancy
def write_int8(stream, num):
    stream.write(num.to_bytes(1, "big", signed=False))


def write_int8_signed(stream, num):
    stream.write(num.to_bytes(1, "big", signed=True))


def write_int32(stream, num):
    stream.write(num.to_bytes(4, "big", signed=False))


# def write_np_int64(stream, num):
#     stream.write(num.tobytes())


def write_float(stream, num):
    stream.write(struct.pack("f", num))


def write_string(stream, string):
    length = len(string)
    stream.write(length.to_bytes(4, "big", signed=False))
    stream.write(string.encode("ascii"))


def write_string_list(stream, li):
    length = len(li)
    write_int32(stream, length)
    for string in li:
        if string is None:
            write_int8(stream, 0)
        else:
            write_int8(stream, 1)
            write_string(stream, string)


def write_effects(stream, allele):
    effect_data = allele.effects
    effect_genes = None
    if not allele.is_reference_allele and allele.allele_index != -1:
        effect_genes = allele.effect.genes
    if effect_genes:
        write_int8(stream, 1)
        write_string_list(stream, [eg.effect for eg in effect_genes])
        write_string_list(stream, [eg.symbol for eg in effect_genes])
    else:
        write_int8(stream, 0)
    write_string_list(stream, effect_data)


def write_genotype(stream, gt):
    assert gt.dtype == np.int8

    rows, _ = gt.shape
    assert rows == 2
    flat = gt.flatten(order="F")
    buff = flat.tobytes()

    write_int32(stream, len(buff))
    stream.write(buff)


def write_best_state(stream, best_state):
    assert best_state.dtype == np.int8

    _, col_count = best_state.shape
    flat = best_state.flatten(order="F")
    buff = flat.tobytes()

    write_int32(stream, len(buff))
    write_int32(stream, col_count)
    stream.write(buff)


def write_enum(stream, enum):
    write_int8(stream, enum.value)


def write_big_enum(stream, enum):
    write_int32(stream, enum.value)


def write_enum_list(stream, li):
    length = len(li)
    write_int32(stream, length)
    for enum in li:
        if enum is None:
            write_int8(stream, 0)
        else:
            write_int8(stream, 1)
            write_enum(stream, enum)


def write_big_enum_list(stream, li):
    length = len(li)
    write_int32(stream, length)
    for enum in li:
        if enum is None:
            write_int8(stream, 0)
        else:
            write_int8(stream, 1)
            write_big_enum(stream, enum)


def read_int8(stream):
    return int.from_bytes(stream.read(1), "big", signed=False)


def read_int8_signed(stream):
    return int.from_bytes(stream.read(1), "big", signed=True)


def read_int32(stream):
    return int.from_bytes(stream.read(4), "big", signed=False)


# def read_np_int64(stream):
#     return np.frombuffer(stream.read(8), dtype=np.int64)[0]


def read_float(stream):
    return struct.unpack("f", stream.read(4))[0]


def read_string(stream):
    length = read_int32(stream)
    return stream.read(length).decode("ascii")


def read_string_list(stream):
    length = int.from_bytes(stream.read(4), "big", signed=False)
    out = []
    for _i in range(0, length):
        is_not_none = read_int8(stream)
        if is_not_none:
            out.append(read_string(stream))
        else:
            out.append(None)
    return out


# def read_effects(stream):
#     assert False
#     res = [{"effects": None}]
#     data = read_string_list(stream)
#     if not data:
#         return res
#     res.extend([{"effects": e} for e in data.split("#")])

#     return res


def read_genotype(stream):
    length = read_int32(stream)
    buff = stream.read(length)
    gt = np.frombuffer(buff, dtype=np.int8)
    assert len(gt) % 2 == 0

    size = len(gt) // 2
    gt = gt.reshape([2, size], order="F")
    return gt


def read_best_state(stream):
    length = read_int32(stream)
    col_count = read_int32(stream)
    buff = stream.read(length)
    best_state = np.frombuffer(buff, dtype=np.int8)
    assert len(best_state) % col_count == 0

    size = len(best_state) // col_count
    best_state = best_state.reshape([size, col_count], order="F")
    return best_state


def read_variant_type(stream):
    return VariantType(read_int8(stream))


def read_genetic_model(stream):
    return GeneticModel(read_int8(stream))


def read_transmission_type(stream):
    return TransmissionType(read_int8(stream))


def read_in_sexes(stream):
    length = int.from_bytes(stream.read(4), "big", signed=False)
    out = []
    for _i in range(0, length):
        is_not_none = read_int8(stream)
        if is_not_none:
            out.append(Sex(read_int8(stream)))
        else:
            out.append(None)
    return out


def read_in_roles(stream):
    length = int.from_bytes(stream.read(4), "big", signed=False)
    out = []
    for _i in range(0, length):
        is_not_none = read_int8(stream)
        if is_not_none:
            out.append(Role(read_int32(stream)))
        else:
            out.append(None)
    return out


def read_inheritance(stream):
    length = int.from_bytes(stream.read(4), "big", signed=False)
    out = []
    for _i in range(0, length):
        is_not_none = read_int8(stream)
        if is_not_none:
            out.append(Inheritance(read_int32(stream)))
        else:
            out.append(None)
    return out


Serializer = namedtuple("Serializer", ["serialize", "deserialize", "type"])
StringSerializer = Serializer(write_string, read_string, "string")
IntSerializer = Serializer(write_int32, read_int32, "int32")
Int8Serializer = Serializer(write_int8, read_int8, "int8")
SignedInt8Serializer = Serializer(
    write_int8_signed, read_int8_signed, "int8 signed")
# NpInt64Serializer = Serializer(write_np_int64, read_np_int64, "numpy_int64")
FloatSerializer = Serializer(write_float, read_float, "float")
VariantTypeSerializer = Serializer(
    write_enum, read_variant_type, "variant type")
StringListSerializer = Serializer(
    write_string_list, read_string_list, "string list")
GenotypeSerializer = Serializer(
    write_genotype, read_genotype, "genotype")
BestStateserializer = Serializer(
    write_best_state, read_best_state, "best state")
GeneticModelSerializer = Serializer(
    write_enum, read_genetic_model, "genetic model")
TransmissionTypeSerializer = Serializer(
    write_enum, read_transmission_type, "transmission type")
InSexesSerializer = Serializer(
    write_enum_list, read_in_sexes, "in sexes")
InRolesSerializer = Serializer(
    write_big_enum_list, read_in_roles, "in roles")
InheritanceSerializer = Serializer(
    write_big_enum_list, read_inheritance, "inheritance")


class AlleleParquetSerializer:

    SUMMARY_SEARCHABLE_PROPERTIES_TYPES = {
        "bucket_index": pa.int32(),
        "chromosome": pa.string(),
        "position": pa.int32(),
        "end_position": pa.int32(),
        "effect_types": pa.string(),
        "effect_gene_symbols": pa.string(),
        "summary_index": pa.int32(),
        "allele_index": pa.int32(),
        "variant_type": pa.int8(),
        "transmission_type": pa.int8(),
        "reference": pa.string(),
    }

    FAMILY_SEARCHABLE_PROPERTIES_TYPES = {
        "family_index": pa.int32(),
        "family_id": pa.string(),
        "is_denovo": pa.int8(),
        "variant_in_sexes": pa.int8(),
        "variant_in_roles": pa.int32(),
        "inheritance_in_members": pa.int16(),
        "variant_in_members": pa.string(),
    }

    PRODUCT_PROPERTIES_LIST = [
        "effect_types", "effect_gene_symbols", "variant_in_members"
    ]

    BASE_SEARCHABLE_PROPERTIES_TYPES = {
        "bucket_index": pa.int32(),
        "chromosome": pa.string(),
        "position": pa.int32(),
        "end_position": pa.int32(),
        "effect_types": pa.string(),
        "effect_gene_symbols": pa.string(),
        "summary_index": pa.int32(),
        "allele_index": pa.int32(),
        "variant_type": pa.int8(),
        "transmission_type": pa.int8(),
        "reference": pa.string(),
        "family_index": pa.int32(),
        "family_id": pa.string(),
        "is_denovo": pa.int8(),
        "variant_in_sexes": pa.int8(),
        "variant_in_roles": pa.int32(),
        "inheritance_in_members": pa.int16(),
        "variant_in_members": pa.string(),
    }

    LIST_TO_ROW_PROPERTIES_LISTS = [
        ["effect_types", "effect_gene_symbols"],
        ["variant_in_members"],
    ]

    ENUM_PROPERTIES = {
        "variant_type": VariantType,
        "transmission_type": TransmissionType,
        "variant_in_sexes": Sex,
        "variant_in_roles": Role,
        "inheritance_in_members": Inheritance,
    }

    ALLELE_CREATION_PROPERTIES = [
        "chromosome",
        "position",
        "end_position",
        "variant_type",
        "reference",
        "alternative",
        "allele_index",
        "summary_index",
        "transmission_type",
        "variant_type",
        "family_id",
        "gt",
        "best_state",
        "genetic_model",
        "variant_in_roles",
        "variant_in_sexes",
        "inheritance_in_members",
        "variant_in_members",
    ]

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
        "variant_in_member",
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
                f"serializer varints schema {variants_schema.col_names}")

        self.summary_prop_serializers = {
            "bucket_index": IntSerializer,
            "chromosome": StringSerializer,
            "position": IntSerializer,
            "end_position": IntSerializer,
            "variant_type": VariantTypeSerializer,
            "reference": StringSerializer,
            "alternative": StringSerializer,
            "allele_index": SignedInt8Serializer,
            "summary_index": IntSerializer,
            "transmission_type": TransmissionTypeSerializer,
        }
        self.annotation_prop_serializers = {
            "af_allele_freq": FloatSerializer,
            "af_allele_count": IntSerializer,
            "af_parents_called_count": IntSerializer,
            "af_parents_called_percent": FloatSerializer,
            "effect_type": StringSerializer,
            "effect_gene_genes": StringListSerializer,
            "effect_gene_types": StringListSerializer,
            "effect_details_transcript_ids": StringListSerializer,
            "effect_details_details": StringListSerializer,
        }
        self.family_prop_serializers = {
            "family_id": StringSerializer,
            "gt": GenotypeSerializer,
            "best_state": BestStateserializer,
            "genetic_model": GeneticModelSerializer,
            "variant_in_roles": InRolesSerializer,
            "variant_in_sexes": InSexesSerializer,
            "inheritance_in_members": InheritanceSerializer,
        }
        self.member_prop_serializers = {
            "variant_in_members": StringListSerializer
        }
        self._schema = None

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

        self.summary_serializers_list = [
            self.summary_prop_serializers,
            self.annotation_prop_serializers,
        ]
        # Family variant index was being imported into the scores schema
        # previously by mistake
        self.family_serializers_list = [
            self.family_prop_serializers,
            self.member_prop_serializers,
            {"family_variant_index": IntSerializer}
        ]
        self.property_serializers_list = [
            *self.summary_serializers_list,
            *self.family_serializers_list,
            self.scores_serializers,
        ]

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

        self._allele_batch_header = None

    @property
    def schema(self):
        if self._schema is None:
            fields = []
            for spr in self.searchable_properties:
                field = pa.field(spr, self.searchable_properties_types[spr])
                fields.append(field)
            fields.append(pa.field("variant_data", pa.binary()))
            fields.append(pa.field("extra_attributes", pa.binary()))
            self._schema = pa.schema(fields)
        return self._schema

    # @property
    # def summary_properties(self):
    #     return self.summary_properties_serializers.keys()

    # @property
    # def annotation_properties(self):
    #     return self.annotation_properties_serializers.keys()

    # @property
    # def family_properties(self):
    #     return self.family_properties_serializers.keys()

    # @property
    # def member_properties(self):
    #     return self.member_properties_serializers.keys()

    @property
    def searchable_properties_summary(self):
        return self.searchable_properties_summary_types.keys()

    @property
    def searchable_properties_family(self):
        return self.searchable_properties_family_types.keys()

    @property
    def searchable_properties(self):
        return self.searchable_properties_types.keys()

    def _serialize_family_allele(self, allele, stream):
        for property_serializers in self.family_serializers_list:
            for prop, serializer in property_serializers.items():
                value = getattr(allele, prop, None)
                if value is None:
                    value = allele.get_attribute(prop)
                self.write_property(stream, value, serializer)

    def serialize_family_variant(
            self, variant_alleles, summary_blobs, scores_blobs):
        stream = io.BytesIO()
        write_int8(stream, len(variant_alleles))
        for allele in variant_alleles:
            stream.write(summary_blobs[allele.allele_index])
            self._serialize_family_allele(allele, stream)
            stream.write(scores_blobs[allele.allele_index])

        stream.seek(0)
        output = stream.read()
        stream.close()
        return output

    def _serialize_summary_allele(self, allele, stream):
        for property_serializers in self.summary_serializers_list:
            for prop, serializer in property_serializers.items():
                value = getattr(allele, prop, None)
                if value is None:
                    value = allele.get_attribute(prop)
                self.write_property(stream, value, serializer)

    def serialize_summary_data(self, alleles):
        output = []
        for allele in alleles:
            stream = io.BytesIO()
            self._serialize_summary_allele(allele, stream)
            stream.seek(0)
            blob = stream.read()
            output.append(blob)
            stream.close()

        return output

    def _serialize_allele_scores(self, allele, stream):
        property_serializers = self.scores_serializers
        for prop, serializer in property_serializers.items():
            value = getattr(allele, prop, None)
            if value is None:
                value = allele.get_attribute(prop)
            self.write_property(stream, value, serializer)

    def serialize_scores_data(self, alleles):
        scores_blobs = []
        for allele in alleles:
            stream = io.BytesIO()
            self._serialize_allele_scores(allele, stream)
            stream.seek(0)
            blob = stream.read()
            scores_blobs.append(blob)
            stream.close()
        return scores_blobs

    def serialize_extra_attributes(self, variant):
        stream = io.BytesIO()
        write_int8(stream, len(self.extra_attributes))
        for prop in self.extra_attributes:
            write_string(stream, prop)
            write_string(stream, variant.get_attribute(prop)[1])

        stream.seek(0)
        output = stream.read()
        stream.close()
        return output

    def write_property(self, stream, value, serializer):
        if value is None:
            write_int8(stream, 0)
        else:
            write_int8(stream, 1)
            serializer.serialize(stream, value)

    def deserialize_allele(self, stream):
        allele_data = {}
        for property_serializers in self.property_serializers_list:
            for prop, serializer in property_serializers.items():
                is_not_none = read_int8(stream)
                if is_not_none:
                    allele_data[prop] = serializer.deserialize(stream)
                else:
                    allele_data[prop] = None
        allele_data["chrom"] = allele_data["chromosome"]
        del allele_data["chromosome"]
        return allele_data

    def deserialize_summary_variant(self, main_blob, extra_blob=None):
        stream = io.BytesIO(main_blob)
        allele_count = read_int8(stream)
        records = []
        for _i in range(0, allele_count):
            allele_data = self.deserialize_allele(stream)
            records.append(allele_data)

        sv = SummaryVariantFactory.summary_variant_from_records(
            records, attr_filter=self.ALLELE_CREATION_PROPERTIES)

        extra_attributes = {}
        if extra_blob:
            stream = io.BytesIO(extra_blob)
            extra_attributes_count = read_int8(stream)
            for i in range(0, extra_attributes_count):
                name = read_string(stream)
                value = read_string(stream)
                extra_attributes[name] = [value]

        sv.update_attributes(extra_attributes)

        return sv

    def deserialize_family_variant(self, main_blob, family, extra_blob=None):

        stream = io.BytesIO(main_blob)
        allele_count = read_int8(stream)
        records = []
        for _i in range(0, allele_count):
            allele_data = self.deserialize_allele(stream)
            records.append(allele_data)

        sv = SummaryVariantFactory.summary_variant_from_records(
            records, attr_filter=self.ALLELE_CREATION_PROPERTIES)
        fv = FamilyVariant(
            sv, family, allele_data["gt"], allele_data["best_state"],
        )

        extra_attributes = {}
        if extra_blob:
            stream = io.BytesIO(extra_blob)
            extra_attributes_count = read_int8(stream)
            for i in range(0, extra_attributes_count):
                name = read_string(stream)
                value = read_string(stream)
                extra_attributes[name] = [value]

        fv.update_attributes(extra_attributes)

        return fv

    def build_searchable_vectors_summary(self, summary_variant):
        vectors = dict()
        for allele in summary_variant.alleles:
            vector = []
            product_properties = []
            if allele.allele_index not in vectors:
                vectors[allele.allele_index] = []
            for spr in self.searchable_properties_summary:
                if spr in self.PRODUCT_PROPERTIES_LIST:
                    product_properties.append(spr)
                    continue
                prop_value = self._get_searchable_prop_value(allele, spr)
                vector.append(prop_value)
            vector = [vector]
            for prop in product_properties:
                prop_value = getattr(allele, prop, None)
                if prop_value is None:
                    prop_value = allele.get_attribute(prop)
                if not len(prop_value):
                    prop_value = [None]
                vector = list(itertools.product(vector, prop_value))
                vector = [list(itertools.chain.from_iterable(map(
                    lambda x: x if isinstance(x, list) else [x],
                    subvector
                ))) for subvector in vector]
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

    @property
    def allele_batch_header(self):
        if self._allele_batch_header is None:
            header = []
            product_props = []
            for spr in self.searchable_properties_summary:
                if spr in self.PRODUCT_PROPERTIES_LIST:
                    product_props.append(spr)
                else:
                    header.append(spr)
            header = header + product_props
            product_props = []
            for spr in self.searchable_properties_family:
                if spr in self.PRODUCT_PROPERTIES_LIST:
                    product_props.append(spr)
                else:
                    header.append(spr)
            header = header + product_props

            self._allele_batch_header = header
        return self._allele_batch_header

    def build_allele_batch_dict(
            self, allele, variant_data,
            extra_attributes_data,
            summary_vectors):
        vectors = summary_vectors[allele.allele_index]
        family_properties = []
        product_properties = []
        for spr in self.searchable_properties_family:
            if spr in self.PRODUCT_PROPERTIES_LIST:
                product_properties.append(spr)
                continue
            prop_value = self._get_searchable_prop_value(allele, spr)
            family_properties.append(prop_value)
        new_vectors = zip(vectors, itertools.repeat(family_properties))
        new_vectors = list(map(list, map(
            itertools.chain.from_iterable,
            new_vectors
        )))
        for prop in product_properties:
            prop_value = getattr(allele, prop, None)
            if prop_value is None:
                prop_value = allele.get_attribute(prop)
            prop_value = list(filter(lambda x: x is not None, prop_value))
            if not len(prop_value):
                # This is added to handle the case when the reference allele
                # has a variant_in_members consisting only of None, but has
                # to be written anyways
                prop_value = [None]
            new_vectors = list(itertools.product(new_vectors, prop_value))
            new_vectors = [list(itertools.chain.from_iterable(map(
                lambda x: x if isinstance(x, list) else [x],
                subvector
            ))) for subvector in new_vectors]

        header = self.allele_batch_header
        allele_data = {name: [] for name in self.schema.names}
        for idx, field_name in enumerate(header):
            for vector in new_vectors:
                allele_data[field_name].append(vector[idx])
        allele_data["variant_data"] = list(itertools.repeat(
            variant_data, len(new_vectors)))
        allele_data["extra_attributes"] = list(itertools.repeat(
            extra_attributes_data, len(new_vectors)))
        return allele_data

    def build_allele_batch_dict_old(
            self, variant_data, extra_attributes_data, allele):
        allele_data = {name: [] for name in self.schema.names}
        for spr in self.searchable_properties:
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
            if spr == "variant_in_members":
                prop_value = list(filter(lambda v: v is not None, prop_value))

            allele_data[spr].append(prop_value)
        allele_data["variant_data"].append(variant_data)
        allele_data["extra_attributes"].append(extra_attributes_data)

        product_values = list()

        ltr_flat = list(itertools.chain(
            *self.LIST_TO_ROW_PROPERTIES_LISTS))

        for k, v in allele_data.items():
            if k not in ltr_flat:
                product_values += [[(k, v)]]

        for ltr_props in self.LIST_TO_ROW_PROPERTIES_LISTS:
            k = ltr_props
            if allele_data[k[0]][0]:
                length = len(allele_data[k[0]][0])
                v = []
                for i in range(0, length):
                    v.append([])
                    for prop in k:
                        v[i].append(allele_data[prop][0][i])
            else:
                v = [None for _ in k]
            product_values += [[(k, v2) for v2 in v]]

        result = defaultdict(list)
        for kvs in itertools.product(*product_values):
            for k, v in kvs:
                if isinstance(k, list):
                    for i in range(0, len(k)):
                        if v is None:
                            result[k[i]].append(None)
                        else:
                            result[k[i]].append(v[i])
                else:
                    result[k].append(v[0])
        return result

    def describe_blob_schema(self):
        schema_description = dict()
        for property_serializers in self.property_serializers_list:
            for prop, serializer in property_serializers.items():
                schema_description[prop] = serializer.type
        return schema_description
