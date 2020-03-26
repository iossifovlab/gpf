import io
import struct
import functools
import operator
import itertools
from copy import copy

from collections import namedtuple

import numpy as np

from dae.utils.variant_utils import GENOTYPE_TYPE, BEST_STATE_TYPE
from dae.annotation.tools.file_io_parquet import ParquetSchema

from dae.variants.variant import SummaryAllele, SummaryVariant
from dae.variants.family_variant import FamilyAllele, FamilyVariant
from dae.variants.attributes import (
    GeneticModel,
    Inheritance,
    VariantType,
    TransmissionType,
    Sex,
    Role,
)

import pyarrow as pa


# TODO: Optimize list methods to avoid redundancy
def write_int8(stream, num):
    stream.write(num.to_bytes(1, "big", signed=False))


def write_int8_signed(stream, num):
    stream.write(num.to_bytes(1, "big", signed=True))


def write_int32(stream, num):
    stream.write(num.to_bytes(4, "big", signed=False))


def write_np_int64(stream, num):
    stream.write(num.tobytes())


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
    write_string_list(effect_data)


def write_genotype(stream, gt):
    rows, _ = gt.shape
    assert rows == 2
    flat = gt.flatten(order="F")
    buff = flat.tobytes()

    write_int32(stream, len(buff))
    stream.write(buff)


def write_best_state(stream, best_state):
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


def read_np_int64(stream):
    return np.frombuffer(stream.read(8), dtype=np.int64)[0]


def read_float(stream):
    return struct.unpack("f", stream.read(4))[0]


def read_string(stream):
    length = read_int32(stream)
    return stream.read(length).decode("ascii")


def read_string_list(stream):
    length = int.from_bytes(stream.read(4), "big", signed=False)
    out = []
    for i in range(0, length):
        is_not_none = read_int8(stream)
        if is_not_none:
            out.append(read_string(stream))
        else:
            out.append(None)
    return out


def read_effects(stream):
    assert False
    res = [{"effects": None}]
    data = read_string_list(stream)
    if not data:
        return res
    res.extend([{"effects": e} for e in data.split("#")])

    return res


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
    for i in range(0, length):
        is_not_none = read_int8(stream)
        if is_not_none:
            out.append(Sex(read_int8(stream)))
        else:
            out.append(None)
    return out


def read_in_roles(stream):
    length = int.from_bytes(stream.read(4), "big", signed=False)
    out = []
    for i in range(0, length):
        is_not_none = read_int8(stream)
        if is_not_none:
            out.append(Role(read_int32(stream)))
        else:
            out.append(None)
    return out


def read_inheritance(stream):
    length = int.from_bytes(stream.read(4), "big", signed=False)
    out = []
    for i in range(0, length):
        is_not_none = read_int8(stream)
        if is_not_none:
            out.append(Inheritance(read_int32(stream)))
        else:
            out.append(None)
    return out


Serializer = namedtuple("Serializer", ["serialize", "deserialize"])
StringSerializer = Serializer(write_string, read_string)
IntSerializer = Serializer(write_int32, read_int32)
Int8Serializer = Serializer(write_int8, read_int8)
SignedInt8Serializer = Serializer(write_int8_signed, read_int8_signed)
NpInt64Serializer = Serializer(write_np_int64, read_np_int64)
FloatSerializer = Serializer(write_float, read_float)
VariantTypeSerializer = Serializer(write_enum, read_variant_type)
StringListSerializer = Serializer(write_string_list, read_string_list)
GenotypeSerializer = Serializer(write_genotype, read_genotype)
BestStateserializer = Serializer(write_best_state, read_best_state)
GeneticModelSerializer = Serializer(write_enum, read_genetic_model)
TransmissionTypeSerializer = Serializer(write_enum, read_transmission_type)
InSexesSerializer = Serializer(write_enum_list, read_in_sexes)
InRolesSerializer = Serializer(write_big_enum_list, read_in_roles)
InheritanceSerializer = Serializer(write_big_enum_list, read_inheritance)


class AlleleParquetSerializer:

    BASE_SEARCHABLE_PROPERTIES_TYPES = {
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
        "family_variant_index": pa.int32(),
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
        "bucket_index",
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
    ]

    def __init__(self, variants_schema):
        self.summary_prop_serializers = {
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
            "af_allele_count": NpInt64Serializer,
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

        additional_searchable_props = {}
        scores = {}

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
                ):
                    scores[col_name] = pa.float32()

        self.property_serializers_list = [
            self.summary_prop_serializers,
            self.annotation_prop_serializers,
            self.family_prop_serializers,
            self.member_prop_serializers,
        ]

        self.searchable_properties_types = {
            **self.BASE_SEARCHABLE_PROPERTIES_TYPES,
            **additional_searchable_props,
            **scores,
        }

        self.schema = None
        self._data_reset()

    def _data_reset(self):
        self._data = {name: [] for name in self.get_schema().names}

    @property
    def summary_properties(self):
        return self.summary_properties_serializers.keys()

    @property
    def annotation_properties(self):
        return self.annotation_properties_serializers.keys()

    @property
    def family_properties(self):
        return self.family_properties_serializers.keys()

    @property
    def member_properties(self):
        return self.member_properties_serializers.keys()

    @property
    def searchable_properties(self):
        return self.searchable_properties_types.keys()

    def build_table(self):
        table = pa.Table.from_pydict(self._data, self.get_schema())
        return table

    def _duplicate_allele_data(self, allele_data, amount):
        for i in range(0, amount):
            for key, value in allele_data.items():
                allele_data[key].append(copy(value[0]))

    def add_allele_to_batch_dict(self, variant, allele):
        allele_data = {name: [] for name in self.get_schema().names}
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
            allele_data[spr].append(prop_value)
        allele_data["variant_data"].append(self.serialize_variant(variant))

        product_values = list()

        ltr_flat = list(itertools.chain(*self.LIST_TO_ROW_PROPERTIES_LISTS))

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

        for kvs in itertools.product(*product_values):
            for k, v in kvs:
                if isinstance(k, list):
                    for i in range(0, len(k)):
                        if v is None:
                            self._data[k[i]].append(None)
                        else:
                            self._data[k[i]].append(v[i])
                else:
                    self._data[k].append(v[0])

    def _serialize_allele(self, allele, stream):
        for property_serializers in self.property_serializers_list:
            for prop, serializer in property_serializers.items():
                value = getattr(allele, prop, None)
                if value is None:
                    value = allele.get_attribute(prop)
                self.write_property(stream, value, serializer)

    def serialize_variant(self, variant):
        stream = io.BytesIO()
        write_int8(stream, len(variant.alleles))
        for allele in variant.alleles:
            self._serialize_allele(allele, stream)

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
        return allele_data

    def deserialize_family_variant(self, data, family):
        summary_alleles = []
        stream = io.BytesIO(data)
        allele_count = read_int8(stream)
        for i in range(0, allele_count):
            allele_data = self.deserialize_allele(stream)
            sa = SummaryAllele(
                allele_data["chromosome"],
                allele_data["position"],
                allele_data["reference"],
                alternative=allele_data["alternative"],
                end_position=allele_data["end_position"],
                summary_index=allele_data["summary_index"],
                allele_index=allele_data["allele_index"],
                transmission_type=allele_data["transmission_type"],
                variant_type=allele_data["variant_type"],
            )
            summary_alleles.append(sa)

            allele_attributes_data = {
                k: v
                for (k, v) in allele_data.items()
                if k not in self.ALLELE_CREATION_PROPERTIES
            }
            sa.update_attributes(allele_attributes_data)

        sv = SummaryVariant(summary_alleles)
        fv = FamilyVariant(
            sv, family, allele_data["gt"], allele_data["best_state"],
        )

        return fv

    def get_schema(self):
        if self.schema is None:
            fields = []
            for spr in self.searchable_properties:
                field = pa.field(spr, self.searchable_properties_types[spr])
                fields.append(field)
            fields.append(pa.field("variant_data", pa.binary()))
            self.schema = pa.schema(fields)
        return self.schema


class ParquetSerializer(object):

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
    ]

    summary = namedtuple(
        "summary",
        [
            "summary_variant_index",
            "allele_index",
            "chrom",
            "position",
            "end_position",
            "reference",
            "alternative",
            "variant_type",
            "transmission_type",
            # 'worst_effect',
            "alternatives_data",
        ],
    )

    effect_gene = namedtuple(
        "effect_gene", ["effect_type", "effect_gene", "effect_data",]
    )

    Family = namedtuple(
        "family",
        [
            "family_variant_index",
            "family_id",
            "is_denovo",
            "variant_sexes",
            "variant_roles",
            "variant_inheritance",
            "genotype_data",
            "best_state_data",
            "genetic_model_data",
            "inheritance_data",
        ],
    )

    member = namedtuple(
        "member",
        [
            "variant_in_member",
            # 'variant_in_role',
            # 'variant_in_sex',
            # 'inheritance_in_member',
        ],
    )

    frequency = namedtuple(
        "frequency",
        [
            "af_parents_called_count",
            "af_parents_called_percent",
            "af_allele_count",
            "af_allele_freq",
            "frequency_data",
        ],
    )

    def __init__(self, schema, include_reference=False):
        assert schema is not None
        assert isinstance(schema, ParquetSchema), type(schema)

        self.include_reference = include_reference
        self.schema = schema
        self._setup_genomic_scores()

    def _setup_genomic_scores(self):
        base_schema = ParquetSchema.from_arrow(ParquetSchema.BASE_SCHEMA)
        genomic_scores_schema = ParquetSchema.diff_schemas(
            self.schema, base_schema
        )
        for field_name in self.GENOMIC_SCORES_SCHEMA_CLEAN_UP:
            if field_name in genomic_scores_schema.columns:
                del genomic_scores_schema.columns[field_name]

        self.genomic_scores_schema = genomic_scores_schema.to_arrow()

        self.genomic_scores_count = len(self.genomic_scores_schema.names)
        fields = [*(self.genomic_scores_schema.names), "genomic_scores_data"]
        self.genomic_scores = namedtuple("genomic_scores", fields)

    def serialize_summary(
        self, summary_variant_index, allele, alternatives_data
    ):
        if allele.is_reference_allele:
            return self.summary(
                summary_variant_index,
                allele.allele_index,
                allele.chrom,
                allele.position,
                allele.end_position,
                allele.reference,
                None,
                None,
                allele.transmission_type.value,
                alternatives_data,
            )
        else:
            return self.summary(
                summary_variant_index,
                allele.allele_index,
                allele.chrom,
                allele.position,
                allele.end_position,
                allele.reference,
                allele.alternative,
                allele.variant_type.value,
                allele.transmission_type.value,
                alternatives_data,
            )

    def serialize_effects(self, allele, effect_data):
        if allele.is_reference_allele:
            return [self.effect_gene(None, None, effect_data)]
        if allele.allele_index == -1:
            return [self.effect_gene(None, None, effect_data)]
        return [
            self.effect_gene(eg.effect, eg.symbol, effect_data)
            for eg in allele.effect.genes
        ]

    def serialize_alelle_frequency(self, allele, frequency_data):
        freq = self.frequency(
            allele.get_attribute("af_parents_called_count"),
            allele.get_attribute("af_parents_called_percent"),
            allele.get_attribute("af_allele_count"),
            allele.get_attribute("af_allele_freq"),
            frequency_data,
        )
        return freq

    @staticmethod
    def serialize_variant_frequency(v):
        result = np.zeros((len(v.alleles), 4), dtype=np.float32)
        for row, allele in enumerate(v.alleles):
            result[row, 0] = allele.get_attribute("af_parents_called_count")
            result[row, 1] = allele.get_attribute("af_parents_called_percent")
            result[row, 2] = allele.get_attribute("af_allele_count")
            result[row, 3] = allele.get_attribute("af_allele_freq")
        flat = result.flatten(order="F")
        buff = flat.tobytes()
        data = str(buff, "latin1")
        return data

    @staticmethod
    def deserialize_variant_frequency(data):
        buff = bytes(data, "latin1")
        flat = np.frombuffer(buff, dtype=np.float32)
        assert len(flat) % 4 == 0

        rows = len(flat) // 4
        res = flat.reshape([rows, 4], order="F")
        attributes = []
        for row in range(rows):
            af_parents_called_count = (
                int(res[row, 0]) if not np.isnan(res[row, 0]) else None
            )
            af_parents_called_percent = (
                res[row, 1] if not np.isnan(res[row, 1]) else None
            )
            af_allele_count = (
                int(res[row, 2]) if not np.isnan(res[row, 2]) else None
            )
            af_allele_freq = res[row, 3] if not np.isnan(res[row, 3]) else None
            a = {
                "af_parents_called_count": af_parents_called_count,
                "af_parents_called_percent": af_parents_called_percent,
                "af_allele_count": af_allele_count,
                "af_allele_freq": af_allele_freq,
            }
            attributes.append(a)

        return attributes

    def serialize_genomic_scores(self, allele, genomic_scores_data):
        values = []
        for gs in self.genomic_scores_schema.names:
            values.append(allele.get_attribute(gs))
        values.append(genomic_scores_data)

        genomic_scores = self.genomic_scores(*values)
        return genomic_scores

    def serialize_variant_genomic_scores(self, v):
        if self.genomic_scores_count == 0:
            return None
        result = np.zeros(
            (len(v.alleles), self.genomic_scores_count), dtype=np.float32
        )
        for row, allele in enumerate(v.alleles):
            for col, gs in enumerate(self.genomic_scores_schema.names):
                result[row, col] = allele.get_attribute(gs)
        flat = result.flatten(order="F")
        buff = flat.tobytes()
        data = str(buff, "latin1")
        return data

    def deserialize_variant_genomic_scores(self, data):
        if data is None:
            return None
        buff = bytes(data, "latin1")
        flat = np.frombuffer(buff, dtype=np.float32)
        assert (
            len(flat) % self.genomic_scores_count == 0
        ), self.genomic_scores_schema

        rows = len(flat) // self.genomic_scores_count
        result = flat.reshape([rows, self.genomic_scores_count], order="F")
        attributes = []
        for row in range(rows):
            a = {
                gs: result[row, col]
                for col, gs in enumerate(self.genomic_scores_schema.names)
            }
            attributes.append(a)

        return attributes

    @staticmethod
    def serialize_variant_genotype(gt):
        rows, _ = gt.shape
        assert rows == 2
        flat = gt.flatten(order="F")
        buff = flat.tobytes()
        data = str(buff, "latin1")

        return data

    @staticmethod
    def deserialize_variant_genotype(data):
        buff = bytes(data, "latin1")
        gt = np.frombuffer(buff, dtype=GENOTYPE_TYPE)
        assert len(gt) % 2 == 0

        size = len(gt) // 2
        gt = gt.reshape([2, size], order="F")
        return gt

    @staticmethod
    def serialize_variant_best_state(best_state):
        flat = best_state.flatten(order="F")
        buff = flat.tobytes()
        data = str(buff, "latin1")

        return data

    @staticmethod
    def deserialize_variant_best_state(data, col_count):
        buff = bytes(data, "latin1")
        best_state = np.frombuffer(buff, dtype=BEST_STATE_TYPE)
        assert len(best_state) % col_count == 0

        size = len(best_state) // col_count
        best_state = best_state.reshape([size, col_count], order="F")
        return best_state

    @staticmethod
    def serialize_variant_inheritance(family_variant):
        data = [fa.inheritance_in_members for fa in family_variant.alleles]
        data = [inh.value for inh in itertools.chain(*data)]
        assert len(data) == len(family_variant.family) * len(
            family_variant.alleles
        )
        data = np.array(data, dtype=np.int16)

        buff = data.tobytes()
        buff = str(buff, "latin1")

        return buff

    @staticmethod
    def deserialize_variant_inheritance(data, col_count):

        data = bytes(data, "latin1")
        data = np.frombuffer(data, dtype=np.int16)
        assert len(data) % col_count == 0

        size = len(data) // col_count

        data = data.reshape([size, col_count], order="C")
        result = [
            [Inheritance.from_value(v) for v in allele_inheritance]
            for allele_inheritance in data
        ]
        return result

    @staticmethod
    def serialize_variant_alternatives(alternatives):
        return ",".join(alternatives)

    @staticmethod
    def deserialize_variant_alternatives(data):
        res = [None]
        if data is None:
            return res
        res.extend(data.split(","))
        return res

    @staticmethod
    def serialize_variant_effects(effects):
        if effects is None:
            return None
        return "#".join([str(e) for e in effects])

    @staticmethod
    def deserialize_variant_effects(data):
        res = [{"effects": None}]
        if data is None:
            return res
        res.extend([{"effects": e} for e in data.split("#")])

        return res

    def serialize_family(
        self,
        family_variant_index,
        family_allele,
        genotype_data,
        best_state_data,
        genetic_model_data,
        inheritance_data,
    ):
        res = self.Family(
            family_variant_index,
            family_allele.family_id,
            family_allele.get_attribute("is_denovo"),
            functools.reduce(
                operator.or_,
                [
                    vs.value
                    for vs in family_allele.variant_in_sexes
                    if vs is not None
                ],
                0,
            ),
            functools.reduce(
                operator.or_,
                [
                    vr.value
                    for vr in family_allele.variant_in_roles
                    if vr is not None
                ],
                0,
            ),
            functools.reduce(
                operator.or_,
                [
                    vi.value
                    for vi in family_allele.inheritance_in_members
                    if vi is not None
                ],
                0,
            ),
            genotype_data,
            best_state_data,
            genetic_model_data,
            inheritance_data,
        )
        return res

    def serialize_members(self, family_variant_index, family):
        result = []
        for variant_in_member in family.variant_in_members:
            if variant_in_member is None:
                continue
            result.append(self.member(variant_in_member))
        return result

    def deserialize_variant(
        self,
        family,
        chrom,
        position,
        end_position,
        reference,
        transmission_type,
        alternatives_data,
        effect_data,
        genotype_data,
        best_state_data,
        genetic_model_data,
        inheritance_data,
        frequency_data,
        genomic_scores_data,
    ):

        effects = self.deserialize_variant_effects(effect_data)
        alternatives = self.deserialize_variant_alternatives(alternatives_data)
        # assert len(effects) == len(alternatives), (effects, alternatives)
        assert family is not None

        genotype = self.deserialize_variant_genotype(genotype_data)
        rows, cols = genotype.shape
        if cols != len(family):
            print(
                f"problem: {chrom},{position},{reference},{alternatives}: "
                f"{family}"
            )
            return None

        assert cols == len(family)

        best_state = self.deserialize_variant_best_state(
            best_state_data, len(family),
        )

        genetic_model = GeneticModel(genetic_model_data)

        frequencies = self.deserialize_variant_frequency(frequency_data)
        # assert len(frequencies) == len(alternatives)
        inheritance = self.deserialize_variant_inheritance(
            inheritance_data, len(family)
        )
        # assert len(inheritance) == len(alternatives), \
        #     (inheritance, alternatives)

        genomic_scores = self.deserialize_variant_genomic_scores(
            genomic_scores_data
        )
        if genomic_scores is None:
            values = zip(alternatives, effects, inheritance, frequencies)
        else:
            assert len(frequencies) == len(genomic_scores)
            attributes = []
            for (f, g) in zip(frequencies, genomic_scores):
                f.update(g)
                attributes.append(f)
            values = zip(alternatives, effects, inheritance, attributes)

        alleles = []
        for allele_index, (alt, effect, inher, attr) in enumerate(values):
            attr.update(effect)
            summary_allele = SummaryAllele(
                chrom,
                position,
                reference,
                alternative=alt,
                summary_index=0,
                allele_index=allele_index,
                transmission_type=transmission_type,
                attributes=attr,
            )

            family_allele = FamilyAllele(
                summary_allele,
                family=family,
                genotype=genotype,
                best_state=best_state,
                genetic_model=genetic_model,
                inheritance_in_members=inher,
            )
            alleles.append(family_allele)

        return FamilyVariant(
            SummaryVariant(alleles), family, genotype, best_state
        )
