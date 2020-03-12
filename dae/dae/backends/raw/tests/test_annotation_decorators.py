from dae.backends.raw.loader import StoredAnnotationDecorator


def test_annotation_pipeline_decorator_iossifov2014(iossifov2014_loader):

    assert iossifov2014_loader.annotation_schema is not None

    variants_loader = iossifov2014_loader

    for sv, _ in variants_loader.full_variants_iterator():
        assert len(sv.alt_alleles) == 1
        assert sv.alt_alleles[0].attributes["score0"] == sv.position
        assert sv.alt_alleles[0].attributes["score2"] == sv.position / 100
        assert sv.alt_alleles[0].attributes["score4"] == sv.position / 10000


def test_stored_annotation_iossifov2014(iossifov2014_loader, temp_filename):

    assert iossifov2014_loader.annotation_schema is not None

    StoredAnnotationDecorator.save_annotation_file(
        iossifov2014_loader, temp_filename
    )

    variants_loader = StoredAnnotationDecorator(
        iossifov2014_loader, temp_filename
    )

    for sv, _ in variants_loader.full_variants_iterator():
        assert len(sv.alt_alleles) == 1
        assert sv.alt_alleles[0].attributes["score0"] == sv.position
        assert sv.alt_alleles[0].attributes["score2"] == sv.position / 100
        assert sv.alt_alleles[0].attributes["score4"] == sv.position / 10000


def test_stored_annotation_does_not_change_summary_alleles(
    iossifov2014_loader, temp_filename
):

    assert iossifov2014_loader.annotation_schema is not None

    StoredAnnotationDecorator.save_annotation_file(
        iossifov2014_loader, temp_filename
    )

    variants_loader = StoredAnnotationDecorator(
        iossifov2014_loader, temp_filename
    )

    for sv, fvs in variants_loader.full_variants_iterator():
        for fv in fvs:
            # Effects will be None if the annotator copies the summary allele
            assert fv.effects is not None
