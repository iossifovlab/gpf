# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest
from dae.genomic_resources.implementations.gene_models_impl import (
    GeneModelsImpl,
    GeneModelsStatistics,
    StatisticsData,
)
from dae.genomic_resources.testing import (
    build_filesystem_test_resource,
    build_inmemory_test_resource,
    convert_to_tab_separated,
    setup_directories,
)
from dae.task_graph.executor import task_graph_run
from dae.task_graph.graph import TaskGraph
from jinja2 import Template

# this content follows the 'refflat' gene model format
REFFLAT_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
TP53      tx1  1     +      10      100   12       95     3         10,50,70   15,60,100
TP53      tx2  1     +      10      100   12       95     2         10,70      15,100
POGZ      tx3  17    +      10      100   12       95     3         10,50,70   15,60,100
BRCA1     tx4  1     -      200     300   210      290    2         200,250    220,300
NONCOD    tx5  2     +      50      150   150      150    2         50,100     80,150
"""  # noqa


def test_gene_models_impl_simple(tmp_path: pathlib.Path) -> None:
    # Example from: https://www.gencodegenes.org/pages/data_format.html
    setup_directories(
        tmp_path, {
            "genomic_resource.yaml":
                "{type: gene_models, filename: gencode.txt, format: gtf}",
            "gencode.txt": convert_to_tab_separated(textwrap.dedent("""
chr19  HAVANA  gene         405438  409170  .  -  .  gene_id||"ENSG00000183186.7";gene_type||"protein_coding";gene_name||"C2CD4C";level||2;havana_gene||"OTTHUMG00000180534.3";
chr19  HAVANA  transcript   405438  409170  .  -  .  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||level||2;||protein_id||"ENSP00000328677.4";||transcript_support_level||"2";||tag||"basic";||tag||"appris_principal_1";||tag||"CCDS";||ccdsid||"CCDS45890.1";||havana_gene||"OTTHUMG00000180534.3";||havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  exon         409006  409170  .  -  .  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||1;||exon_id||"ENSE00001322986.5";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  exon         405438  408401  .  -  .  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||2;||exon_id||"ENSE00001290344.6";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  CDS          407099  408361  .  -  0  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||2;||exon_id||"ENSE00001290344.6";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  start_codon  408359  408361  .  -  0  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||2;||exon_id||"ENSE00001290344.6";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  stop_codon   407096  407098  .  -  0  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||2;||exon_id||"ENSE00001290344.6";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  UTR          409006  409170  .  -  .  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||1;||exon_id||"ENSE00001322986.5";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  UTR          405438  407098  .  -  .  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||2;||exon_id||"ENSE00001290344.6";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
chr19  HAVANA  UTR          408362  408401  .  -  .  gene_id||"ENSG00000183186.7";transcript_id||"ENST00000332235.7";||gene_type||"protein_coding";||gene_name||"C2CD4C";||transcript_type||"protein_coding";||transcript_name||"C2CD4C-001";||exon_number||2;||exon_id||"ENSE00001290344.6";||level||2;protein_id||"ENSP00000328677.4";transcript_support_level||"2";tag||"basic";tag||"appris_principal_1";tag||"CCDS";ccdsid||"CCDS45890.1";havana_gene||"OTTHUMG00000180534.3";havana_transcript||"OTTHUMT00000451789.3";
""")),  # noqa: E501
        })
    res = build_filesystem_test_resource(tmp_path)
    assert res is not None

    gene_models_impl = GeneModelsImpl(res)
    assert gene_models_impl is not None

    graph = TaskGraph()
    tasks = gene_models_impl.add_statistics_build_tasks(graph)
    assert len(tasks) == 1

    task_graph_run(graph)
    assert gene_models_impl.get_statistics() is not None


def test_gene_models_impl_files_property() -> None:
    """Test that files property returns correct set of files."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    gene_models_impl = GeneModelsImpl(res)
    files = gene_models_impl.files

    assert isinstance(files, set)
    assert "genes.txt" in files
    assert len(files) == 1


def test_gene_models_impl_files_with_gene_mapping() -> None:
    """Test that files property includes gene mapping file."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat, "
                "gene_mapping: mapping.txt}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
            "geneMap.txt": convert_to_tab_separated("""
                from   to
                TP53   tumor_protein_p53
            """),
        })

    gene_models_impl = GeneModelsImpl(res)
    files = gene_models_impl.files

    assert isinstance(files, set)
    assert "genes.txt" in files
    assert "mapping.txt" in files
    assert len(files) == 2


def test_gene_models_impl_statistics_calculation() -> None:
    """Test statistics calculation with mixed coding and non-coding genes."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    gene_models_impl = GeneModelsImpl(res)

    graph = TaskGraph()
    tasks = gene_models_impl.add_statistics_build_tasks(graph)
    assert len(tasks) == 1

    task_graph_run(graph)
    stats = gene_models_impl.get_statistics()

    assert stats is not None
    assert stats.resource_id == res.resource_id

    # Check global statistics
    assert stats.global_statistic.transcript_number == 5  # 5 transcripts
    # 4 coding transcripts
    assert stats.global_statistic.protein_coding_transcript_number == 4
    assert stats.global_statistic.gene_number == 4  # TP53, POGZ, BRCA1, NONCOD
    # TP53, POGZ, BRCA1
    assert stats.global_statistic.protein_coding_gene_number == 3

    # Check chromosome statistics
    assert stats.chromosome_count == 3  # chr1, chr2, chr17

    assert "1" in stats.chrom_statistics
    chr1_stats = stats.chrom_statistics["1"]
    assert chr1_stats.transcript_number == 3  # tx1, tx2, tx4
    assert chr1_stats.protein_coding_transcript_number == 3
    assert chr1_stats.gene_number == 2  # TP53, BRCA1
    assert chr1_stats.protein_coding_gene_number == 2

    assert "17" in stats.chrom_statistics
    chr17_stats = stats.chrom_statistics["17"]
    assert chr17_stats.transcript_number == 1  # tx3
    assert chr17_stats.protein_coding_transcript_number == 1
    assert chr17_stats.gene_number == 1  # POGZ
    assert chr17_stats.protein_coding_gene_number == 1

    assert "2" in stats.chrom_statistics
    chr2_stats = stats.chrom_statistics["2"]
    assert chr2_stats.transcript_number == 1  # tx5
    assert chr2_stats.protein_coding_transcript_number == 0  # non-coding
    assert chr2_stats.gene_number == 1  # NONCOD
    assert chr2_stats.protein_coding_gene_number == 0


def test_statistics_data_serialization_deserialization() -> None:
    """Test StatisticsData serialization and deserialization."""
    stats = GeneModelsStatistics(
        resource_id="test_resource",
        chromosome_count=2,
        global_statistic=StatisticsData(
            transcript_number=100,
            protein_coding_transcript_number=80,
            gene_number=50,
            protein_coding_gene_number=40,
        ),
        chrom_statistics={
            "chr1": StatisticsData(
                transcript_number=60,
                protein_coding_transcript_number=50,
                gene_number=30,
                protein_coding_gene_number=25,
            ),
            "chr2": StatisticsData(
                transcript_number=40,
                protein_coding_transcript_number=30,
                gene_number=20,
                protein_coding_gene_number=15,
            ),
        },
    )

    # Serialize
    serialized = stats.serialize()
    assert isinstance(serialized, str)
    assert "resource_id: test_resource" in serialized
    assert "chromosome_count: 2" in serialized
    assert "transcript_number: 100" in serialized

    # Deserialize
    deserialized = GeneModelsStatistics.deserialize(serialized)

    assert deserialized.resource_id == "test_resource"
    assert deserialized.chromosome_count == 2
    assert deserialized.global_statistic.transcript_number == 100
    assert deserialized.global_statistic.protein_coding_transcript_number == 80
    assert deserialized.global_statistic.gene_number == 50
    assert deserialized.global_statistic.protein_coding_gene_number == 40

    assert "chr1" in deserialized.chrom_statistics
    chr1 = deserialized.chrom_statistics["chr1"]
    assert chr1.transcript_number == 60
    assert chr1.protein_coding_transcript_number == 50
    assert chr1.gene_number == 30
    assert chr1.protein_coding_gene_number == 25

    assert "chr2" in deserialized.chrom_statistics
    chr2 = deserialized.chrom_statistics["chr2"]
    assert chr2.transcript_number == 40
    assert chr2.protein_coding_transcript_number == 30
    assert chr2.gene_number == 20
    assert chr2.protein_coding_gene_number == 15


def test_gene_models_impl_get_info() -> None:
    """Test that get_info returns HTML content."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    gene_models_impl = GeneModelsImpl(res)

    # Build statistics first
    graph = TaskGraph()
    gene_models_impl.add_statistics_build_tasks(graph)
    task_graph_run(graph)

    info = gene_models_impl.get_info()
    assert isinstance(info, str)
    assert len(info) > 0
    assert "genes.txt" in info


def test_gene_models_impl_get_statistics_info() -> None:
    """Test that get_statistics_info returns HTML content."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    gene_models_impl = GeneModelsImpl(res)

    # Build statistics first
    graph = TaskGraph()
    gene_models_impl.add_statistics_build_tasks(graph)
    task_graph_run(graph)

    stats_info = gene_models_impl.get_statistics_info()
    assert isinstance(stats_info, str)
    assert len(stats_info) > 0


def test_gene_models_impl_calc_info_hash() -> None:
    """Test calc_info_hash returns bytes."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    gene_models_impl = GeneModelsImpl(res)
    info_hash = gene_models_impl.calc_info_hash()

    assert isinstance(info_hash, bytes)
    assert info_hash == b"placeholder"


def test_gene_models_impl_calc_statistics_hash() -> None:
    """Test calc_statistics_hash returns consistent hash."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    gene_models_impl = GeneModelsImpl(res)
    stats_hash = gene_models_impl.calc_statistics_hash()

    assert isinstance(stats_hash, bytes)
    assert len(stats_hash) > 0

    # Hash should be consistent across calls
    stats_hash2 = gene_models_impl.calc_statistics_hash()
    assert stats_hash == stats_hash2


def test_gene_models_impl_get_statistics_before_build() -> None:
    """Test that get_statistics raises exception before statistics are built."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    gene_models_impl = GeneModelsImpl(res)

    # Should raise FileNotFoundError when statistics file doesn't exist
    with pytest.raises(FileNotFoundError):
        gene_models_impl.get_statistics()


def test_gene_models_impl_statistics_caching() -> None:
    """Test that get_statistics caches results."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    gene_models_impl = GeneModelsImpl(res)

    # Build statistics
    graph = TaskGraph()
    gene_models_impl.add_statistics_build_tasks(graph)
    task_graph_run(graph)

    # First call
    stats1 = gene_models_impl.get_statistics()
    assert stats1 is not None

    # Second call should return cached result
    stats2 = gene_models_impl.get_statistics()
    assert stats2 is stats1  # Should be same object


def test_gene_models_impl_get_template() -> None:
    """Test that get_template returns a Jinja2 Template."""
    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(REFFLAT_CONTENT),
        })

    gene_models_impl = GeneModelsImpl(res)
    template = gene_models_impl.get_template()

    assert isinstance(template, Template)


def test_gene_models_impl_only_noncoding_transcripts() -> None:
    """Test statistics with only non-coding transcripts."""
    noncoding_content = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
LINC1     tx1  1     +      10      100   100      100    2         10,50      40,100
LINC2     tx2  2     -      200     300   300      300    1         200        300
"""  # noqa

    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(noncoding_content),
        })

    gene_models_impl = GeneModelsImpl(res)

    graph = TaskGraph()
    gene_models_impl.add_statistics_build_tasks(graph)
    task_graph_run(graph)

    stats = gene_models_impl.get_statistics()
    assert stats is not None
    assert stats.global_statistic.transcript_number == 2
    assert stats.global_statistic.protein_coding_transcript_number == 0
    assert stats.global_statistic.gene_number == 2
    assert stats.global_statistic.protein_coding_gene_number == 0


def test_gene_models_impl_empty_gene_models() -> None:
    """Test statistics with empty gene models file."""
    empty_content = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
"""  # noqa

    res = build_inmemory_test_resource(
        content={
            "genomic_resource.yaml":
                "{type: gene_models, filename: genes.txt, format: refflat}",
            "genes.txt": convert_to_tab_separated(empty_content),
        })

    gene_models_impl = GeneModelsImpl(res)

    graph = TaskGraph()
    gene_models_impl.add_statistics_build_tasks(graph)
    task_graph_run(graph)

    stats = gene_models_impl.get_statistics()
    assert stats is not None
    assert stats.global_statistic.transcript_number == 0
    assert stats.global_statistic.protein_coding_transcript_number == 0
    assert stats.global_statistic.gene_number == 0
    assert stats.global_statistic.protein_coding_gene_number == 0
    assert stats.chromosome_count == 0
