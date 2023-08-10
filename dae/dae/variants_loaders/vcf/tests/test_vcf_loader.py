# pylint: disable=W0621,C0114,C0116,W0212,W0613
import copy
import os
from pathlib import Path
from typing import Any, Callable, Optional
import pytest
import numpy as np
import yaml
from dae.annotation.annotation_factory import AnnotationConfigParser, AnnotationConfigurationError, check_for_repeated_attributes, check_for_unused_parameters, get_annotator_factory
from dae.annotation.annotation_pipeline import AnnotationPipeline, AnnotatorInfo, InputAnnotableAnnotatorDecorator, ValueTransformAnnotatorDecorator
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.repository_factory import build_genomic_resource_repository
from dae.variants_loaders.dae.loader import DenovoLoader
from dae.variants_loaders.raw.loader import AnnotationPipelineDecorator
from dae.variants.attributes import Inheritance
from dae.variants_loaders.vcf.loader import VcfLoader
from dae.configuration.gpf_config_parser import DefaultBox
from dae.genomic_resources.testing import setup_pedigree, setup_vcf
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.inmemory_storage.raw_variants import RawMemoryVariants
from dae.testing.acgt_import import acgt_gpf
from dae.pedigrees.loader import FamiliesLoader


@pytest.fixture
def gpf_instance(
        tmp_path_factory: pytest.TempPathFactory) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("instance")
    gpf_instance = acgt_gpf(root_path)
    return gpf_instance


@pytest.fixture
def effects_trio_dad_ped(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("effects_trio_dad")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role	phenotype
    f1	        mom1	    0	    0	    2	1	    mom	    unaffected
    f1	        dad1	    0	    0	    1	1	    dad	    unaffected
    f1	        ch1	        dad1	mom1	2	2	    prb	    autism
    """)
    return ped_path


@pytest.fixture
def effects_trio_dad_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("effects_trio_dad")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	    mom1  dad1  ch1
    1	    865582	.	C	T	    .	    .	    EFF=SYN	GT	    0/1	  0/0	0/0
    1	    1222518	.	C	A	    .	    .	    .	    GT	    0/0	  0/1	0/0
    """)
    return vcf_path


@pytest.fixture
def effects_trio_ped(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("effects_trio")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1	        mom1	    0	    0	    2	1	    mom
    f1	        dad1	    0	    0	    1	1	    dad
    f1	        ch1	        dad1	mom1	2	2	    prb
    """)
    return ped_path


@pytest.fixture
def effects_trio_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("effects_trio")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	         ALT	        QUAL	FILTER	INFO	    FORMAT	mom1  dad1	ch1
    1	    865582	.	C	         T	            .	    .	    EFF=SYN	    GT	    0/1	  0/0	0/1
    1	    865583	.	G	         A	            .	    .	    EFF=SYN	    GT	    0/1	  0/0	0/1
    1	    865624	.	G	         A	            .	    .	    EFF=MIS	    GT	    0/1	  0/0	0/1
    1	    865627	.	G	         A	            .	    .	    EFF=MIS	    GT	    0/1	  0/0	0/1
    1	    865664	.	G	         A	            .	    .	    EFF=SYN	    GT	    0/1	  0/0	0/1
    1	    865691	.	C	         T	            .	    .	    EFF=MIS	    GT	    0/1	  0/0	0/1
    1	    878109	.	C	         G,T	        .	    .	    EFF=MIS!MIS	GT	    0/1	  0/0	0/1
    1	    901921	.	G	         A,C	        .	    .	    EFF=SYN!MIS	GT	    0/1	  0/0	0/1
    1	    905956	.	CGGCTCGGAAGG C,TGGCTCGGAAGG	.	    .	    EFF=FS!MIS	GT	    0/1	  0/0	0/1
    1	    1222518	.	C	         A	            .	    .	    .	        GT	    0/1	  0/1	1/1
    """)
    return vcf_path


@pytest.fixture
def effects_trio2_ped(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("effects_trio2")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1	        mom1	    0	    0	    2	1	    mom
    f1	        dad1	    0	    0	    1	1	    dad
    f1	        ch1	        dad1	mom1	2	2	    prb
    f2	        mom2	    0	    0	    2	1	    mom
    f2	        dad2	    0	    0	    1	1	    dad
    f2	        ch2	        dad2	mom2	2	2	    prb
    """)
    return ped_path


@pytest.fixture
def effects_trio2_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("effects_trio2")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	    QUAL FILTER	INFO	FORMAT	mom1	dad1	ch1	  miss	dad2  ch2   mom2
    1	    11539	.	T	G	    .	 .	    .	    GT	    0/1	    0/0	    0/0	  1/1	0/0	  0/0	0/1
    1	    11540	.	T	G	    .	 .	    .	    GT	    0/0	    0/1	    0/0	  1/1	0/1	  0/0	0/0
    1	    11541	.	T	G	    .	 .	    .	    GT	    0/0	    0/0	    0/0	  0/0	0/1	  0/0	0/0
    1	    11542	.	T	G	    .	 .	    .	    GT	    0/1	    0/0	    0/0	  0/0	0/0	  0/0	0/0
    1	    11551	.	T	G	    .	 .	    .	    GT	    1/1	    1/1	    0/0	  0/0	1/1	  0/0	1/1
    1	    11552	.	T	G	    .	 .	    .	    GT	    1/1	    1/1	    1/1	  1/1	1/1	  1/1	1/1
    1	    11553	.	T	G	    .	 .	    .	    GT	    0/0	    0/0	    1/1	  1/1	0/0	  1/1	0/0
    1	    11601	.	T	G,A	    .	 .	    .	    GT	    0/1	    0/1	    0/0	  0/0	0/0	  0/0	0/0
    1	    11602	.	T	G,A	    .	 .	    .	    GT	    0/2	    0/2	    0/0	  0/0	0/0	  0/0	0/0
    1	    11603	.	T	G,A	    .	 .	    .	    GT	    0/0	    0/0	    0/0	  0/0	0/2	  0/0	0/2
    1	    11604	.	T	G,A	    .	 .	    .	    GT	    0/0	    0/0	    0/0	  0/0	0/1	  0/0	0/1
    1	    11605	.	T	G,A	    .	 .	    .	    GT	    0/1	    0/2	    0/0	  0/0	0/1	  0/0	0/2
    1	    11606	.	T	G,A,C	.	 .	    .	    GT	    0/1	    0/2	    0/0	  0/0	0/1	  0/0	0/2
    """)
    return vcf_path


@pytest.fixture
def members_in_order1_ped(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("members_in_order1")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId  personId	dadId	momId	sex	status	role
    f	      gpa	    0	    0	    1	1	    paternal_grandfather
    f	      gma	    0	    0	    2	1	    paternal_grandmother
    f	      mom	    0	    0	    2	1	    mom
    f	      dad	    gpa	    gma	    1	1	    dad
    f	      ch1	    dad	    mom	    2	2	    prb
    f	      ch2	    dad	    mom	    2	1	    sib
    f	      ch3	    dad	    mom	    2	1	    sib
    """)
    return ped_path


@pytest.fixture
def members_in_order1_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("members_in_order1")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT QUAL  FILTER  INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    1	    11539	.	T	G   .	  .	      .	    GT	    0/0	0/0	0/0	0/0	0/1	0/0	0/1
    1	    11540	.	T	G   .	  .	      .	    GT	    0/0	0/0	0/0	0/0	0/0	0/1	0/1
    """)
    return vcf_path

@pytest.fixture
def members_in_order2_ped(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("members_in_order2")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId  personId	dadId	momId	sex	status	role
    f	      gpa	    0	    0	    1	1	    paternal_grandfather
    f	      gma	    0	    0	    2	1	    paternal_grandmother
    f	      mom	    0	    0	    2	1	    mom
    f	      dad	    gpa	    gma	    1	1	    dad
    f	      ch1	    dad	    mom	    2	2	    prb
    f	      ch2	    dad	    mom	    2	1	    sib
    f	      ch3	    dad	    mom	    2	1	    sib
    """)
    return ped_path


@pytest.fixture
def members_in_order2_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("members_in_order2")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=1>
    #CHROM	POS	   ID REF  ALT	QUAL  FILTER  INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    1	    11539  .  T	   G	.	  .	      .	    GT	    0/0	0/0	0/1	0/0	0/1	0/0	0/0
    1	    11540  .  T	   G	.	  .	      .	    GT	    0/0	0/0	0/1	0/0	0/0	0/1	0/0
    """)
    return vcf_path


@pytest.fixture
def unknown_trio_ped(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("unknown_trio")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId  personId	dadId	momId	sex	status	role
    f1	      mom1	    0	    0	    2	1	    mom
    f1	      dad1	    0	    0	    1	1	    dad
    f1	      ch1	    dad1	mom1	2	2	    prb
    """)
    return ped_path


@pytest.fixture
def unknown_trio_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("unknown_trio")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	    QUAL	FILTER	INFO	FORMAT	mom1	dad1	ch1
    1	    11500	.	C	T	    .	    .	    .	    GT	    0/1	    0/0	    0/.
    1	    11501	.	C	T	    .	    .	    .	    GT	    0/1	    0/0	    1/.
    1	    11502	.	C	T	    .	    .	    .	    GT	    0/0	    0/0	    1/.
    1	    11503	.	C	T	    .	    .	    .	    GT	    0/1	    0/1	    1/1
    """)
    return vcf_path


@pytest.fixture
def trios_multi_ped(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("trios_multi")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId  personId	dadId	momId	sex	status	role
    f1	      mom1	    0	    0	    2	1	    mom
    f1	      dad1	    0	    0	    1	1	    dad
    f1	      ch1	    dad1	mom1	2	2	    prb
    f2	      mom2	    0	    0	    2	1	    mom
    f2	      dad2	    0	    0	    1	1	    dad
    f2	      ch2	    dad2	mom2	2	2	    prb
    """)
    return ped_path


@pytest.fixture
def trios_multi_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("trios_multi")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	    QUAL	FILTER	INFO	FORMAT	mom1	dad1	ch1
    1	    11500	.	T	G,C	    .	    .	    .	    GT	    0/1	    0/0	    0/0
    1	    11501	.	T	G,C	    .	    .	    .	    GT	    0/2	    0/0	    0/0
    1	    11502	.	T	G,C	    .	    .	    .	    GT	    0/0	    0/0	    0/0
    1	    11503	.	T	G,C	    .	    .	    .	    GT	    0/1	    0/0	    0/0
    1	    11504	.	T	G,C	    .	    .	    .	    GT	    0/1	    0/2	    0/0
    1	    11505	.	T	G,C,A	.	    .	    .	    GT	    0/1	    0/2	    0/3
    1	    11506	.	T	G,C,A	.	    .	    .	    GT	    0/1	    0/2	    0/0
    """)
    return vcf_path


@pytest.fixture
def quads_f1_ped(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("quads_f1")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId  personId	dadId	momId	sex	status	role
    f1	      mom1	    0	    0	    2	1	    mom
    f1	      dad1	    0	    0	    1	1	    dad
    f1	      prb1	    dad1	mom1	1	2	    prb
    f1	      sib1	    dad1	mom1	2	2	    sib
    """)
    return ped_path


@pytest.fixture
def quads_f1_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("quads_f1")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=1>
    ##contig=<ID=2>
    #CHROM	POS	    ID	REF	ALT	QUAL  FILTER  INFO	FORMAT	mom1  dad1	prb1  sib1
    1	    11539	.	T	G	.	  .	      .	    GT	    0/1	  0/0	0/1	  0/0
    2	    11540	.	T	G	.	  .	      .	    GT	    0/0	  0/1	0/1	  0/0
    """)
    return vcf_path

def vcf_loader_data(prefix: str, pedigree: Path, vcf: Path) -> DefaultBox:
    conf = {
        "prefix": prefix,
        "pedigree": str(pedigree),
        "vcf": str(vcf)
    }

    return DefaultBox(conf)


@pytest.fixture()
def vcf_variants_loaders(gpf_instance):
    annotation_pipeline = construct_import_annotation_pipeline(
        gpf_instance
    )

    def builder(
        path,
        params={
            "vcf_include_reference_genotypes": True,
            "vcf_include_unknown_family_genotypes": True,
            "vcf_include_unknown_person_genotypes": True,
            "vcf_denovo_mode": "denovo",
            "vcf_omission_mode": "omission",
        },
    ):
        config = path

        families_loader = FamiliesLoader(config.pedigree)
        families = families_loader.load()

        loaders = []

        if config.denovo:
            denovo_loader = DenovoLoader(
                families,
                config.denovo,
                gpf_instance.reference_genome,
                params={
                    "denovo_genotype": "genotype",
                    "denovo_family_id": "family",
                    "denovo_chrom": "chrom",
                    "denovo_pos": "pos",
                    "denovo_ref": "ref",
                    "denovo_alt": "alt",
                }
            )
            loaders.append(AnnotationPipelineDecorator(
                denovo_loader, annotation_pipeline))

        vcf_loader = VcfLoader(
            families,
            [config.vcf],
            gpf_instance.reference_genome,
            params=params
        )

        loaders.append(AnnotationPipelineDecorator(
            vcf_loader, annotation_pipeline
        ))

        return loaders

    return builder


def construct_import_annotation_pipeline(
        gpf_instance, annotation_configfile=None):
    """Construct annotation pipeline for importing data."""
    pipeline_config = []
    if annotation_configfile is not None:
        assert os.path.exists(annotation_configfile), annotation_configfile
        with open(annotation_configfile, "rt", encoding="utf8") as infile:
            pipeline_config = yaml.safe_load(infile.read())
    else:
        if gpf_instance.dae_config.annotation is not None:
            config_filename = gpf_instance.dae_config.annotation.conf_file
            assert os.path.exists(config_filename), config_filename
            with open(config_filename, "rt", encoding="utf8") as infile:
                pipeline_config = yaml.safe_load(infile.read())

        pipeline_config.insert(
            0, _construct_import_effect_annotator_config(gpf_instance))

    grr = gpf_instance.grr
    pipeline = build_annotation_pipeline(
        pipeline_config_raw=pipeline_config, grr_repository=grr)
    return pipeline


def _construct_import_effect_annotator_config(gpf_instance):
    """Construct import effect annotator."""
    genome = gpf_instance.reference_genome
    gene_models = gpf_instance.gene_models

    config = {
        "effect_annotator": {
            "genome": genome.resource_id,
            "gene_models": gene_models.resource_id,
            "attributes": [
                {
                    "source": "allele_effects",
                    "destination": "allele_effects",
                    "internal": True
                }
            ]
        }
    }
    return config


def build_annotation_pipeline(
        pipeline_config: Optional[list[AnnotatorInfo]] = None,
        pipeline_config_raw: Optional[list[dict]] = None,
        pipeline_config_file: Optional[str] = None,
        pipeline_config_str: Optional[str] = None,
        grr_repository: Optional[GenomicResourceRepo] = None,
        grr_repository_file: Optional[str] = None,
        grr_repository_definition: Optional[dict] = None
) -> AnnotationPipeline:
    """Build an annotation pipeline."""
    if pipeline_config_file is not None:
        assert pipeline_config is None
        assert pipeline_config_raw is None
        assert pipeline_config_str is None
        pipeline_config = AnnotationConfigParser.parse_config_file(
            pipeline_config_file)
    elif pipeline_config_str is not None:
        assert pipeline_config_raw is None
        assert pipeline_config is None
        pipeline_config = AnnotationConfigParser.parse_str(pipeline_config_str)
    elif pipeline_config_raw is not None:
        assert pipeline_config is None
        pipeline_config = AnnotationConfigParser.parse_raw(pipeline_config_raw)
    assert pipeline_config is not None

    if not grr_repository:
        grr_repository = build_genomic_resource_repository(
            definition=grr_repository_definition,
            file_name=grr_repository_file)
    else:
        assert grr_repository_file is None
        assert grr_repository_definition is None

    pipeline = AnnotationPipeline(grr_repository)

    for annotator_id, annotator_config in enumerate(pipeline_config):
        raw_config_copy = copy.deepcopy(annotator_config)
        try:
            builder = get_annotator_factory(annotator_config.type)

            # annotator_config = set_parameter_usage_monitors(annotator_config)
            annotator = builder(pipeline, annotator_config)
            annotator = InputAnnotableAnnotatorDecorator.decorate(annotator)
            annotator = ValueTransformAnnotatorDecorator.decorate(annotator)
            check_for_unused_parameters(annotator_config)
            check_for_repeated_attributes(pipeline, annotator_config)
            pipeline.add_annotator(annotator)
        except ValueError as value_error:
            raise AnnotationConfigurationError(
                f"The {annotator_id+1}-th annotator "
                f"configuration {raw_config_copy} is incorrect: ",
                value_error) from value_error

    return pipeline


@pytest.fixture
def variants_vcf(vcf_variants_loaders):
    def builder(
        path,
        params={
            "vcf_include_reference_genotypes": True,
            "vcf_include_unknown_family_genotypes": True,
            "vcf_include_unknown_person_genotypes": True,
            "vcf_denovo_mode": "denovo",
            "vcf_omission_mode": "omission",
        },
    ) -> RawMemoryVariants:

        loaders = vcf_variants_loaders(path, params=params)
        assert len(loaders) > 0
        fvars = RawMemoryVariants(loaders, loaders[0].families)
        return fvars

    return builder


@pytest.mark.parametrize(
    "fixture_data",
    [
        ("effects_trio_dad",
            "effects_trio_dad_ped",
            "effects_trio_dad_vcf"),
        ("effects_trio", "effects_trio_ped", "effects_trio_vcf"),
        ("effects_trio2", "effects_trio2_ped", "effects_trio2_vcf"),
        ("members_in_order1", "members_in_order1_ped", "members_in_order1_vcf"),
        ("members_in_order2", "members_in_order2_ped", "members_in_order2_vcf"),
        ("unknown_trio", "unknown_trio_ped", "unknown_trio_vcf"),
        ("trios_multi", "trios_multi_ped", "trios_multi_vcf"),
        ("quads_f1", "quads_f1_ped", "quads_f1_vcf"),
    ],
)
def test_vcf_loader(
    request: pytest.FixtureRequest,
    fixture_data: tuple[str, str, str],
    gpf_instance: GPFInstance
) -> None:
    prefix, pedigree, vcf = fixture_data
    pedigree_path = request.getfixturevalue(pedigree)
    vcf_path = request.getfixturevalue(vcf)
    conf = vcf_loader_data(prefix, pedigree_path, vcf_path)
    print(conf)
    families_loader = FamiliesLoader(conf.pedigree)
    families = families_loader.load()

    loader = VcfLoader(
        families,
        [conf.vcf],
        gpf_instance.reference_genome,
        params={
            "vcf_include_reference_genotypes": True,
            "vcf_include_unknown_family_genotypes": True,
            "vcf_include_unknown_person_genotypes": True,
        },
    )
    assert loader is not None

    vars_new = list(loader.family_variants_iterator())

    for nfv in vars_new:
        print(nfv)


@pytest.fixture
def multivcf_split1_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("mutlivcf_split1")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1
    1	    865582	.	C	T	.	    .	    EFF=SYN	GT	    1/1	    0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1
    1	    865583	.	G	A	.	    .	    EFF=SYN	GT	    0/0	    1/1 	0/1 	0/1 	0/0 	1/1 	1/0 	0/1 	0/0 	1/1 	0/1 	0/1
    1	    865624	.	G	A	.	    .	    EFF=MIS	GT	    1/0	    0/0 	0/1 	0/0 	1/0 	0/0 	0/1 	0/0 	1/0 	0/0 	0/1 	0/0
    1	    865627	.	G	A	.	    .	    EFF=MIS	GT	    0/0	    1/0 	0/1 	0/0 	0/0 	1/0 	0/1 	0/0 	0/0 	1/1 	0/1 	1/0
    1	    865664	.	G	A	.	    .	    EFF=SYN	GT	    0/1	    0/0 	0/1 	0/0 	0/1 	0/0 	0/0 	0/1 	0/1 	0/0 	0/1 	0/0
    1	    865691	.	C	T	.	    .	    EFF=MIS	GT	    1/0	    1/0 	0/1 	0/0 	1/0 	1/0 	0/1 	0/0 	1/0 	1/1 	0/1 	0/1
    """)

    return vcf_path


@pytest.fixture
def multivcf_split2_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("mutlivcf_split1")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f4.mom	f4.dad	f4.p1	f4.s1	f5.mom	f5.dad	f5.p1	f5.s1	f3.s1
    1	    865582	.	C	T	.   	.   	EFF=SYN	GT  	1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	1/0 	0/1 	./.
    1	    865583	.	G	A	.   	.   	EFF=SYN	GT  	0/0 	1/1 	0/1 	0/1 	0/0 	1/1 	1/0 	0/1 	./.
    1	    865624	.	G	A	.   	.   	EFF=MIS	GT  	1/0 	0/0 	1/0 	0/0 	1/0 	0/0 	1/0 	0/0 	./.
    1	    865627	.	G	A	.   	.   	EFF=MIS	GT  	0/0 	1/1 	1/0 	0/0 	0/0 	1/1 	1/0 	1/0 	./.
    1	    865664	.	G	A	.   	.   	EFF=SYN	GT  	0/1 	0/0 	0/1 	0/0 	0/1 	0/0 	0/0 	0/1 	./.
    1	    865691	.	C	T	.   	.   	EFF=MIS	GT  	1/0 	1/1 	1/0 	1/0 	1/0 	1/1 	0/1 	0/1 	./.
    """)

    return vcf_path


@pytest.fixture
def multivcf_ped(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("multivcf")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role	phenotype
    f1	        f1.mom  	0   	0	    2	1	    mom 	unaffected
    f1	        f1.dad  	0	    0	    1	1	    dad 	unaffected
    f1	        f1.p1   	f1.dad	f1.mom	1	2	    prb 	autism
    f1	        f1.s1   	f1.dad	f1.mom	2	2	    sib	    autism
    f2	        f2.mom  	0	    0	    2	1	    mom 	unaffected
    f2	        f2.dad  	0	    0	    1	1	    dad 	unaffected
    f2	        f2.p1   	f2.dad	f2.mom	1	2	    prb	    autism
    f2	        f2.s1   	f2.dad	f2.mom	2	2	    sib	    autism
    f3	        f3.mom  	0	    0	    2	1	    mom 	unaffected
    f3	        f3.dad  	0	    0	    1	1	    dad 	unaffected
    f3	        f3.p1   	f3.dad	f3.mom	1	2	    prb	    autism
    f3	        f3.s1   	f3.dad	f3.mom	2	2	    sib	    autism
    f4	        f4.mom  	0	    0	    2	1	    mom 	unaffected
    f4	        f4.dad  	0	    0	    1	1	    dad 	unaffected
    f4	        f4.p1   	f4.dad	f4.mom	1	2	    prb 	autism
    f4	        f4.s1   	f4.dad	f4.mom	2	2	    sib 	autism
    f5	        f5.mom  	0	    0	    2	1	    mom 	unaffected
    f5	        f5.dad  	0	    0	    1	1	    dad 	unaffected
    f5	        f5.p1   	f5.dad	f5.mom	1	2	    prb 	autism
    f5	        f5.s1   	f5.dad	f5.mom	2	2	    sib	    autism
    """)

    return ped_path


def test_simple_vcf_loader_multi(
    gpf_instance: GPFInstance,
    multivcf_split1_vcf: Path,
    multivcf_split2_vcf: Path,
    multivcf_ped: Path
) -> None:
    vcf_filenames = [
        str(multivcf_split1_vcf),
        str(multivcf_split2_vcf),
    ]
    assert all(os.path.exists(fn) for fn in vcf_filenames)
    assert os.path.exists(str(multivcf_ped))

    families = FamiliesLoader(multivcf_ped).load()

    vcf_loader = VcfLoader(
        families,
        vcf_filenames,
        gpf_instance.reference_genome,
        fill_missing_ref=False,
    )
    assert vcf_loader is not None
    variants = list(vcf_loader.full_variants_iterator())
    assert len(variants) == 6


@pytest.fixture
def multivcf_original_ped(tmp_path_factory: pytest.TempPathFactory):
    root_path = tmp_path_factory.mktemp("multivcf_original")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role	phenotype
    f1	        f1.mom	    0	    0	    2	1	    mom 	unaffected
    f1	        f1.dad	    0	    0	    1	1	    dad 	unaffected
    f1	        f1.p1	    f1.dad	f1.mom	1	2	    prb 	autism
    f1	        f1.s1	    f1.dad	f1.mom	2	2	    sib 	autism
    f2	        f2.mom	    0	    0	    2	1	    mom 	unaffected
    f2	        f2.dad	    0	    0	    1	1	    dad 	unaffected
    f2	        f2.p1	    f2.dad	f2.mom	1	2	    prb 	autism
    f2	        f2.s1	    f2.dad	f2.mom	2	2	    sib 	autism
    f3	        f3.mom	    0	    0	    2	1	    mom 	unaffected
    f3	        f3.dad	    0	    0	    1	1	    dad 	unaffected
    f3	        f3.p1	    f3.dad	f3.mom	1	2	    prb 	autism
    f3	        f3.s1	    f3.dad	f3.mom	2	2	    sib 	autism
    f4	        f4.mom	    0	    0	    2	1	    mom 	unaffected
    f4	        f4.dad	    0	    0	    1	1	    dad 	unaffected
    f4	        f4.p1	    f4.dad	f4.mom	1	2	    prb 	autism
    f4	        f4.s1	    f4.dad	f4.mom	2	2	    sib 	autism
    f5	        f5.mom	    0	    0	    2	1	    mom 	unaffected
    f5	        f5.dad	    0	    0	    1	1	    dad 	unaffected
    f5	        f5.p1	    f5.dad	f5.mom	1	2	    prb 	autism
    f5	        f5.s1	    f5.dad	f5.mom	2	2	    sib 	autism
    """)

    return ped_path


@pytest.fixture
def multivcf_original_vcf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("multivcf_original")
    vcf_path = setup_vcf(root_path / "vcf_path" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=1>
    #CHROM	POS 	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1	f4.mom	f4.dad	f4.p1	f4.s1	f5.mom	f5.dad	f5.p1	f5.s1
    1	    865582	.	C	T	.	    .   	EFF=SYN	GT  	1/1 	0/0 	0/1	    0/1 	1/1 	0/0 	0/1 	0/1 	1/1 	0/0	    0/1 	0/1 	1/1 	0/0 	0/1	    0/1 	1/1	    0/0 	1/0	    0/1
    1	    865583	.	G	A	.	    .   	EFF=SYN	GT  	0/0 	1/1 	0/1	    0/1 	0/0 	1/1 	1/0 	0/1 	0/0 	1/1	    0/1 	0/1 	0/0 	1/1 	0/1	    0/1 	0/0	    1/1 	1/0	    0/1
    1	    865624	.	G	A	.	    .   	EFF=MIS	GT  	1/0 	0/0 	0/1	    0/0 	1/0 	0/0 	0/1 	0/0 	1/0 	0/0	    0/1 	0/0 	1/0 	0/0 	1/0	    0/0 	1/0	    0/0 	1/0	    0/0
    1	    865627	.	G	A	.	    .   	EFF=MIS	GT  	0/0 	1/0 	0/1	    0/0 	0/0 	1/0 	0/1 	0/0 	0/0 	1/1	    0/1 	1/0 	0/0 	1/1 	1/0	    0/0 	0/0	    1/1 	1/0	    1/0
    1	    865664	.	G	A	.	    .   	EFF=SYN	GT  	0/1 	0/0 	0/1	    0/0 	0/1 	0/0 	0/0 	0/1 	0/1 	0/0	    0/1 	0/0 	0/1 	0/0 	0/1	    0/0 	0/1	    0/0 	0/0	    0/1
    1	    865691	.	C	T	.	    .   	EFF=MIS	GT  	1/0 	1/0 	0/1	    0/0 	1/0 	1/0 	0/1 	0/0 	1/0 	1/1	    0/1 	0/1 	1/0 	1/1 	1/0	    1/0 	1/0	    1/1 	0/1	    0/1
    """)

    return vcf_path


@pytest.mark.parametrize(
    "multivcf_files",
    [
        ["multivcf_split1_vcf", "multivcf_split2_vcf"],
        ["multivcf_original_vcf"],
    ],
)
def test_vcf_loader_multi(
    request: pytest.FixtureRequest,
    multivcf_files: list[str],
    multivcf_original_vcf: Path,
    multivcf_original_ped: Path,
    gpf_instance: GPFInstance
) -> None:
    # pylint: disable=too-many-locals,invalid-name

    multivcf_files = [
        str(request.getfixturevalue(f)) for f in multivcf_files
    ]

    families = FamiliesLoader(str(multivcf_original_ped)).load()
    families_multi = FamiliesLoader(str(multivcf_original_ped)).load()

    multi_vcf_loader = VcfLoader(
        families_multi, multivcf_files,
        gpf_instance.reference_genome,
        fill_missing_ref=False
    )
    assert multi_vcf_loader is not None
    # for sv, fvs in multi_vcf_loader.full_variants_iterator():
    #     print(sv, fvs)

    single_vcf = str(multivcf_original_vcf)
    single_loader = VcfLoader(
        families, [single_vcf], gpf_instance.reference_genome
    )
    assert single_loader is not None

    single_it = single_loader.full_variants_iterator()
    multi_it = multi_vcf_loader.full_variants_iterator()

    for s, m in zip(single_it, multi_it):
        assert s[0] == m[0]
        assert len(s[1]) == 5
        assert len(m[1]) == 5

        s_gt_f1 = s[1][0].gt
        m_gt_f1 = m[1][0].gt
        assert all((s_gt_f1 == m_gt_f1).flatten())

        s_gt_f2 = s[1][0].gt
        m_gt_f2 = m[1][0].gt
        assert all((s_gt_f2 == m_gt_f2).flatten())

        s_gt_f3 = s[1][0].gt
        m_gt_f3 = m[1][0].gt
        assert all((s_gt_f3 == m_gt_f3).flatten())

        s_gt_f4 = s[1][0].gt
        m_gt_f4 = m[1][0].gt
        assert all((s_gt_f4 == m_gt_f4).flatten())

        s_gt_f5 = s[1][0].gt
        m_gt_f5 = m[1][0].gt
        assert all((s_gt_f5 == m_gt_f5).flatten())


@pytest.fixture
def multivcf_missing1(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("multivcf_missing1")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	f1.mom	f1.dad	f1.p1	f1.s1	f2.mom	f2.dad	f2.p1	f2.s1	f3.mom	f3.dad	f3.p1	f3.s1
    1	    865582	.	C	T	.	    .	    EFF=SYN	GT  	1/1 	0/0 	0/1 	0/1	    1/1 	0/0 	0/1 	0/1 	1/1 	0/0 	0/1 	0/1
    1	    865627	.	G	A	.	    .	    EFF=MIS	GT  	0/0 	1/0 	0/1 	0/0	    0/0 	1/0 	0/1 	0/0 	0/0 	1/1 	0/1 	1/0
    1	    865664	.	G	A	.	    .	    EFF=SYN	GT  	0/1 	0/0 	0/1 	0/0	    0/1 	0/0 	0/0 	0/1 	0/1 	0/0 	0/1 	0/0
    1	    865691	.	C	T	.	    .	    EFF=MIS	GT  	1/0 	1/0 	0/1 	0/0	    1/0 	1/0 	0/1 	0/0 	1/0 	1/1 	0/1 	0/1
    """)
    return vcf_path


@pytest.fixture
def multivcf_missing2(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root_path = tmp_path_factory.mktemp("multivcf_missing2")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##contig=<ID=1>
    #CHROM	POS	      ID  REF	ALT	    QUAL	FILTER	INFO	FORMAT	f4.mom	f4.dad	f4.p1	f4.s1	f5.mom	f5.dad	f5.p1	f5.s1
    1	    865582	  .	  C	    T	    .   	.	    EFF=SYN	GT  	1/1 	0/0 	0/1	    0/1 	1/1	    0/0 	1/0	    0/1
    1	    865583	  .	  G	    A	    .   	.	    EFF=SYN	GT  	0/0 	1/1 	0/1	    0/1 	0/0	    1/1 	1/0 	0/1
    1	    865624	  .	  G	    A	    .   	.	    EFF=MIS	GT  	1/0 	0/0 	1/0	    0/0 	1/0	    0/0 	1/0	    0/0
    1	    865627	  .	  G	    A	    .   	.	    EFF=MIS	GT  	0/0 	1/1 	1/0	    0/0 	0/0	    1/1 	1/0	    1/0
    1	    865664	  .	  G	    A	    .   	.	    EFF=SYN	GT  	0/1 	0/0 	0/1	    0/0 	0/1	    0/0 	0/0 	0/1
    1	    865691	  .	  C     T	    .   	.	    EFF=MIS	GT  	1/0 	1/1 	1/0	    1/0 	1/0	    1/1 	0/1	    0/1
    """)
    return vcf_path


@pytest.mark.parametrize(
    "fill_mode, fill_value", [["reference", 0], ["unknown", -1]]
)
def test_multivcf_loader_fill_missing(
    fill_mode: list[str, int],
    fill_value: list[str, int],
    multivcf_ped: Path,
    multivcf_missing1: Path,
    multivcf_missing2: Path,
    gpf_instance: GPFInstance
) -> None:
    # pylint: disable=too-many-locals

    multivcf_files = [
        str(multivcf_missing1),
        str(multivcf_missing2),
    ]
    families = FamiliesLoader(multivcf_ped).load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_multi_loader_fill_in_mode": fill_mode,
    }
    multi_vcf_loader = VcfLoader(
        families, multivcf_files, gpf_instance.reference_genome,
        params=params
    )

    assert multi_vcf_loader is not None
    multi_it = multi_vcf_loader.full_variants_iterator()
    svs_fvs = list(multi_it)
    print(svs_fvs)
    first_present = svs_fvs[0]
    second_missing = svs_fvs[1]
    assert next(multi_it, None) is None

    gt1_f1 = first_present[1][0].genotype
    gt1_f1_expected = np.array([[1, 1], [0, 0], [0, 1], [0, 1]], dtype=np.int8)
    gt1_f5 = first_present[1][4].genotype
    gt1_f5_expected = np.array([[1, 1], [0, 0], [1, 0], [0, 1]], dtype=np.int8)
    assert all((gt1_f1 == gt1_f1_expected).flatten())
    assert all((gt1_f5 == gt1_f5_expected).flatten())
    print(second_missing[1][0], " ", second_missing[1][0].genotype)
    print(second_missing[1][1], " ", second_missing[1][1].genotype)

    gt2_f1 = second_missing[1][0].genotype
    gt2_f2 = second_missing[1][1].genotype
    gt2_f3 = second_missing[1][2].genotype
    gt2_f5 = second_missing[1][4].genotype

    gt2_f1_f2_f3_expected = np.array([[fill_value] * 2] * 4, dtype=np.int8)
    gt2_f5_expected = np.array([[0, 0], [1, 1], [1, 0], [0, 1]], dtype=np.int8)

    assert all((gt2_f1 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f3 == gt2_f1_f2_f3_expected).flatten())
    assert all((gt2_f5 == gt2_f5_expected).flatten())
    assert svs_fvs[0][0].ref_allele.position == 865582
    assert svs_fvs[1][0].ref_allele.position == 865583
    assert svs_fvs[2][0].ref_allele.position == 865624
    assert svs_fvs[3][0].ref_allele.position == 865627
    assert svs_fvs[4][0].ref_allele.position == 865664
    assert svs_fvs[5][0].ref_allele.position == 865691


# def test_transform_vcf_genotype():
#     genotypes = [
#         [0, 0, False],
#         [0, 1, False],
#         [1, 0, False],
#         [1, 1, False],
#         [0, True],
#         [1, True],
#     ]
#     expected = np.array([
#         [0, 0, 1, 1, 0, 1],
#         [0, 1, 0, 1, -2, -2],
#         [False, False, False, False, True, True]
#     ], dtype=GenotypeType)

#     assert np.array_equal(
#         expected, VcfLoader.transform_vcf_genotypes(genotypes)
#     )


@pytest.fixture
def inheritance_trio_denovo_omission_ped(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("inheritance_trio_denovo_omission_ped")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1		    mom1		0	    0	    2	1	    mom
    f1		    dad1		0	    0	    1	1	    dad
    f1		    ch1		    dad1	mom1	2	2	    prb
    """)

    return ped_path


@pytest.fixture
def inheritance_trio_denovo_omission_vcf(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("inheritance_trio_denovo_omission_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=INH,Number=1,Type=String,Description="Inheritance">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	mom1	dad1	ch1
    1	    11515	.	T	G	.	    .   	INH=OMI	GT	    0/0 	1/0 	1/1
    1	    11523	.	T	G	.	    .   	INH=DEN	GT	    1/1 	1/1 	1/0
    1	    11524	.	T	G	.	    .   	INH=DEN	GT	    1/1 	1/1 	0/1
    """)

    return vcf_path


@pytest.mark.parametrize(
    "denovo_mode, total, unexpected_inheritance",
    [
        ("denovo", 3, {Inheritance.possible_denovo}),
        ("possible_denovo", 3, {Inheritance.denovo}),
        ("ignore", 1, {Inheritance.possible_denovo, Inheritance.denovo}),
        ("ala_bala", 3, {Inheritance.denovo}),
    ],
)
def test_vcf_denovo_mode(
    denovo_mode,
    total,
    unexpected_inheritance,
    inheritance_trio_denovo_omission_ped: Path,
    inheritance_trio_denovo_omission_vcf: Path,
    gpf_instance: GPFInstance,
) -> None:
    families = FamiliesLoader(
        f"{str(inheritance_trio_denovo_omission_ped)}"
    ).load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_denovo_mode": denovo_mode,
    }
    vcf_loader = VcfLoader(
        families,
        [f"{str(inheritance_trio_denovo_omission_vcf)}"],
        gpf_instance.reference_genome,
        params=params,
    )

    assert vcf_loader is not None
    variants = list(vcf_loader.family_variants_iterator())
    assert len(variants) == total
    for fv in variants:
        for fa in fv.alleles:
            print(fa, fa.inheritance_in_members)
            assert set(
                fa.inheritance_in_members
            ) & unexpected_inheritance == set([])


@pytest.mark.parametrize(
    "omission_mode, total, unexpected_inheritance",
    [
        ("omission", 3, {Inheritance.possible_omission}),
        ("possible_omission", 3, {Inheritance.omission}),
        ("ignore", 2, {Inheritance.possible_omission, Inheritance.omission}),
        ("ala_bala", 3, {Inheritance.omission}),
    ],
)
def test_vcf_omission_mode(
    omission_mode,
    total,
    unexpected_inheritance,
    inheritance_trio_denovo_omission_ped: Path,
    inheritance_trio_denovo_omission_vcf: Path,
    gpf_instance: GPFInstance,
) -> None:
    families = FamiliesLoader(
        f"{inheritance_trio_denovo_omission_ped}"
    ).load()
    params = {
        "vcf_include_reference_genotypes": True,
        "vcf_include_unknown_family_genotypes": True,
        "vcf_include_unknown_person_genotypes": True,
        "vcf_omission_mode": omission_mode,
    }
    vcf_loader = VcfLoader(
        families,
        [f"{inheritance_trio_denovo_omission_vcf}"],
        gpf_instance.reference_genome,
        params=params,
    )

    assert vcf_loader is not None
    variants = list(vcf_loader.family_variants_iterator())
    assert len(variants) == total
    for fv in variants:
        for fa in fv.alleles:
            print(20 * "-")
            print(fa, fa.inheritance_in_members)
            assert set(
                fa.inheritance_in_members
            ) & unexpected_inheritance == set([])


@pytest.fixture
def f1_test_ped(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("inheritance_trio_denovo_omission_ped")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1	        mom1	    0	    0	    2	1   	mom
    f1	        dad1	    0	    0	    1	1   	dad
    f1	        ch1	        dad1	mom1	2	2   	prb
    f1	        ch2	        dad1	mom1	1	1   	sib
    """)

    return ped_path


@pytest.fixture
def f1_test_vcf(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("inheritance_trio_denovo_omission_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
    ##INFO=<ID=INH,Number=1,Type=String,Description="Inheritance">
    ##contig=<ID=1>
    #CHROM	POS	    ID	REF	ALT	QUAL	FILTER	INFO	            FORMAT	mom1	dad1	ch1	  ch2
    1	    878152	.	C	T,A	.	    .	    EFF=SYN!MIS;INH=MIX	GT  	0/0 	0/1 	0/1	  0/2
    1	    901923	.	C	T,A	.	    .	    EFF=SYN!MIS;INH=UKN	GT  	./. 	./. 	./.	  ./.
    1	    905951	.	G	A,T	.	    .	    EFF=SYN!MIS;INH=MIX	GT	    0/0 	0/0	    ./.	  0/0
    1	    905957	.	C	T,A	.	    .	    EFF=SYN!MIS;INH=DEN	GT	    0/0 	0/0	    0/1	  0/0
    1	    905966	.	A	G,T	.	    .	    EFF=SYN!MIS;INH=OMI	GT	    1/1 	0/0 	0/1	  0/0
    1	    906086	.	G	A,T	.	    .	    EFF=SYN!MIS;INH=MIX	GT	    1/0 	0/0 	0/.	  0/2
    1	    906092	.	T	C,A	.	    .	    EFF=SYN!MIS;INH=OMI	GT	    1/1 	2/2 	1/1	  2/2
    """)

    return vcf_path


@pytest.mark.parametrize(
    "vcf_include_reference_genotypes,"
    "vcf_include_unknown_family_genotypes,"
    "vcf_include_unknown_person_genotypes,count",
    [
        (True, True, True, 7),
        (True, True, False, 4),
        (True, False, True, 6),
        (False, True, True, 7),
        (True, False, False, 4),
        (False, False, False, 4),
    ],
)
def test_vcf_loader_params(
    vcf_variants_loaders: Any,
    f1_test_ped: Path,
    f1_test_vcf: Path,
    vcf_include_reference_genotypes: bool,
    vcf_include_unknown_family_genotypes: bool,
    vcf_include_unknown_person_genotypes: bool,
    count: bool,
) -> None:
    params = {
        "vcf_include_reference_genotypes":
        vcf_include_reference_genotypes,
        "vcf_include_unknown_family_genotypes":
        vcf_include_unknown_family_genotypes,
        "vcf_include_unknown_person_genotypes":
        vcf_include_unknown_person_genotypes,
    }

    config = vcf_loader_data("f1_test", f1_test_ped, f1_test_vcf)

    variants_loader = vcf_variants_loaders(
        config, params=params)[0]
    variants = list(variants_loader.family_variants_iterator())
    assert len(variants) == count


@pytest.fixture
def simple_vcf_loader(gpf_instance: GPFInstance):
    def _split_all_ext(filename):
        res, ext = os.path.splitext(filename)
        while len(ext) > 0:
            res, ext = os.path.splitext(res)
        return res
    def ctor(ped: Path, vcf: Path, additional_params: Any):
        ped_filename = _split_all_ext(str(ped)) + ".ped"
        families_loader = FamiliesLoader(ped_filename)
        families = families_loader.load()
        params = additional_params
        vcf_filename = vcf

        return VcfLoader(
            families, [str(vcf_filename)],
            genome=gpf_instance.reference_genome, params=params,
        )
    return ctor


@pytest.fixture
def multi_contig_ped(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("multi_contig_ped")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1	        mom1	    0	    0	    2	1   	mom
    f1	        dad1	    0	    0	    1	1   	dad
    f1	        ch1	        dad1	mom1	2	2   	prb
    f1	        ch2	        dad1	mom1	1	1   	sib
    """)

    return ped_path


@pytest.fixture
def multi_contig_vcf(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("multi_contig_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=1>
    ##contig=<ID=2>
    ##contig=<ID=3>
    ##contig=<ID=4>
    #CHROM	POS	    ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    1   	11539	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	0/0	0/0	0/0	0/0	0/0
    1   	11540	.	T	G,A	        .	    .   	.   	GT  	0/2	0/0	0/0	0/0	0/0	0/0	0/0
    1   	11541	.	T	G,A	        .	    .   	.   	GT  	./.	./.	./.	./.	./.	./.	./.
    2   	11542	.	T	G,A	        .	    .   	.   	GT  	0/1	0/0	0/0	0/0	0/2	0/0	0/0
    3   	11543	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    3   	11544	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    3   	11545	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/1	0/0	0/0
    4   	11546	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	1/1	0/1	0/0	0/0
    4   	11547	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	0/1	0/0	0/0	1/1
    4   	11548	.	T	GA,AA,CA,CC	.	    .   	.   	GT  	2/3	2/2	2/2	2/2	2/2	2/2	2/2
    """)

    return vcf_path


@pytest.fixture
def multi_contig_vcf_gz(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("multi_contig_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=1>
    ##contig=<ID=2>
    ##contig=<ID=3>
    ##contig=<ID=4>
    #CHROM	POS	    ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    1   	11539	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	0/0	0/0	0/0	0/0	0/0
    1   	11540	.	T	G,A	        .	    .   	.   	GT  	0/2	0/0	0/0	0/0	0/0	0/0	0/0
    1   	11541	.	T	G,A	        .	    .   	.   	GT  	./.	./.	./.	./.	./.	./.	./.
    2   	11542	.	T	G,A	        .	    .   	.   	GT  	0/1	0/0	0/0	0/0	0/2	0/0	0/0
    3   	11543	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    3   	11544	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    3   	11545	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/1	0/0	0/0
    4   	11546	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	1/1	0/1	0/0	0/0
    4   	11547	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	0/1	0/0	0/0	1/1
    4   	11548	.	T	GA,AA,CA,CC	.	    .   	.   	GT  	2/3	2/2	2/2	2/2	2/2	2/2	2/2
    """)

    return vcf_path


@pytest.fixture
def multi_contig_chr_ped(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("multi_contig_chr_ped")
    ped_path = setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f	        gpa     	0	    0	    1	1   	paternal_grandfather
    f	        gma     	0	    0	    2	1   	paternal_grandmother
    f	        mom     	0	    0	    2	1   	mom
    f	        dad     	gpa	    gma	    1	1   	dad
    f	        ch1     	dad	    mom	    2	2   	prb
    f	        ch2     	dad	    mom	    2	1   	sib
    f	        ch3     	dad	    mom	    2	1   	sib
    """)

    return ped_path


@pytest.fixture
def multi_contig_chr_vcf(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("multi_contig_chr_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    ##contig=<ID=chr3>
    ##contig=<ID=chr4>
    #CHROM	POS 	ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    chr1	11539	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	0/0	0/0	0/0	0/0	0/0
    chr1	11540	.	T	G,A	        .	    .   	.   	GT  	0/2	0/0	0/0	0/0	0/0	0/0	0/0
    chr1	11541	.	T	G,A	        .	    .   	.   	GT  	./.	./.	./.	./.	./.	./.	./.
    chr2	11542	.	T	G,A	        .	    .   	.   	GT  	0/1	0/0	0/0	0/0	0/2	0/0	0/0
    chr3	11543	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3	11544	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3	11545	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/1	0/0	0/0
    chr4	11546	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	1/1	0/1	0/0	0/0
    chr4	11547	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	0/1	0/0	0/0	1/1
    chr4	11548	.	T	GA,AA,CA,CC	.	    .   	.   	GT  	2/3	2/2	2/2	2/2	2/2	2/2	2/2

    """)

    return vcf_path


@pytest.fixture
def multi_contig_chr_vcf_gz(
    tmp_path_factory: pytest.TempPathFactory
) -> Path:
    root_path = tmp_path_factory.mktemp("multi_contig_chr_vcf")
    vcf_path = setup_vcf(root_path / "vcf_data" / "in.vcf.gz", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    ##contig=<ID=chr3>
    ##contig=<ID=chr4>
    #CHROM	POS 	ID	REF	ALT	        QUAL	FILTER	INFO	FORMAT	mom	dad	ch1	ch2	ch3	gma	gpa
    chr1	11539	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	0/0	0/0	0/0	0/0	0/0
    chr1	11540	.	T	G,A	        .	    .   	.   	GT  	0/2	0/0	0/0	0/0	0/0	0/0	0/0
    chr1	11541	.	T	G,A	        .	    .   	.   	GT  	./.	./.	./.	./.	./.	./.	./.
    chr2	11542	.	T	G,A	        .	    .   	.   	GT  	0/1	0/0	0/0	0/0	0/2	0/0	0/0
    chr3	11543	.	T	G,A	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3	11544	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/0	0/0	0/0
    chr3	11545	.	T	G	        .	    .   	.   	GT  	0/0	0/0	./.	0/0	0/1	0/0	0/0
    chr4	11546	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	1/1	0/1	0/0	0/0
    chr4	11547	.	T	G	        .	    .   	.   	GT  	0/0	0/0	0/0	0/1	0/0	0/0	1/1
    chr4	11548	.	T	GA,AA,CA,CC	.	    .   	.   	GT  	2/3	2/2	2/2	2/2	2/2	2/2	2/2

    """)

    return vcf_path


@pytest.mark.parametrize("input_filename, params", [
    (["multi_contig_ped", "multi_contig_vcf"], {"add_chrom_prefix": "chr"}),
    (["multi_contig_chr_ped", "multi_contig_chr_vcf"], {"del_chrom_prefix": "chr"}),
])
def test_chromosomes_have_adjusted_chrom(
    request: pytest.FixtureRequest,
    simple_vcf_loader: Callable[[Path, Path, dict[str, str]], VcfLoader],
    input_filename: list[str],
    params: dict[str, str]
) -> None:
    ped = request.getfixturevalue(input_filename[0])
    vcf = request.getfixturevalue(input_filename[1])
    loader = simple_vcf_loader(ped, vcf, params)

    prefix = params.get("add_chrom_prefix", "")
    assert loader.chromosomes == [f"{prefix}1", f"{prefix}2", f"{prefix}3",
                                  f"{prefix}4"]


@pytest.mark.parametrize("input_filename, params", [
    (["multi_contig_ped", "multi_contig_vcf"], {"add_chrom_prefix": "chr"}),
    (["multi_contig_chr_ped", "multi_contig_chr_vcf"], {"del_chrom_prefix": "chr"}),
])
def test_variants_have_adjusted_chrom(
    request: pytest.FixtureRequest,
    simple_vcf_loader: Callable[[Path, Path, dict[str, str]], VcfLoader],
    input_filename: list[str],
    params: dict[str, str]
) -> None:
    ped = request.getfixturevalue(input_filename[0])
    vcf = request.getfixturevalue(input_filename[1])
    loader = simple_vcf_loader(ped, vcf, params)
    is_add = "add_chrom_prefix" in params

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    for summary_variant, _ in variants:
        if is_add:
            assert summary_variant.chromosome.startswith("chr")
        else:
            assert not summary_variant.chromosome.startswith("chr")


@pytest.mark.parametrize("input_filename, params", [
    (["multi_contig_ped", "multi_contig_vcf_gz"], {"add_chrom_prefix": "chr"}),
    (["multi_contig_chr_ped", "multi_contig_chr_vcf_gz"], {"del_chrom_prefix": "chr"}),
])
def test_reset_regions_with_adjusted_chrom(
    request: pytest.FixtureRequest,
    simple_vcf_loader: Callable[[Path, Path, dict[str, str]], VcfLoader],
    input_filename: list[str],
    params: dict[str, str]
) -> None:
    ped = request.getfixturevalue(input_filename[0])
    vcf = request.getfixturevalue(input_filename[1])

    loader = simple_vcf_loader(ped, vcf, params)
    prefix = params.get("add_chrom_prefix", "")
    regions = [f"{prefix}1", f"{prefix}2"]

    loader.reset_regions(regions)

    variants = list(loader.full_variants_iterator())
    assert len(variants) > 0
    unique_chroms = np.unique([sv.chromosome for sv, _ in variants])
    assert (unique_chroms == regions).all()


# @pytest.mark.parametrize(
#     "fill_mode, fill_value", [["reference", 0], ["unknown", -1]]
# )
# def test_multivcf_loader_handle_all_unknown(
#     fixture_dirname, fill_mode, fill_value, gpf_instance_2013
# ):
#     ped_file = fixture_dirname("backends/multivcf.ped")

#     multivcf_files = [
#         fixture_dirname("backends/multivcf_unknown1.vcf"),
#         fixture_dirname("backends/multivcf_unknown2.vcf"),
#     ]
#     families = FamiliesLoader(ped_file).load()
#     params = {
#         "vcf_include_reference_genotypes": True,
#         "vcf_include_unknown_family_genotypes": True,
#         "vcf_include_unknown_person_genotypes": True,
#         "vcf_multi_loader_fill_in_mode": fill_mode,
#     }
#     multi_vcf_loader = VcfLoader(
#         families, multivcf_files, gpf_instance_2013.reference_genome,
#         params=params
#     )

#     assert multi_vcf_loader is not None
#     vs = list(multi_vcf_loader.family_variants_iterator())
#     assert len(vs) == 30


def test_collect_filenames_local(fixture_dirname):
    vcf_filenames = [fixture_dirname("backends/multivcf_split[vc].vcf")]

    params = {
        "vcf_chromosomes": "1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;X;Y"
    }
    all_filenames, _ = VcfLoader._collect_filenames(params, vcf_filenames)

    assert len(all_filenames) == 2
    assert all_filenames[0] == fixture_dirname("backends/multivcf_split1.vcf")
    assert all_filenames[1] == fixture_dirname("backends/multivcf_split2.vcf")


def test_collect_filenames_s3(fixture_dirname, s3_filesystem,
                              s3_tmp_bucket_url, mocker):
    s3_filesystem.put(fixture_dirname("backends/multivcf_split1.vcf"),
                      f"{s3_tmp_bucket_url}/dir/multivcf_split1.vcf")
    s3_filesystem.put(fixture_dirname("backends/multivcf_split2.vcf"),
                      f"{s3_tmp_bucket_url}/dir/multivcf_split2.vcf")

    mocker.patch("dae.variants_loaders.vcf.loader.url_to_fs",
                 return_value=(s3_filesystem, None))

    vcf_filenames = ["s3://test-bucket/dir/multivcf_split[vc].vcf"]

    params = {
        "vcf_chromosomes": "1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;X;Y"
    }
    all_filenames, _ = VcfLoader._collect_filenames(params, vcf_filenames)

    assert len(all_filenames) == 2
    assert all_filenames[0] == "s3://test-bucket/dir/multivcf_split1.vcf"
    assert all_filenames[1] == "s3://test-bucket/dir/multivcf_split2.vcf"


def test_family_variants(resources_dir, gpf_instance_2013):
    ped_filename = str(resources_dir / "simple_family.ped")
    families = FamiliesLoader(ped_filename).load()

    vcf_loader = VcfLoader(
        families,
        [str(resources_dir / "simple_variants.vcf")],
        gpf_instance_2013.reference_genome,
    )
    variants = list(vcf_loader.full_variants_iterator())
    assert len(variants) == 10

    family_variants = [v[1] for v in variants]
    exp_num_fam_variants_and_alleles = [
        # (num variants, num alleles)
        (0, 0),  # 1st variant is not found in any individual
        (1, 2),  # only the 2nd alt allele of the second variant is found
        (0, 0),  # the 3rd variant is unknown across the board
        (1, 3),  # the 4th variant is found in 1 individual (similar to 2nd)
        (0, 0),  # the 5th, 6th and 7th have missing values
        (0, 0),
        (0, 0),
        (1, 2),  # the 8th is a normal-looking variant
        (1, 2),  # the 9th is a normal-looking variant
        (1, 4),  # the 10th is found in all individuals
    ]

    for i, fam_variants in enumerate(family_variants):
        exp_num_variants, exp_num_alleles = exp_num_fam_variants_and_alleles[i]
        assert len(fam_variants) == exp_num_variants
        assert sum(len(fv.alleles) for fv in fam_variants) == exp_num_alleles
