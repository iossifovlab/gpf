from django.db import models

# Create your models here.


class SummaryVariant(models.Model):
    ln = models.IntegerField(db_index=True)

    chrome = models.CharField(max_length=3, db_index=True)
    position = models.IntegerField()
    variant = models.CharField(max_length=45)
    variant_type = models.CharField(max_length=4)

    effect_type = models.CharField(max_length=32, null=True, db_index=True)
    effect_gene = models.CharField(max_length=32, db_index=True, null=True)

    effect_count = models.IntegerField(default=0)

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

    symbol = models.CharField(max_length=32, db_index=True, null=True)
    effect_type = models.CharField(max_length=32, db_index=True)
    variant_type = models.CharField(max_length=4)

    n_par_called = models.IntegerField()
    n_alt_alls = models.IntegerField()
    alt_freq = models.FloatField()


class FamilyVariant(models.Model):
    summary_variant = models.ForeignKey(SummaryVariant,
                                        related_name="family_variants")
    family_id = models.CharField(max_length=16, db_index=True)

    best = models.CharField(max_length=16)
    counts = models.CharField(max_length=64)

    in_mom = models.BooleanField(default=False)
    in_dad = models.BooleanField(default=False)

    in_prb = models.BooleanField(default=False)
    in_prb_gender = models.CharField(max_length=1, null=True)
    in_sib = models.BooleanField(default=False)
    in_sib_gender = models.CharField(max_length=1, null=True)
