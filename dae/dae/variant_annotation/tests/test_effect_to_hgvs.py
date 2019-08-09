import pytest
from dae.variant_annotation.annotator import VariantAnnotator
# from variant_annotation.effect_to_hgvs import EffectToHGVS


@pytest.fixture(scope="session")
def genome(request):
    from dae.DAE import genomesDB

    return genomesDB.get_genome()


@pytest.fixture(scope="session")
def gene_models(request):
    from dae.DAE import genomesDB
    return genomesDB.get_gene_models()


@pytest.mark.skip
@pytest.mark.parametrize("location,variant", [
    ('1:899319', 'del(2)'),
    ('4:69202842', 'ins(AT)'),

])
def test_frame_shift(genome, gene_models, location, variant):
    effects = VariantAnnotator.annotate_variant(
        gene_models, genome,
        loc=location,
        var=variant)

    assert effects is not None

    # for effect in effects:
    #     result = EffectToHGVS.effect_to_HGVS(effect)
    #     print(result)
    #     assert result


# def test_frame_shift2(genome, gene_models):
#     effects = VariantAnnotator.annotate_variant(
#         gene_models, genome,
#         loc="12:130827138",
#         var="del(4)")

#     assert effects is not None
#     for effect in effects:
#         result = EffectToHGVS.effect_to_HGVS(effect)
#         print(result)
#         assert result
