from dae.backends.raw.loader import StoredAnnotationDecorator


def test_stored_annotation_iossifov2014(
        iossifov2014_loader, temp_filename):

    iossifov2014_loader.save_annotation_file(temp_filename)

    variants_loader = StoredAnnotationDecorator(
        iossifov2014_loader, temp_filename)

    for sv, _ in variants_loader.summary_genotypes_iterator():
        print(sv)
