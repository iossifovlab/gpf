# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

from dae.genomic_resources.implementations.gene_models_impl import (
    GeneModelsImpl,
)
from dae.genomic_resources.testing import (
    build_filesystem_test_resource,
    convert_to_tab_separated,
    setup_directories,
)
from dae.task_graph.executor import task_graph_run
from dae.task_graph.graph import TaskGraph


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
