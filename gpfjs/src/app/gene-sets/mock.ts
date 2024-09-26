const hierarchy = [{
  datasetId: 'SPARK_genotypes',
  datasetName: 'SPARK Genotypes',
  personSetCollections: [
    {
      personSetCollectionId: 'phenotype',
      personSetCollectionName: 'Phenotype',
      personSetCollectionLegend: [
        {
          id: 'autism',
          name: 'autism',
          values: [
            'affected'
          ],
          color: '#ff2121'
        },
        {
          id: 'unaffected',
          name: 'unaffected',
          values: [
            'unaffected'
          ],
          color: '#ffffff'
        }
      ]
    }
  ]
  ,
  children: [
    {
      datasetId: 'SFARI_SPARK_WES_1_CSHL',
      datasetName: 'SPARK CSHL WES batch 1',
      personSetCollections: [
        {
          personSetCollectionId: 'phenotype',
          personSetCollectionName: 'Phenotype',
          personSetCollectionLegend: [
            {
              id: 'autism',
              name: 'autism',
              values: [
                'affected'
              ],
              color: '#ff2121'
            },
            {
              id: 'unaffected',
              name: 'unaffected',
              values: [
                'unaffected'
              ],
              color: '#ffffff'
            }
        ],
        }
      ],
      children: null
    },
    {
      datasetId: 'iWES_v2_genotypes',
      datasetName: 'SPARK Consortium iWES v2',
      personSetCollections: [
        {
        personSetCollectionId: '',
        personSetCollectionName: '',
        personSetCollectionLegend: [],
        }
      ],
      children: null
    }
  ],
},
{
  datasetId: 'SFARI_SVIP_WES_1_liftover',
  datasetName: 'Simons Searchlight WES liftover',
  PersonSetCollections: [
    {
      personSetCollectionId: 'phenotype',
      personSetCollectionName: 'Phenotype',
      personSetCollectionLegend: [
        {
          "id": "aspergers_disorder",
          "name": "aspergers disorder",
          "values": [
              "aspergers-disorder"
          ],
          "color": "#9d8c00"
      },
      {
          "id": "autistic_disorder",
          "name": "autistic disorder",
          "values": [
              "autistic-disorder"
          ],
          "color": "#ff2121"
      },
      {
          "id": "non_spectrum_dx",
          "name": "non-spectrum dx",
          "values": [
              "non-spectrum-dx"
          ],
          "color": "#aca8cf"
      },
      {
          "id": "pdd_nos_atypical_autism",
          "name": "PDD-NOS atypical autism",
          "values": [
              "pdd-nos-atypical-autism"
          ],
          "color": "#0200a2"
      },
      {
          "id": "no_diagnosis",
          "name": "no diagnosis",
          "values": [
              "no-diagnosis"
          ],
          "color": "#ffffff"
      }
      ]
    },
    {
      personSetCollectionId: 'status_16p',
      personSetCollectionName: '16p status',
      personSetCollectionLegend: [
        {
          "id": "deletion",
          "name": "deletion",
          "values": [
              "deletion"
          ],
          "color": "#ff2121"
      },
      {
          "id": "duplication",
          "name": "duplication",
          "values": [
              "duplication"
          ],
          "color": "#ac6bad"
      },
      {
          "id": "triplication",
          "name": "triplication",
          "values": [
              "triplication"
          ],
          "color": "#ffe502"
      },
      {
          "id": "negative",
          "name": "negative",
          "values": [
              "negative"
          ],
          "color": "#ffffff"
      }
      ]
    }
  ],
  children: null
}];

export const mockResponse =
[
  {
    desc: 'Autism Gene Sets',
    name: 'autism',
    format: [
      'key',
      ' (',
      'count',
      '): ',
      'desc'
    ],
    types: []
  },
  {
    desc: 'Denovo',
    name: 'denovo',
    format: [
      'key',
      ' (|count|)'
    ],
    types: hierarchy
  }
];


