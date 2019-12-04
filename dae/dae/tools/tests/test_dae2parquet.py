from box import Box

from dae.pedigrees.family import FamiliesLoader

from dae.tools.dae2parquet import parse_cli_arguments, dae_build_makefile

from dae.backends.raw.loader import AnnotationPipelineDecorator

from dae.backends.impala.parquet_io import ParquetManager
from dae.backends.dae.loader import DaeTransmittedLoader, DenovoLoader

from dae.annotation.tools.file_io_parquet import ParquetReader


def test_dae2parquet_denovo(
        dae_denovo_config, annotation_pipeline_internal,
        temp_dirname,
        default_gpf_instance, dae_config_fixture, genomes_db):

    print(dae_denovo_config)

    genome = genomes_db.get_genome()

    families_loader = FamiliesLoader(
        dae_denovo_config.family_filename,
        params={'ped_file_format': 'simple'})

    variants_loader = DenovoLoader(
        families_loader.families, dae_denovo_config.denovo_filename, genome)
    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal
    )

    study_id = "test_dae2parquet_denovo"

    parquet_filenames = ParquetManager.build_parquet_filenames(
        temp_dirname, bucket_index=100, study_id=study_id)

    ParquetManager.pedigree_to_parquet(
        variants_loader, parquet_filenames.pedigree)
    ParquetManager.variants_to_parquet(
        variants_loader, parquet_filenames.variant,
        bucket_index=100
    )

    summary = ParquetReader(Box({
        'infile': parquet_filenames.variant,
    }, default_box=True, default_box_attr=None))
    summary._setup()
    summary._cleanup()

    # print(summary.schema)
    schema = summary.schema
    print(schema['score0'])

    assert schema['score0'].type_name == 'float'
    assert schema['score2'].type_name == 'float'
    assert schema['score4'].type_name == 'float'

    assert schema['effect_gene'].type_name == 'str'
    assert schema['effect_type'].type_name == 'str'
    assert schema['effect_data'].type_name == 'str'
    # assert schema['worst_effect'].type_name == 'str'


def test_dae2parquet_transmitted(
        dae_transmitted_config, annotation_pipeline_internal,
        temp_dirname,
        default_gpf_instance, dae_config_fixture, genomes_db):

    genome = genomes_db.get_genome()

    families_loader = FamiliesLoader(
        dae_transmitted_config.family_filename,
        params={'ped_file_format': 'simple'})

    variants_loader = DaeTransmittedLoader(
        families_loader.families,
        dae_transmitted_config.summary_filename,
        dae_transmitted_config.toomany_filename,
        genome
    )
    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal)

    parquet_filenames = ParquetManager.build_parquet_filenames(
        temp_dirname, bucket_index=100, study_id="test_dae_transmitted"
    )
    ParquetManager.pedigree_to_parquet(
        variants_loader, parquet_filenames.pedigree)
    ParquetManager.variants_to_parquet(
        variants_loader, parquet_filenames.variant)

    summary = ParquetReader(Box({
        'infile': parquet_filenames.variant,
    }, default_box=True, default_box_attr=None))
    summary._setup()
    summary._cleanup()

    # print(summary.schema)
    schema = summary.schema
    print(schema['score0'])

    assert schema['score0'].type_name == 'float'
    assert schema['score2'].type_name == 'float'
    assert schema['score4'].type_name == 'float'

    assert schema['effect_gene'].type_name == 'str'
    assert schema['effect_type'].type_name == 'str'
    assert schema['effect_data'].type_name == 'str'
    # assert schema['worst_effect'].type_name == 'str'


def test_dae2parquet_make(
        dae_transmitted_config, annotation_pipeline_config,
        annotation_scores_dirname, temp_dirname,
        default_gpf_instance, dae_config_fixture, genomes_db):

    argv = [
        'make',
        '--annotation', annotation_pipeline_config,
        '-o', temp_dirname,
        '-f', 'simple',
        '-l', '100000000',
        dae_transmitted_config.family_filename,
        dae_transmitted_config.summary_filename,
        dae_transmitted_config.toomany_filename,
    ]
    genome = genomes_db.get_genome()

    argv = parse_cli_arguments(default_gpf_instance, argv)

    assert argv is not None
    assert argv.type == 'make'

    dae_build_makefile(dae_config_fixture, genome, argv)
