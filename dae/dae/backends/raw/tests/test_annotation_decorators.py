from dae.backends.raw.loader import StoredAnnotationDecorator


def test_stored_annotation_iossifov2014(iossifov2014_loader, temp_filename):

    assert iossifov2014_loader.annotation_schema is not None

    StoredAnnotationDecorator.save_annotation_file(
        iossifov2014_loader, temp_filename
    )

    variants_loader = StoredAnnotationDecorator(
        iossifov2014_loader, temp_filename
    )

    for sv, _ in variants_loader.full_variants_iterator():
        print(sv)


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
