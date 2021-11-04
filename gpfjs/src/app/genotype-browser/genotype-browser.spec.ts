import { BrowserQueryFilter, GenomicScore, PersonSetCollection } from './genotype-browser';

describe('BrowserQueryFilter', () => {
  it('should create from json', () => {
    const browserQueryFilterMock = new BrowserQueryFilter(
      'name1', ['gene2', 'gene3'], ['effectType4', 'effectType5'],
      ['gender6', 'gender7'], new PersonSetCollection('id8', ['9', '10']),
      ['studyType11', 'studyType12'], ['variant13', 'variant14']
    );

    const browserQueryFilterMockFromJson = BrowserQueryFilter.fromJson(
      {
        datasetId: 'name1', geneSymbols: [ 'gene2', 'gene3' ], effectTypes: [ 'effectType4', 'effectType5' ],
        gender: [ 'gender6', 'gender7' ], peopleGroup: { id: 'id8', checkedValues: [ '9', '10' ] },
        studyTypes: [ 'studyType11', 'studyType12' ], variantTypes: [ 'variant13', 'variant14' ]
      }
    );

    expect(browserQueryFilterMock).toEqual(browserQueryFilterMockFromJson);
  });
});

describe('PersonSetCollection', () => {
  it('should create from json', () => {
    expect(new PersonSetCollection('id1', ['check1', 'check2'])).toEqual(PersonSetCollection.fromJson({
      id: 'id1',
      checkedValues: [ 'check1', 'check2' ]
    }));
  });
});

describe('GenomicScore', () => {
  it('should create from json', () => {
    expect(new GenomicScore('1', 2, 3)).toEqual(GenomicScore.fromJson({
      metric: '1', rangeStart: 2, rangeEnd: 3
    }));
  });

  it('should create from json array', () => {
    expect([new GenomicScore('1', 2, 3), new GenomicScore('4', 5, 6)]).toEqual(GenomicScore.fromJsonArray([
      { metric: '1', rangeStart: 2, rangeEnd: 3 },
      { metric: '4', rangeStart: 5, rangeEnd: 6 }
    ]
    ));
  });
});
