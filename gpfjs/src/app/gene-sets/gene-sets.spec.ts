import { DenovoPersonSetCollection, GeneSet, GeneSetsCollection, GeneSetType } from './gene-sets';

describe('GeneSets', () => {
  it('should create GeneSetsCollection from JSON method', () => {
    const geneSetsCollectionMock1 = new GeneSetsCollection('name1', 'desc2', [
      new GeneSetType(
        'datasetId3',
        'datasetName4',
        [new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6', [])]
      ),
      new GeneSetType(
        'datasetId9',
        'datasetName10',
        [new DenovoPersonSetCollection('personSetCollectionId11', 'personSetCollectionName12', [])]
      )
    ]);

    const geneSetsCollectionMockFromJSON1 = GeneSetsCollection.fromJson({
      name: 'name1', desc: 'desc2',
      types: [
        new GeneSetType('datasetId3', 'datasetName4', [
          new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6', [])
        ]),
        new GeneSetType('datasetId9', 'datasetName10', [
          new DenovoPersonSetCollection('personSetCollectionId11', 'personSetCollectionName12', [])
        ])
       ]
    });
    expect(geneSetsCollectionMock1).toStrictEqual(geneSetsCollectionMockFromJSON1);
  });

  it('should create GeneSetsCollection from JSON array method', () => {
    const geneSetsCollectionMock1 = [
      new GeneSetsCollection('name1', 'desc2',
        [
          new GeneSetType(
            'datasetId3',
            'datasetName4',
            [new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6', [])]
          ),
          new GeneSetType(
            'datasetId9',
            'datasetName10',
            [new DenovoPersonSetCollection('personSetCollectionId11', 'personSetCollectionName12', [])]
          )
        ]
      ),
      new GeneSetsCollection('name15', 'desc16',
        [
          new GeneSetType(
            'datasetId17',
            'datasetName18',
            [new DenovoPersonSetCollection('personSetCollectionId19', 'personSetCollectionName20', [])]
          ),
          new GeneSetType(
            'datasetId23',
            'datasetName24',
            [new DenovoPersonSetCollection('personSetCollectionId25', 'personSetCollectionName26', [])]
          )
        ]
      )
    ];

    const geneSetsCollectionFromJSONArray1 = GeneSetsCollection.fromJsonArray([
      {
        name: 'name1', desc: 'desc2',
        types: [
          new GeneSetType('datasetId3', 'datasetName4', [
            new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6', [])
          ]),
          new GeneSetType('datasetId9', 'datasetName10', [
            new DenovoPersonSetCollection('personSetCollectionId11', 'personSetCollectionName12', [])
          ])
        ]
      },
      {
        name: 'name15', desc: 'desc16',
        types: [
          new GeneSetType('datasetId17', 'datasetName18', [
            new DenovoPersonSetCollection('personSetCollectionId19', 'personSetCollectionName20', [])
          ]),
          new GeneSetType('datasetId23', 'datasetName24', [
            new DenovoPersonSetCollection('personSetCollectionId25', 'personSetCollectionName26', [])
          ])
        ]
      }
    ]);

    expect(geneSetsCollectionMock1).toStrictEqual(geneSetsCollectionFromJSONArray1);
  });

  it('should create GeneSet from JSON method', () => {
    const geneSetMock1 = new GeneSet('name1', 1, 'desc1', 'download1');
    const geneSetMockFromJSON1 = GeneSet.fromJson({
      name: 'name1',
      count: 1,
      desc: 'desc1',
      download: 'download1'
    });
    expect(geneSetMock1).toStrictEqual(geneSetMockFromJSON1);
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
    expect(geneSetMock1).toStrictEqual(geneSetMockFromJSONArray1);
  });

  it('should create GeneSetType from JSON', () => {
    const geneSetTypeMock1 = new GeneSetType('datasetId1', 'datasetName2', [
      new DenovoPersonSetCollection('personSetCollectionId3', 'personSetCollectionName4', [])
    ]);

    const geneSetTypeMockFromJSON1 = GeneSetType.fromJson(
      new GeneSetType('datasetId1', 'datasetName2', [
        new DenovoPersonSetCollection('personSetCollectionId3', 'personSetCollectionName4', [])
      ])
    );

    expect(geneSetTypeMock1).toStrictEqual(geneSetTypeMockFromJSON1);
  });

  it('should create GeneSetType from JSON array', () => {
    const geneSetTypeArrayMock1 = [
      new GeneSetType('datasetId1', 'datasetName2', [
        new DenovoPersonSetCollection('personSetCollectionId3', 'personSetCollectionName4', [])
      ]),
      new GeneSetType('datasetId7', 'datasetName8', [
        new DenovoPersonSetCollection('personSetCollectionName10', 'personSetCollectionName10', [])
      ])
    ];

    const geneSetTypeMockFromJSONArray1 = GeneSetType.fromJsonArray([
      new GeneSetType('datasetId1', 'datasetName2', [
        new DenovoPersonSetCollection('personSetCollectionId3', 'personSetCollectionName4', [])
      ]),
      new GeneSetType('datasetId7', 'datasetName8', [
        new DenovoPersonSetCollection('personSetCollectionName10', 'personSetCollectionName10', [])
      ])
    ]);

    expect(geneSetTypeArrayMock1).toStrictEqual(geneSetTypeMockFromJSONArray1);
  });
});
