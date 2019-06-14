'''
Created on Jul 1, 2018

@author: lubo
'''
from __future__ import unicode_literals


from builtins import str
from builtins import object


class EffectGene(object):
    def __init__(self, symbol=None, effect=None):
        self.symbol = symbol
        self.effect = effect

    def __repr__(self):
        return "{}:{}".format(self.symbol, self.effect)

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        assert isinstance(other, EffectGene)

        return self.symbol == other.symbol and \
            self.effect == other.effect

    def __hash__(self):
        return hash(tuple([self.symbol, self.effect]))

    @classmethod
    def from_gene_effects(cls, gene_effects):
        result = []
        for symbol, effect in gene_effects:
            result.append(cls.from_tuple((symbol, effect)))
        return result

    @classmethod
    def from_string(cls, data):
        return cls.from_tuple(data.split(":"))

    @staticmethod
    def to_string(gene_effects):
        return str(gene_effects)

    @classmethod
    def from_tuple(cls, t):
        (symbol, effect) = tuple(t)
        return EffectGene(symbol, effect)


class EffectTranscript(object):

    def __init__(self, transcript_id, details):
        self.transcript_id = transcript_id
        self.details = details

    def __repr__(self):
        return "{}:{}".format(self.transcript_id, self.details)

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        assert isinstance(other, EffectTranscript)

        return self.transcript_id == other.transcript_id and \
            self.details == other.details

    @classmethod
    def from_tuple(cls, t):
        (transcript_id, details) = tuple(t)
        return EffectTranscript(transcript_id, details)

    @classmethod
    def from_effect_transcripts(cls, effect_transcripts):
        result = {}
        for transcript_id, details in effect_transcripts:
            result[transcript_id] = EffectTranscript.from_tuple(
                (transcript_id, details))
        return result


class Effect(object):
    def __init__(self, worst_effect, gene_effects, effect_transcripts):
        self.worst = worst_effect
        self.genes = EffectGene.from_gene_effects(gene_effects)
        self.transcripts = EffectTranscript.from_effect_transcripts(
            effect_transcripts)
        self._effect_types = None

    def __repr__(self):
        return '{}:{}'.format(self.worst, EffectGene.to_string(self.genes))

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        assert isinstance(other, Effect)

        return self.worst == other.worst and \
            self.genes == other.genes and \
            self.transcripts == other.transcripts

    @property
    def types(self):
        if self._effect_types is None:
            self._effect_types = set([
                eg.effect for eg in self.genes
            ])
        return self._effect_types

    @classmethod
    def from_effects(cls, effect_type, effect_genes, transcripts):
        return Effect(effect_type, effect_genes, transcripts)
