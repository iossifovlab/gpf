export class Column {
  public id: string;
  public index?: number;
  public displayName: string;
  public defaultVisible: boolean;
  public columns: Column[];
}

export class AgpConfig {
  public columns: Column[];
}

export const rowMock = [
  ["testVal", "testVal2", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank"],
  ["testVal", "testVal2", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank"],
  ["testVal", "testVal2", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank"],
  ["testVal", "testVal2", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank"],
  ["testVal", "testVal2", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank"],
  ["testVal", "testVal2", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank"],
  ["testVal", "testVal2", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank", "blankblank"],
];

export const configMock: AgpConfig = {
  columns: [
    {
      id: 'geneSets',
      displayName: 'Gene Sets',
      defaultVisible: true,
      columns: [
        {
          id: 'autism_gene_sets',
          displayName: 'Autism Gene Sets',
          defaultVisible: true,
          columns: [
            {
              id: 'autism_candidates_from_Iossifov_PNAS_2015',
              index: 0,
              displayName: 'autism candidates from Iossifov PNAS 2015',
              defaultVisible: true,
              columns: []
            },
            {
              id: 'autism_candidates_from_Sanders_Neuron_2015',
              index: 1,
              displayName: 'autism candidates from Sanders Neuron 2015',
              defaultVisible: true,
              columns: []
            }
          ]
        },
        {
          id: 'relevant_gene_sets',
          displayName: 'Relevant Gene Sets',
          defaultVisible: true,
          columns: [
            {
              id: 'CHD8_target_genes',
              index: 2,
              displayName: 'CHD8 target genes',
              defaultVisible: true,
              columns: []
            },
            {
              id: 'chromatin_modifiers',
              index: 3,
              displayName: 'chromatin modifiers',
              defaultVisible: true,
              columns: []
            },
            {
              id: 'essential_genes',
              index: 4,
              displayName: 'essential genes',
              defaultVisible: true,
              columns: []
            },
            {
              id: 'FMRP_Darnell',
              index: 5,
              displayName: 'FMRP Darnell',
              defaultVisible: true,
              columns: []
            }
          ]
        }
      ]
    },
    {
      id: 'genomicScores',
      displayName: 'Genomic Scores',
      defaultVisible: true,
      columns: [
        {
          id: 'autism_scores',
          displayName: 'Autism Scores',
          defaultVisible: true,
          columns: [
            {
              id: 'SFARI_gene_score',
              index: 6,
              displayName: 'SFARI gene score',
              defaultVisible: true,
              columns: []
            }
          ]
        },
        {
          id: 'protection_scores',
          displayName: 'Protection Scores',
          defaultVisible: true,
          columns: [
            {
              id: 'RVIS_rank',
              index: 7,
              displayName: 'RVIS rank',
              defaultVisible: true,
              columns: []
            },
            {
              id: 'LGD_rank',
              index: 8,
              displayName: 'LGD rank',
              defaultVisible: true,
              columns: []
            },
            {
              id: 'pLI_rank',
              index: 9,
              displayName: 'pLI rank',
              defaultVisible: true,
              columns: []
            },
            {
              id: 'pRec_rank',
              index: 10,
              displayName: 'pRec rank',
              defaultVisible: true,
              columns: []
            }
          ]
        }
      ]
    },
    {
      id: 'datasets',
      displayName: 'Datasets',
      defaultVisible: true,
      columns: [
        {
          id: 'denovo_db',
          displayName: 'denovo-db v.1.6',
          defaultVisible: true,
          columns: [
            {
              id: 'acromelic_frontonasal_dysostosis',
              displayName: 'acromelic frontonasal dysostosis',
              defaultVisible: true,
              columns: [
                {
                  id: 'denovo_lgds',
                  index: 11,
                  displayName: 'LGDs',
                  defaultVisible: true,
                  columns: []
                },
                {
                  id: 'denovo_missense',
                  index: 12,
                  displayName: 'missense',
                  defaultVisible: true,
                  columns: []
                },
                {
                  id: 'denovo_intron',
                  index: 13,
                  displayName: 'intron',
                  defaultVisible: true,
                  columns: []
                }
              ]
            },
            {
              id: 'amyotrophic_lateral_sclerosis',
              displayName: 'amyotrophic lateral sclerosis',
              defaultVisible: true,
              columns: [
                {
                  id: 'denovo_lgds',
                  index: 14,
                  displayName: 'LGDs',
                  defaultVisible: true,
                  columns: []
                },
                {
                  id: 'denovo_missense',
                  index: 15,
                  displayName: 'missense',
                  defaultVisible: true,
                  columns: []
                },
                {
                  id: 'denovo_intron',
                  index: 16,
                  displayName: 'intron',
                  defaultVisible: true,
                  columns: []
                }
              ]
            }
          ]
        }
      ]
    }
  ]
};
