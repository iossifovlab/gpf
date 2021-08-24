"""
Created on Jul 1, 2018

@author: lubo
"""


class EffectGene(object):
    def __init__(self, symbol=None, effect=None):
        self.symbol = symbol
        self.effect = effect

    @staticmethod
    def from_string(data):
        if not data:
            return None

        parts = [p.strip() for p in data.split(":")]
        if len(parts) == 2:
            return EffectGene(parts[0], parts[1])
        elif len(parts) == 1:
            return EffectGene(symbol=None, effect=parts[0])
        else:
            raise ValueError("unexpected effect gene format: {}".format(data))

    def __repr__(self):
        if self.symbol is None:
            return self.effect
        else:
            return "{}:{}".format(self.symbol, self.effect)

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        assert isinstance(other, EffectGene)

        return self.symbol == other.symbol and self.effect == other.effect

    def __hash__(self):
        return hash(tuple([self.symbol, self.effect]))

    @classmethod
    def from_gene_effects(cls, gene_effects):
        result = []
        for symbol, effect in gene_effects:
            result.append(cls.from_tuple((symbol, effect)))
        return result

    @classmethod
    def from_tuple(cls, t):
        (symbol, effect) = tuple(t)
        return EffectGene(symbol, effect)


class EffectTranscript(object):
    def __init__(self, transcript_id, gene, details):
        self.transcript_id = transcript_id
        self.gene = gene
        self.details = details

    @staticmethod
    def from_string(data):
        if not data:
            return None

        parts = [p.strip() for p in data.split(":")]
        assert len(parts) == 3
        return EffectTranscript(parts[0], parts[1], parts[2])

    def __repr__(self):
        return f"{self.transcript_id}:{self.gene}:{self.details}"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        assert isinstance(other, EffectTranscript)

        return (
            self.transcript_id == other.transcript_id
            and self.details == other.details
        )

    @classmethod
    def from_tuple(cls, t):
        (transcript_id, details) = tuple(t)
        return EffectTranscript(transcript_id, details)

    @classmethod
    def from_effect_transcripts(cls, effect_transcripts):
        result = {}
        for transcript_id, details in effect_transcripts:
            result[transcript_id] = EffectTranscript.from_tuple(
                (transcript_id, details)
            )
        return result


class Effect(object):
    def __init__(self, worst_effect, gene_effects, effect_transcripts):
        self.worst = worst_effect
        self.genes = gene_effects
        self.transcripts = effect_transcripts
        self._effect_types = None

    def __repr__(self):
        effects = "|".join([str(g) for g in self.genes])
        transcripts = "|".join([str(t) for t in self.transcripts.values()])
        return "{}!{}!{}".format(self.worst, effects, transcripts)

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        assert isinstance(other, Effect)

        return (
            self.worst == other.worst
            and self.genes == other.genes
            and self.transcripts == other.transcripts
        )

    @property
    def types(self):
        if self._effect_types is None:
            self._effect_types = [eg.effect for eg in self.genes]
        return self._effect_types

    @classmethod
    def from_effects(cls, effect_type, effect_genes, transcripts):
        if effect_type is None:
            return None

        transcripts = EffectTranscript.from_effect_transcripts(transcripts)
        effect_genes = EffectGene.from_gene_effects(effect_genes)
        return Effect(effect_type, effect_genes, transcripts)

    @staticmethod
    def from_string(data):
        if data is None:
            return None
        parts = data.split("!")
        assert len(parts) == 3, parts
        worst = parts[0].strip()
        effect_genes = [
            EffectGene.from_string(eg.strip()) for eg in parts[1].split("|")
        ]
        effect_genes = [eg for eg in filter(None, effect_genes)]
        transcripts = [
            EffectTranscript.from_string(et.strip())
            for et in parts[2].split("|")
        ]
        transcripts = filter(None, transcripts)
        transcripts = {t.transcript_id: t for t in transcripts}
        if not effect_genes and not transcripts:
            return None
        return Effect(worst, effect_genes, transcripts)
