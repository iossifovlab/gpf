from django.db import models

# Create your models here.


EFFECT_CHOICES = (
    ('1', "3'UTR",),
    ('2', "3'UTR-intron",),
    ('3', "5'UTR",),
    ('4', "5'UTR-intron",),
    ('5', "frame-shift",),
    ('6', "intergenic",),
    ('7', "intron",),
    ('7', "missense",),
    ('9', "no-frame-shift",),
    ('10', "no-frame-shift-newStop",),
    ('11', "noEnd",),
    ('12', "noStart",),
    ('13', "non-coding",),
    ('14', "non-coding-intron",),
    ('15', "nonsense",),
    ('16', "splice-site",),
    ('17', "synonymous",),
)

VARIANT_CHOICES = (
    ('del', 'del'),
    ('ins', 'ins'),
    ('sub', 'sub'),
    ('cnv', 'CNV'),
)


class SummaryVariant(models.Model):
    ln = models.IntegerField(db_index=True)

    chrome = models.CharField(max_length=3, db_index=True)
    position = models.IntegerField()
    variant = models.CharField(max_length=45)
    variant_type = models.CharField(max_length=4,
                                    choices=VARIANT_CHOICES)

#     effect_type = models.CharField(max_length=3,
#                                    choices=EFFECT_CHOICES)
#     effect_gene = models.CharField(max_length=32, db_index=True)
#
#     effect_count = models.IntegerField()

    n_par_called = models.IntegerField()
    n_alt_alls = models.IntegerField()
    alt_freq = models.FloatField()

    prcnt_par_called = models.FloatField()
    seg_dups = models.IntegerField()
    hw = models.FloatField()

    ssc_freq = models.FloatField(null=True)
    evs_freq = models.FloatField(null=True)
    e65_freq = models.FloatField(null=True)


class GeneEffectVariant(models.Model):
    summary_variant = models.ForeignKey(SummaryVariant,
                                        related_name="effects")

    symbol = models.CharField(max_length=32, db_index=True)
    effect_type = models.CharField(max_length=3,
                                   choices=EFFECT_CHOICES)
    variant_type = models.CharField(max_length=4,
                                    choices=VARIANT_CHOICES)

    n_par_called = models.IntegerField()
    n_alt_alls = models.IntegerField()
    alt_freq = models.FloatField()
