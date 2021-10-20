import { BrowserQueryFilter, GenomicScore, PersonSetCollection, PresentInParent, PresentInParentRarity } from 'app/genotype-browser/genotype-browser';
import { ChildrenStats, EnrichmentEffectResult, EnrichmentTestResult } from './enrichment-result';

describe('ChildrenStats', () => {
  it('should create from json', () => {
    const childrenStatsMock = new ChildrenStats(1, 2, 3);

    const childrenStatsMockFromJson = ChildrenStats.fromJson({
      M: 1,
      F: 2,
      U: 3
    });

    expect(childrenStatsMock).toEqual(childrenStatsMockFromJson);
  });
});

const [
  browserQueryFilterMock1,
  browserQueryFilterMock2
] = [
  new BrowserQueryFilter(
    'name1', ['gene2', 'gene3'], ['effectType4', 'effectType5'],
    ['gender6', 'gender7'], new PersonSetCollection('id8', ['9', '10']),
    ['studyType11', 'studyType12'], ['variant13', 'variant14'], [
      new GenomicScore('15', 16, 17), new GenomicScore('18', 19, 20)
    ],
    new PresentInParent(['parent21', 'parent22'], new PresentInParentRarity(23, 24, true)),
    ['yes', 'no']
  ),
  new BrowserQueryFilter(
    'name25', ['gene26', 'gene27'], ['effectType28', 'effectType29'],
    ['gender30', 'gender31'], new PersonSetCollection('id32', ['33', '34']),
    ['studyType35', 'studyType36'], ['variant37', 'variant38'], [
      new GenomicScore('39', 40, 41), new GenomicScore('42', 43, 44)
    ],
    new PresentInParent(['parent45', 'parent46'], new PresentInParentRarity(47, 48, false)),
    ['notNo', 'trueNot']
  )
];

const [
  browserQueryFilterMockFromJson1,
  browserQueryFilterMockFromJson2
] = [
  {
    datasetId: 'name1', geneSymbols: [ 'gene2', 'gene3' ], effectTypes: [ 'effectType4', 'effectType5' ],
    gender: [ 'gender6', 'gender7' ], personSetCollection: { id: 'id8', checkedValues: [ '9', '10' ] },
    studyTypes: [ 'studyType11', 'studyType12' ], variantTypes: [ 'variant13', 'variant14' ],
    genomicScores:  [
      { metric: '15', rangeStart: 16, rangeEnd: 17 }, { metric: '18', rangeStart: 19, rangeEnd: 20 }
    ], presentInParent: {
      presentInParent: [ 'parent21', 'parent22' ], rarity: { minFreq: 23, maxFreq: 24, ultraRare: true }
    }, presentInChild: ['yes', 'no']
  },
  {
    datasetId: 'name25', geneSymbols: [ 'gene26', 'gene27' ], effectTypes: [ 'effectType28', 'effectType29' ],
    gender: [ 'gender30', 'gender31' ],
    personSetCollection: { id: 'id32', checkedValues: [ '33', '34' ] },
    studyTypes: [ 'studyType35', 'studyType36' ], variantTypes: [ 'variant37', 'variant38' ],
    genomicScores: [{
      metric: '39', rangeStart: 40, rangeEnd: 41 }, { metric: '42', rangeStart: 43, rangeEnd: 44
    }], presentInParent: {
      presentInParent: [ 'parent45', 'parent46' ], rarity: { minFreq: 47, maxFreq: 48, ultraRare: false }
    }, presentInChild: ['notNo', 'trueNot']
  }
];

describe('EnrichmentTestResult', () => {
  it('should create from json', () => {
    const enrichmentTestResultMock = new EnrichmentTestResult(
      'name1', 2, 3, 4, 5, browserQueryFilterMock1, browserQueryFilterMock2
    );

    const enrichmentTestResultFromJson = EnrichmentTestResult.fromJson({
      name: 'name1', count: 2, expected: 3, overlapped: 4, pvalue: 5,
      countFilter: browserQueryFilterMockFromJson1,
      overlapFilter: browserQueryFilterMockFromJson2
    });
    expect(enrichmentTestResultMock).toEqual(enrichmentTestResultFromJson);
  });
});
