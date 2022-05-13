import { GeneSet, GeneSetsCollection, GeneSetType } from './gene-sets';

describe('GeneSets', () => {
  it('should create GeneSetsCollection from JSON method', () => {
    const geneSetsCollectionMock1 = new GeneSetsCollection('name1', 'desc2', [
      new GeneSetType('datasetId3', 'datasetName4', 'personSetCollectionId5', 'personSetCollectionName6',
        ['personSetCollectionLegend7', 'personSetCollectionLegend8']),
      new GeneSetType('datasetId9', 'datasetName10', 'personSetCollectionId11', 'personSetCollectionName12',
        ['personSetCollectionLegend13', 'personSetCollectionLegend14'])
    ]);

    const geneSetsCollectionMockFromJSON1 = GeneSetsCollection.fromJson({
      name: 'name1', desc: 'desc2',
      types: [{
        datasetId: 'datasetId3',
        datasetName: 'datasetName4',
        personSetCollectionId: 'personSetCollectionId5',
        personSetCollectionName: 'personSetCollectionName6',
        personSetCollectionLegend: ['personSetCollectionLegend7', 'personSetCollectionLegend8']
      }, {
        datasetId: 'datasetId9', datasetName: 'datasetName10',
        personSetCollectionId: 'personSetCollectionId11',
        personSetCollectionName: 'personSetCollectionName12',
        personSetCollectionLegend: ['personSetCollectionLegend13', 'personSetCollectionLegend14']
      }]
    });
    expect(geneSetsCollectionMock1).toEqual(geneSetsCollectionMockFromJSON1);
  });

  it('should create GeneSetsCollection from JSON array method', () => {
    const geneSetsCollectionMock1 = [
      new GeneSetsCollection('name1', 'desc2', [
        new GeneSetType('datasetId3', 'datasetName4', 'personSetCollectionId5', 'personSetCollectionName6',
          ['personSetCollectionLegend7', 'personSetCollectionLegend8']),
        new GeneSetType('datasetId9', 'datasetName10', 'personSetCollectionId11', 'personSetCollectionName12',
          ['personSetCollectionLegend13', 'personSetCollectionLegend14'])
      ]),
      new GeneSetsCollection('name15', 'desc16', [
        new GeneSetType('datasetId17', 'datasetName18', 'personSetCollectionId19', 'personSetCollectionName20',
          ['personSetCollectionLegend21', 'personSetCollectionLegend22']),
        new GeneSetType('datasetId23', 'datasetName24', 'personSetCollectionId25', 'personSetCollectionName26',
          ['personSetCollectionLegend27', 'personSetCollectionLegend28'])
      ])
    ];

    const geneSetsCollectionFromJSONArray1 = GeneSetsCollection.fromJsonArray([
      {
        name: 'name1', desc: 'desc2',
        types: [
          {
            datasetId: 'datasetId3',
            datasetName: 'datasetName4',
            personSetCollectionId: 'personSetCollectionId5',
            personSetCollectionName: 'personSetCollectionName6',
            personSetCollectionLegend: ['personSetCollectionLegend7', 'personSetCollectionLegend8']
          }, {
            datasetId: 'datasetId9',
            datasetName: 'datasetName10',
            personSetCollectionId: 'personSetCollectionId11',
            personSetCollectionName: 'personSetCollectionName12',
            personSetCollectionLegend: ['personSetCollectionLegend13', 'personSetCollectionLegend14']
          }
        ]
      },
      {
        name: 'name15', desc: 'desc16',
        types: [
          {
            datasetId: 'datasetId17',
            datasetName: 'datasetName18',
            personSetCollectionId: 'personSetCollectionId19',
            personSetCollectionName: 'personSetCollectionName20',
            personSetCollectionLegend: ['personSetCollectionLegend21', 'personSetCollectionLegend22']
          }, {
            datasetId: 'datasetId23',
            datasetName: 'datasetName24',
            personSetCollectionId: 'personSetCollectionId25',
            personSetCollectionName: 'personSetCollectionName26',
            personSetCollectionLegend: ['personSetCollectionLegend27', 'personSetCollectionLegend28']
          }
        ]
      }
    ]);

    expect(geneSetsCollectionMock1).toEqual(geneSetsCollectionFromJSONArray1);
  });

  it('should create GeneSet from JSON method', () => {
    const geneSetMock1 = new GeneSet('name1', 1, 'desc1', 'download1');
    const geneSetMockFromJSON1 = GeneSet.fromJson({
      name: 'name1',
      count: 1,
      desc: 'desc1',
      download: 'download1'
    });
    expect(geneSetMock1).toEqual(geneSetMockFromJSON1);
  });

  it('should create GeneSet from JSON method array', () => {
    const geneSetMock1 = [new GeneSet('name1', 2, 'desc3', 'download4'), new GeneSet('name5', 6, 'desc7', 'download8')];
    const geneSetMockFromJSONArray1 = GeneSet.fromJsonArray([{
      name: 'name1',
      count: 2,
      desc: 'desc3',
      download: 'download4'
    }, {
      name: 'name5',
      count: 6,
      desc: 'desc7',
      download: 'download8'
    }]);
    expect(geneSetMock1).toEqual(geneSetMockFromJSONArray1);
  });

  it('should create GeneSetType from JSON', () => {
    const geneSetTypeMock1 = new GeneSetType('datasetId1',
      'datasetName2', 'personSetCollectionId3', 'personSetCollectionName4', [
        'personSetCollectionLegend5', 'personSetCollectionLegend6'
      ]
    );

    const geneSetTypeMockFromJSON1 = GeneSetType.fromJson({
      datasetId: 'datasetId1',
      datasetName: 'datasetName2',
      personSetCollectionId: 'personSetCollectionId3',
      personSetCollectionName: 'personSetCollectionName4',
      personSetCollectionLegend: ['personSetCollectionLegend5', 'personSetCollectionLegend6']
    });

    expect(geneSetTypeMock1).toEqual(geneSetTypeMockFromJSON1);
  });

  it('should create GeneSetType from JSON array', () => {
    const geneSetTypeArrayMock1 = [
      new GeneSetType('datasetId1', 'datasetName2', 'personSetCollectionId3', 'personSetCollectionName4', [
        'personSetCollectionLegend5', 'personSetCollectionLegend6'
      ]),
      new GeneSetType('datasetId7', 'datasetName8', 'personSetCollectionId9', 'personSetCollectionName10', [
        'personSetCollectionLegend11', 'personSetCollectionLegend12'
      ])
    ];

    const geneSetTypeMockFromJSONArray1 = GeneSetType.fromJsonArray([
      {
        datasetId: 'datasetId1',
        datasetName: 'datasetName2',
        personSetCollectionId: 'personSetCollectionId3',
        personSetCollectionName: 'personSetCollectionName4',
        personSetCollectionLegend: ['personSetCollectionLegend5', 'personSetCollectionLegend6']
      },
      {
        datasetId: 'datasetId7',
        datasetName: 'datasetName8',
        personSetCollectionId: 'personSetCollectionId9',
        personSetCollectionName: 'personSetCollectionName10',
        personSetCollectionLegend: ['personSetCollectionLegend11', 'personSetCollectionLegend12']
      },
    ]);

    expect(geneSetTypeArrayMock1).toEqual(geneSetTypeMockFromJSONArray1);
  });
});
