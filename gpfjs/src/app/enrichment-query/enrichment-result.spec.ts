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

describe('EnrichmentEffectResult', () => {
    it('should create from json', () => {
      const enrichmentEffectResultMock = new EnrichmentEffectResult(
        new EnrichmentTestResult('name1', 2, 3, 4, 5, browserQueryFilterMock1, browserQueryFilterMock2),
        new EnrichmentTestResult('name49', 50, 51, 52, 53,
          new BrowserQueryFilter(
            'name54', ['gene55', 'gene56'], ['effectType57', 'effectType58'],
            ['gender59', 'gender60'], new PersonSetCollection('id61', ['62', '63']),
            ['studyType64', 'studyType65'], ['variant66', 'variant67'], [
              new GenomicScore('68', 69, 70), new GenomicScore('71', 72, 73)
            ],
            new PresentInParent(['parent74', 'parent75'], new PresentInParentRarity(76, 77, false)),
            ['yes1', 'no1']
          ),
          new BrowserQueryFilter(
            'name78', ['gene79', 'gene80'], ['effectType81', 'effectType82'],
            ['gender83', 'gender84'], new PersonSetCollection('id85', ['86', '87']),
            ['studyType88', 'studyType89'], ['variant90', 'variant91'], [
              new GenomicScore('92', 93, 94), new GenomicScore('95', 96, 97)
            ],
            new PresentInParent(['parent98', 'parent99'], new PresentInParentRarity(100, 101, true)),
            ['yes2', 'no2']
          )
        ),
        new EnrichmentTestResult('name102', 103, 104, 105 , 106,
          new BrowserQueryFilter(
            'name107', ['gene108', 'gene109'], ['effectType110', 'effectType111'],
            ['gender112', 'gender113'], new PersonSetCollection('id114', ['115', '116']),
            ['studyType117', 'studyType118'], ['variant119', 'variant120'], [
              new GenomicScore('121', 122, 123), new GenomicScore('124', 125, 126)
            ],
            new PresentInParent(['parent127', 'parent128'], new PresentInParentRarity(129, 130, false)),
            ['yes3', 'no3']
          ),
          new BrowserQueryFilter(
            'name131', ['gene132', 'gene133'], ['effectType134', 'effectType135'],
            ['gender136', 'gender137'], new PersonSetCollection('id138', ['139', '140']),
            ['studyType141', 'studyType142'], ['variant143', 'variant144'], [
              new GenomicScore('145', 146, 147), new GenomicScore('148', 149, 150)
            ],
            new PresentInParent(['parent151', 'parent152'], new PresentInParentRarity(153, 154, true)),
            ['yes4', 'no4']
          )
        ),
        new EnrichmentTestResult('name155', 156, 157, 158 , 159,
          new BrowserQueryFilter(
            'name160', ['gene161', 'gene162'], ['effectType163', 'effectType164'],
            ['gender165', 'gender166'], new PersonSetCollection('id167', ['168', '169']),
            ['studyType170', 'studyType171'], ['variant172', 'variant173'], [
              new GenomicScore('174', 175, 176), new GenomicScore('177', 178, 179)
            ],
            new PresentInParent(['parent180', 'parent181'], new PresentInParentRarity(182, 183, true)),
            ['yes5', 'no5']
          ),
          new BrowserQueryFilter(
            'name184', ['gene185', 'gene186'], ['effectType187', 'effectType188'],
            ['gender189', 'gender190'], new PersonSetCollection('id191', ['192', '193']),
            ['studyType194', 'studyType195'], ['variant196', 'variant197'], [
              new GenomicScore('198', 199, 200), new GenomicScore('201', 202, 203)
            ],
            new PresentInParent(['parent204', 'parent205'], new PresentInParentRarity(206, 207, false)),
            ['yes6', 'no6']
          )
        )
      );

      const enrichmentEffectResultMockFromJson = EnrichmentEffectResult.fromJson({
        all: {
          name: 'name1', count: 2, expected: 3, overlapped: 4, pvalue: 5,
          countFilter: browserQueryFilterMockFromJson1,
          overlapFilter: browserQueryFilterMockFromJson2
        }, male: {
          name: 'name49', count: 50, expected: 51, overlapped: 52, pvalue: 53,
          countFilter:
          {
            datasetId: 'name54', geneSymbols: [ 'gene55', 'gene56' ], effectTypes: [ 'effectType57', 'effectType58' ],
            gender: [ 'gender59', 'gender60' ], personSetCollection: { id: 'id61', checkedValues: [ '62', '63' ] },
            studyTypes: [ 'studyType64', 'studyType65' ], variantTypes: [ 'variant66', 'variant67' ],
            genomicScores:  [
              { metric: '68', rangeStart: 69, rangeEnd: 70 }, { metric: '71', rangeStart: 72, rangeEnd: 73 }
            ], presentInParent: {
              presentInParent: [ 'parent74', 'parent75' ], rarity: { minFreq: 76, maxFreq: 77, ultraRare: false }
            }, presentInChild: ['yes1', 'no1']
          },
          overlapFilter:
          {
            datasetId: 'name78', geneSymbols: [ 'gene79', 'gene80' ], effectTypes: [ 'effectType81', 'effectType82' ],
            gender: [ 'gender83', 'gender84' ], personSetCollection: { id: 'id85', checkedValues: [ '86', '87' ] },
            studyTypes: [ 'studyType88', 'studyType89' ], variantTypes: [ 'variant90', 'variant91' ],
            genomicScores:  [
              { metric: '92', rangeStart: 93, rangeEnd: 94 }, { metric: '95', rangeStart: 96, rangeEnd: 97 }
            ], presentInParent: {
              presentInParent: [ 'parent98', 'parent99' ], rarity: { minFreq: 100, maxFreq: 101, ultraRare: true }
            }, presentInChild: ['yes2', 'no2']
          }
        }, female: {
          name: 'name102', count: 103, expected: 104, overlapped: 105, pvalue: 106,
          countFilter:
          {
            datasetId: 'name107', geneSymbols: [ 'gene108', 'gene109' ],
            effectTypes: [ 'effectType110', 'effectType111' ],
            gender: [ 'gender112', 'gender113' ], personSetCollection: { id: 'id114', checkedValues: [ '115', '116' ] },
            studyTypes: [ 'studyType117', 'studyType118' ], variantTypes: [ 'variant119', 'variant120' ],
            genomicScores:  [
              { metric: '121', rangeStart: 122, rangeEnd: 123 }, { metric: '124', rangeStart: 125, rangeEnd: 126 }
            ], presentInParent: {
              presentInParent: [ 'parent127', 'parent128' ], rarity: { minFreq: 129, maxFreq: 130, ultraRare: false }
            }, presentInChild: ['yes3', 'no3']
          },
          overlapFilter:
          {
            datasetId: 'name131', geneSymbols: [ 'gene132', 'gene133' ],
            effectTypes: [ 'effectType134', 'effectType135' ],
            gender: [ 'gender136', 'gender137' ], personSetCollection: { id: 'id138', checkedValues: [ '139', '140' ] },
            studyTypes: [ 'studyType141', 'studyType142' ], variantTypes: [ 'variant143', 'variant144' ],
            genomicScores:  [
              { metric: '145', rangeStart: 146, rangeEnd: 147 }, { metric: '148', rangeStart: 149, rangeEnd: 150 }
            ], presentInParent: {
              presentInParent: [ 'parent151', 'parent152' ], rarity: { minFreq: 153, maxFreq: 154, ultraRare: true }
            }, presentInChild: ['yes4', 'no4']
          }
        }, rec: {
          name: 'name155', count: 156, expected: 157, overlapped: 158, pvalue: 159,
          countFilter:
          {
            datasetId: 'name160', geneSymbols: [ 'gene161', 'gene162' ],
            effectTypes: [ 'effectType163', 'effectType164' ],
            gender: [ 'gender165', 'gender166' ], personSetCollection: { id: 'id167', checkedValues: [ '168', '169' ] },
            studyTypes: [ 'studyType170', 'studyType171' ], variantTypes: [ 'variant172', 'variant173' ],
            genomicScores:  [
              { metric: '174', rangeStart: 175, rangeEnd: 176 }, { metric: '177', rangeStart: 178, rangeEnd: 179 }
            ], presentInParent: {
              presentInParent: [ 'parent180', 'parent181' ], rarity: { minFreq: 182, maxFreq: 183, ultraRare: true }
            }, presentInChild: ['yes5', 'no5']
          },
          overlapFilter:
          {
            datasetId: 'name184', geneSymbols: [ 'gene185', 'gene186' ],
            effectTypes: [ 'effectType187', 'effectType188' ],
            gender: [ 'gender189', 'gender190' ], personSetCollection: { id: 'id191', checkedValues: [ '192', '193' ] },
            studyTypes: [ 'studyType194', 'studyType195' ], variantTypes: [ 'variant196', 'variant197' ],
            genomicScores:  [
              { metric: '198', rangeStart: 199, rangeEnd: 200 }, { metric: '201', rangeStart: 202, rangeEnd: 203 }
            ], presentInParent: {
              presentInParent: [ 'parent204', 'parent205' ], rarity: { minFreq: 206, maxFreq: 207, ultraRare: false }
            }, presentInChild: ['yes6', 'no6']
          }
        }
      });

      expect(enrichmentEffectResultMock).toEqual(enrichmentEffectResultMockFromJson);
    });
  }
);
