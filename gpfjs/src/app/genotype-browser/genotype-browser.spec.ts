import { BrowserQueryFilter, GenomicScore, PersonSetCollection, PresentInParent, PresentInParentRarity } from './genotype-browser';

describe('BrowserQueryFilter', () => {
  it('should create from json', () => {
    const browserQueryFilterMock = new BrowserQueryFilter(
      'name1', ['gene2', 'gene3'], ['effectType4', 'effectType5'],
      ['gender6', 'gender7'], new PersonSetCollection('id8', ['9', '10']),
      ['studyType11', 'studyType12'], ['variant13', 'variant14'], [
        new GenomicScore('15', 16, 17), new GenomicScore('18', 19, 20)
      ],
      new PresentInParent(['parent21', 'parent22'], new PresentInParentRarity(23, 24, true)),
      ['yes', 'no']
    );

    const browserQueryFilterMockFromJson = BrowserQueryFilter.fromJson(
      {
        datasetId: 'name1', geneSymbols: [ 'gene2', 'gene3' ], effectTypes: [ 'effectType4', 'effectType5' ],
        gender: [ 'gender6', 'gender7' ], personSetCollection: { id: 'id8', checkedValues: [ '9', '10' ] },
        studyTypes: [ 'studyType11', 'studyType12' ], variantTypes: [ 'variant13', 'variant14' ],
        genomicScores:  [
          { metric: '15', rangeStart: 16, rangeEnd: 17 }, { metric: '18', rangeStart: 19, rangeEnd: 20 }
        ], presentInParent: {
          presentInParent: [ 'parent21', 'parent22' ], rarity: { minFreq: 23, maxFreq: 24, ultraRare: true }
        }, presentInChild: ['yes', 'no']
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

describe('PresentInParent', () => {
  it('should create from json', () => {
    expect(new PresentInParent(['1', '2'], new PresentInParentRarity(3, 4, true))).toEqual(PresentInParent.fromJson({
      presentInParent: [ '1', '2' ], rarity: { minFreq: 3, maxFreq: 4, ultraRare: true }
    }));
  });
});

describe('PresentInParentRarity', () => {
  it('should create from json', () => {
    expect(new PresentInParentRarity(1, 2, false)).toEqual(PresentInParentRarity.fromJson({
      minFreq: 1, maxFreq: 2, ultraRare: false
    }));
  });
});
