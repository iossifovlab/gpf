import { BrowserQueryFilter, GenomicScore, PersonSetCollection, PresentInParent, PresentInParentRarity } from 'app/genotype-browser/genotype-browser';
import { ChildrenStats, EnrichmentEffectResult, EnrichmentResult, EnrichmentTestResult } from './enrichment-result';

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

const enrichmentEffectResult = {
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
};

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
      const enrichmentEffectResultMockFromJson = EnrichmentEffectResult.fromJson(enrichmentEffectResultMock);
      expect(enrichmentEffectResultMock).toEqual(enrichmentEffectResultMockFromJson);
    });
  }
);

describe('EnrichmentResult', () => {
  it('should create from json', () => {
    const enrichmentResult = new EnrichmentResult('selector1', enrichmentEffectResultMock,
      new EnrichmentEffectResult(
        new EnrichmentTestResult('name208', 209, 210, 211, 212,
          new BrowserQueryFilter(
            'name208', ['gene209', 'gene210'], ['effectType211', 'effectType212'],
            ['gender213', 'gender214'], new PersonSetCollection('id215', ['216', '217']),
            ['studyType218', 'studyType219'], ['variant220', 'variant221'], [
              new GenomicScore('222', 223, 224), new GenomicScore('225', 226, 227)
            ],
            new PresentInParent(['parent228', 'parent229'], new PresentInParentRarity(230, 231, true)),
            ['yes55', 'no55']
          ),
          new BrowserQueryFilter(
            'name232', ['gene233', 'gene234'], ['effectType235', 'effectType236'],
            ['gender237', 'gender238'], new PersonSetCollection('id239', ['240', '241']),
            ['studyType242', 'studyType243'], ['variant244', 'variant245'], [
              new GenomicScore('246', 247, 248), new GenomicScore('249', 250, 251)
            ],
            new PresentInParent(['parent252', 'parent253'], new PresentInParentRarity(254, 255, false)),
            ['notNo', 'trueNot']
          )
        ),
        new EnrichmentTestResult('name256', 257, 258, 259, 260,
          new BrowserQueryFilter(
            'name261', ['gene262', 'gene263'], ['effectType264', 'effectType265'],
            ['gender266', 'gender267'], new PersonSetCollection('id268', ['269', '270']),
            ['studyType271', 'studyType272'], ['variant273', 'variant274'], [
              new GenomicScore('275', 276, 277), new GenomicScore('278', 279, 280)
            ],
            new PresentInParent(['parent281', 'parent282'], new PresentInParentRarity(283, 284, false)),
            ['yes208', 'no208']
          ),
          new BrowserQueryFilter(
            'name285', ['gene286', 'gene287'], ['effectType288', 'effectType289'],
            ['gender290', 'gender291'], new PersonSetCollection('id292', ['293', '294']),
            ['studyType295', 'studyType296'], ['variant297', 'variant298'], [
              new GenomicScore('299', 300, 301), new GenomicScore('302', 303, 304)
            ],
            new PresentInParent(['parent305', 'parent306'], new PresentInParentRarity(307, 308, true)),
            ['yes209', 'no209']
          )
        ),
        new EnrichmentTestResult('name309', 310, 311, 312 , 313,
          new BrowserQueryFilter(
            'name314', ['gene315', 'gene316'], ['effectType317', 'effectType318'],
            ['gender319', 'gender320'], new PersonSetCollection('id321', ['322', '323']),
            ['studyType324', 'studyType325'], ['variant326', 'variant327'], [
              new GenomicScore('328', 329, 330), new GenomicScore('331', 332, 333)
            ],
            new PresentInParent(['parent334', 'parent335'], new PresentInParentRarity(336, 337, false)),
            ['yes210', 'no210']
          ),
          new BrowserQueryFilter(
            'name338', ['gene339', 'gene340'], ['effectType341', 'effectType342'],
            ['gender343', 'gender344'], new PersonSetCollection('id345', ['346', '347']),
            ['studyType348', 'studyType349'], ['variant350', 'variant351'], [
              new GenomicScore('352', 353, 354), new GenomicScore('355', 356, 357)
            ],
            new PresentInParent(['parent358', 'parent359'], new PresentInParentRarity(360, 361, true)),
            ['yes211', 'no211']
          )
        ),
        new EnrichmentTestResult('name362', 363, 364, 365 , 366,
          new BrowserQueryFilter(
            'name367', ['gene368', 'gene369'], ['effectType370', 'effectType371'],
            ['gender372', 'gender373'], new PersonSetCollection('id374', ['375', '376']),
            ['studyType377', 'studyType378'], ['variant379', 'variant380'], [
              new GenomicScore('381', 382, 383), new GenomicScore('384', 385, 386)
            ],
            new PresentInParent(['parent387', 'parent388'], new PresentInParentRarity(389, 390, true)),
            ['yes212', 'no212']
          ),
          new BrowserQueryFilter(
            'name391', ['gene392', 'gene393'], ['effectType394', 'effectType395'],
            ['gender396', 'gender397'], new PersonSetCollection('id398', ['399', '400']),
            ['studyType401', 'studyType402'], ['variant403', 'variant404'], [
              new GenomicScore('405', 406, 407), new GenomicScore('408', 409, 410)
            ],
            new PresentInParent(['parent411', 'parent412'], new PresentInParentRarity(413, 414, false)),
            ['yes213', 'no213']
          )
        )
      ), new EnrichmentEffectResult(
        new EnrichmentTestResult('name415', 416, 417, 418, 419,
          new BrowserQueryFilter(
            'name415', ['gene416', 'gene417'], ['effectType418', 'effectType419'],
            ['gender420', 'gender421'], new PersonSetCollection('id422', ['423', '424']),
            ['studyType425', 'studyType426'], ['variant427', 'variant428'], [
              new GenomicScore('429', 430, 431), new GenomicScore('432', 433, 434)
            ],
            new PresentInParent(['parent435', 'parent436'], new PresentInParentRarity(437, 438, true)),
            ['yes', 'no']
          ),
          new BrowserQueryFilter(
            'name439', ['gene440', 'gene441'], ['effectType442', 'effectType443'],
            ['gender444', 'gender445'], new PersonSetCollection('id446', ['447', '448']),
            ['studyType449', 'studyType450'], ['variant451', 'variant452'], [
              new GenomicScore('453', 454, 455), new GenomicScore('456', 457, 458)
            ],
            new PresentInParent(['parent459', 'parent460'], new PresentInParentRarity(461, 462, false)),
            ['notNo5', 'trueNot5']
          )
        ),
        new EnrichmentTestResult('name463', 464, 465, 466, 467,
          new BrowserQueryFilter(
            'name468', ['gene469', 'gene470'], ['effectType471', 'effectType472'],
            ['gender473', 'gender474'], new PersonSetCollection('id475', ['476', '477']),
            ['studyType478', 'studyType479'], ['variant480', 'variant481'], [
              new GenomicScore('482', 483, 484), new GenomicScore('485', 486, 487)
            ],
            new PresentInParent(['parent488', 'parent489'], new PresentInParentRarity(490, 491, false)),
            ['yes415', 'no415']
          ),
          new BrowserQueryFilter(
            'name492', ['gene493', 'gene494'], ['effectType495', 'effectType496'],
            ['gender497', 'gender498'], new PersonSetCollection('id499', ['500', '501']),
            ['studyType502', 'studyType503'], ['variant504', 'variant505'], [
              new GenomicScore('506', 507, 508), new GenomicScore('509', 510, 511)
            ],
            new PresentInParent(['parent512', 'parent513'], new PresentInParentRarity(514, 515, true)),
            ['yes416', 'no416']
          )
        ),
        new EnrichmentTestResult('name516', 517, 518, 519 , 520,
          new BrowserQueryFilter(
            'name521', ['gene522', 'gene523'], ['effectType524', 'effectType525'],
            ['gender526', 'gender527'], new PersonSetCollection('id528', ['529', '530']),
            ['studyType531', 'studyType532'], ['variant533', 'variant534'], [
              new GenomicScore('535', 536, 537), new GenomicScore('538', 539, 540)
            ],
            new PresentInParent(['parent541', 'parent542'], new PresentInParentRarity(543, 544, false)),
            ['yes417', 'no417']
          ),
          new BrowserQueryFilter(
            'name545', ['gene546', 'gene547'], ['effectType548', 'effectType549'],
            ['gender550', 'gender551'], new PersonSetCollection('id552', ['553', '554']),
            ['studyType555', 'studyType556'], ['variant557', 'variant558'], [
              new GenomicScore('559', 560, 561), new GenomicScore('562', 563, 564)
            ],
            new PresentInParent(['parent565', 'parent566'], new PresentInParentRarity(567, 568, true)),
            ['yes418', 'no418']
          )
        ),
        new EnrichmentTestResult('name569', 570, 571, 572 , 573,
          new BrowserQueryFilter(
            'name574', ['gene575', 'gene576'], ['effectType577', 'effectType578'],
            ['gender579', 'gender580'], new PersonSetCollection('id581', ['582', '583']),
            ['studyType584', 'studyType585'], ['variant586', 'variant587'], [
              new GenomicScore('588', 589, 590), new GenomicScore('591', 592, 593)
            ],
            new PresentInParent(['parent594', 'parent595'], new PresentInParentRarity(596, 597, true)),
            ['yes419', 'no419']
          ),
          new BrowserQueryFilter(
            'name598', ['gene599', 'gene600'], ['effectType601', 'effectType602'],
            ['gender603', 'gender604'], new PersonSetCollection('id605', ['606', '607']),
            ['studyType608', 'studyType609'], ['variant610', 'variant611'], [
              new GenomicScore('612', 613, 614), new GenomicScore('615', 616, 617)
            ],
            new PresentInParent(['parent618', 'parent619'], new PresentInParentRarity(620, 621, false)),
            ['yes420', 'no420']
          )
        )
      ), new ChildrenStats(622, 623, 624)
    );

    const enrichmentResultFromJson = EnrichmentResult.fromJson({
      selector: 'selector1',
      LGDs: {
        all: {
          name: 'name1', count: 2, expected: 3, overlapped: 4, pvalue: 5,
          countFilter:
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
          overlapFilter:
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
          },
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
      }, missense: {
        all: {
          name: 'name208', count: 209, expected: 210, overlapped: 211, pvalue: 212,
          countFilter:
          {
            datasetId: 'name208', geneSymbols: [ 'gene209', 'gene210' ],
            effectTypes: [ 'effectType211', 'effectType212' ],
            gender: [ 'gender213', 'gender214' ], personSetCollection: { id: 'id215', checkedValues: [ '216', '217' ] },
            studyTypes: [ 'studyType218', 'studyType219' ], variantTypes: [ 'variant220', 'variant221' ],
            genomicScores:  [
              { metric: '222', rangeStart: 223, rangeEnd: 224 }, { metric: '225', rangeStart: 226, rangeEnd: 227 }
            ], presentInParent: {
              presentInParent: [ 'parent228', 'parent229' ], rarity: { minFreq: 230, maxFreq: 231, ultraRare: true }
            }, presentInChild: ['yes55', 'no55']
          },
          overlapFilter:
          {
            datasetId: 'name232', geneSymbols: [ 'gene233', 'gene234' ],
            effectTypes: [ 'effectType235', 'effectType236' ],
            gender: [ 'gender237', 'gender238' ],
            personSetCollection: { id: 'id239', checkedValues: [ '240', '241' ] },
            studyTypes: [ 'studyType242', 'studyType243' ], variantTypes: [ 'variant244', 'variant245' ],
            genomicScores: [{
              metric: '246', rangeStart: 247, rangeEnd: 248 }, { metric: '249', rangeStart: 250, rangeEnd: 251
            }], presentInParent: {
              presentInParent: [ 'parent252', 'parent253' ], rarity: { minFreq: 254, maxFreq: 255, ultraRare: false }
            }, presentInChild: ['notNo', 'trueNot']
          },
        }, male: {
          name: 'name256', count: 257, expected: 258, overlapped: 259, pvalue: 260,
          countFilter:
          {
            datasetId: 'name261', geneSymbols: [ 'gene262', 'gene263' ],
            effectTypes: [ 'effectType264', 'effectType265' ],
            gender: [ 'gender266', 'gender267' ], personSetCollection: { id: 'id268', checkedValues: [ '269', '270' ] },
            studyTypes: [ 'studyType271', 'studyType272' ], variantTypes: [ 'variant273', 'variant274' ],
            genomicScores:  [
              { metric: '275', rangeStart: 276, rangeEnd: 277 }, { metric: '278', rangeStart: 279, rangeEnd: 280 }
            ], presentInParent: {
              presentInParent: [ 'parent281', 'parent282' ], rarity: { minFreq: 283, maxFreq: 284, ultraRare: false }
            }, presentInChild: ['yes208', 'no208']
          },
          overlapFilter:
          {
            datasetId: 'name285', geneSymbols: [ 'gene286', 'gene287' ],
            effectTypes: [ 'effectType288', 'effectType289' ],
            gender: [ 'gender290', 'gender291' ], personSetCollection: { id: 'id292', checkedValues: [ '293', '294' ] },
            studyTypes: [ 'studyType295', 'studyType296' ], variantTypes: [ 'variant297', 'variant298' ],
            genomicScores:  [
              { metric: '299', rangeStart: 300, rangeEnd: 301 }, { metric: '302', rangeStart: 303, rangeEnd: 304 }
            ], presentInParent: {
              presentInParent: [ 'parent305', 'parent306' ], rarity: { minFreq: 307, maxFreq: 308, ultraRare: true }
            }, presentInChild: ['yes209', 'no209']
          }
        }, female: {
          name: 'name309', count: 310, expected: 311, overlapped: 312, pvalue: 313,
          countFilter:
          {
            datasetId: 'name314', geneSymbols: [ 'gene315', 'gene316' ],
            effectTypes: [ 'effectType317', 'effectType318' ],
            gender: [ 'gender319', 'gender320' ], personSetCollection: { id: 'id321', checkedValues: [ '322', '323' ] },
            studyTypes: [ 'studyType324', 'studyType325' ], variantTypes: [ 'variant326', 'variant327' ],
            genomicScores:  [
              { metric: '328', rangeStart: 329, rangeEnd: 330 }, { metric: '331', rangeStart: 332, rangeEnd: 333 }
            ], presentInParent: {
              presentInParent: [ 'parent334', 'parent335' ], rarity: { minFreq: 336, maxFreq: 337, ultraRare: false }
            }, presentInChild: ['yes210', 'no210']
          },
          overlapFilter:
          {
            datasetId: 'name338', geneSymbols: [ 'gene339', 'gene340' ],
            effectTypes: [ 'effectType341', 'effectType342' ],
            gender: [ 'gender343', 'gender344' ], personSetCollection: { id: 'id345', checkedValues: [ '346', '347' ] },
            studyTypes: [ 'studyType348', 'studyType349' ], variantTypes: [ 'variant350', 'variant351' ],
            genomicScores:  [
              { metric: '352', rangeStart: 353, rangeEnd: 354 }, { metric: '355', rangeStart: 356, rangeEnd: 357 }
            ], presentInParent: {
              presentInParent: [ 'parent358', 'parent359' ], rarity: { minFreq: 360, maxFreq: 361, ultraRare: true }
            }, presentInChild: ['yes211', 'no211']
          }
        }, rec: {
          name: 'name362', count: 363, expected: 364, overlapped: 365, pvalue: 366,
          countFilter:
          {
            datasetId: 'name367', geneSymbols: [ 'gene368', 'gene369' ],
            effectTypes: [ 'effectType370', 'effectType371' ],
            gender: [ 'gender372', 'gender373' ], personSetCollection: { id: 'id374', checkedValues: [ '375', '376' ] },
            studyTypes: [ 'studyType377', 'studyType378' ], variantTypes: [ 'variant379', 'variant380' ],
            genomicScores:  [
              { metric: '381', rangeStart: 382, rangeEnd: 383 }, { metric: '384', rangeStart: 385, rangeEnd: 386 }
            ], presentInParent: {
              presentInParent: [ 'parent387', 'parent388' ], rarity: { minFreq: 389, maxFreq: 390, ultraRare: true }
            }, presentInChild: ['yes212', 'no212']
          },
          overlapFilter:
          {
            datasetId: 'name391', geneSymbols: [ 'gene392', 'gene393' ],
            effectTypes: [ 'effectType394', 'effectType395' ],
            gender: [ 'gender396', 'gender397' ], personSetCollection: { id: 'id398', checkedValues: [ '399', '400' ] },
            studyTypes: [ 'studyType401', 'studyType402' ], variantTypes: [ 'variant403', 'variant404' ],
            genomicScores:  [
              { metric: '405', rangeStart: 406, rangeEnd: 407 }, { metric: '408', rangeStart: 409, rangeEnd: 410 }
            ], presentInParent: {
              presentInParent: [ 'parent411', 'parent412' ], rarity: { minFreq: 413, maxFreq: 414, ultraRare: false }
            }, presentInChild: ['yes213', 'no213']
          }
        }
      }, synonymous: {
        all: {
          name: 'name415', count: 416, expected: 417, overlapped: 418, pvalue: 419,
          countFilter:
          {
            datasetId: 'name415', geneSymbols: [ 'gene416', 'gene417' ],
            effectTypes: [ 'effectType418', 'effectType419' ],
            gender: [ 'gender420', 'gender421' ], personSetCollection: { id: 'id422', checkedValues: [ '423', '424' ] },
            studyTypes: [ 'studyType425', 'studyType426' ], variantTypes: [ 'variant427', 'variant428' ],
            genomicScores:  [
              { metric: '429', rangeStart: 430, rangeEnd: 431 }, { metric: '432', rangeStart: 433, rangeEnd: 434 }
            ], presentInParent: {
              presentInParent: [ 'parent435', 'parent436' ], rarity: { minFreq: 437, maxFreq: 438, ultraRare: true }
            }, presentInChild: ['yes', 'no']
          },
          overlapFilter:
          {
            datasetId: 'name439', geneSymbols: [ 'gene440', 'gene441' ],
            effectTypes: [ 'effectType442', 'effectType443' ],
            gender: [ 'gender444', 'gender445' ],
            personSetCollection: { id: 'id446', checkedValues: [ '447', '448' ] },
            studyTypes: [ 'studyType449', 'studyType450' ], variantTypes: [ 'variant451', 'variant452' ],
            genomicScores: [{
              metric: '453', rangeStart: 454, rangeEnd: 455 }, { metric: '456', rangeStart: 457, rangeEnd: 458
            }], presentInParent: {
              presentInParent: [ 'parent459', 'parent460' ], rarity: { minFreq: 461, maxFreq: 462, ultraRare: false }
            }, presentInChild: ['notNo5', 'trueNot5']
          },
        }, male: {
          name: 'name463', count: 464, expected: 465, overlapped: 466, pvalue: 467,
          countFilter:
          {
            datasetId: 'name468', geneSymbols: [ 'gene469', 'gene470' ],
            effectTypes: [ 'effectType471', 'effectType472' ],
            gender: [ 'gender473', 'gender474' ], personSetCollection: { id: 'id475', checkedValues: [ '476', '477' ] },
            studyTypes: [ 'studyType478', 'studyType479' ], variantTypes: [ 'variant480', 'variant481' ],
            genomicScores:  [
              { metric: '482', rangeStart: 483, rangeEnd: 484 }, { metric: '485', rangeStart: 486, rangeEnd: 487 }
            ], presentInParent: {
              presentInParent: [ 'parent488', 'parent489' ], rarity: { minFreq: 490, maxFreq: 491, ultraRare: false }
            }, presentInChild: ['yes415', 'no415']
          },
          overlapFilter:
          {
            datasetId: 'name492', geneSymbols: [ 'gene493', 'gene494' ],
            effectTypes: [ 'effectType495', 'effectType496' ],
            gender: [ 'gender497', 'gender498' ], personSetCollection: { id: 'id499', checkedValues: [ '500', '501' ] },
            studyTypes: [ 'studyType502', 'studyType503' ], variantTypes: [ 'variant504', 'variant505' ],
            genomicScores:  [
              { metric: '506', rangeStart: 507, rangeEnd: 508 }, { metric: '509', rangeStart: 510, rangeEnd: 511 }
            ], presentInParent: {
              presentInParent: [ 'parent512', 'parent513' ], rarity: { minFreq: 514, maxFreq: 515, ultraRare: true }
            }, presentInChild: ['yes416', 'no416']
          }
        }, female: {
          name: 'name516', count: 517, expected: 518, overlapped: 519, pvalue: 520,
          countFilter:
          {
            datasetId: 'name521', geneSymbols: [ 'gene522', 'gene523' ],
            effectTypes: [ 'effectType524', 'effectType525' ],
            gender: [ 'gender526', 'gender527' ], personSetCollection: { id: 'id528', checkedValues: [ '529', '530' ] },
            studyTypes: [ 'studyType531', 'studyType532' ], variantTypes: [ 'variant533', 'variant534' ],
            genomicScores:  [
              { metric: '535', rangeStart: 536, rangeEnd: 537 }, { metric: '538', rangeStart: 539, rangeEnd: 540 }
            ], presentInParent: {
              presentInParent: [ 'parent541', 'parent542' ], rarity: { minFreq: 543, maxFreq: 544, ultraRare: false }
            }, presentInChild: ['yes417', 'no417']
          },
          overlapFilter:
          {
            datasetId: 'name545', geneSymbols: [ 'gene546', 'gene547' ],
            effectTypes: [ 'effectType548', 'effectType549' ],
            gender: [ 'gender550', 'gender551' ], personSetCollection: { id: 'id552', checkedValues: [ '553', '554' ] },
            studyTypes: [ 'studyType555', 'studyType556' ], variantTypes: [ 'variant557', 'variant558' ],
            genomicScores:  [
              { metric: '559', rangeStart: 560, rangeEnd: 561 }, { metric: '562', rangeStart: 563, rangeEnd: 564 }
            ], presentInParent: {
              presentInParent: [ 'parent565', 'parent566' ], rarity: { minFreq: 567, maxFreq: 568, ultraRare: true }
            }, presentInChild: ['yes418', 'no418']
          }
        }, rec: {
          name: 'name569', count: 570, expected: 571, overlapped: 572, pvalue: 573,
          countFilter:
          {
            datasetId: 'name574', geneSymbols: [ 'gene575', 'gene576' ],
            effectTypes: [ 'effectType577', 'effectType578' ],
            gender: [ 'gender579', 'gender580' ], personSetCollection: { id: 'id581', checkedValues: [ '582', '583' ] },
            studyTypes: [ 'studyType584', 'studyType585' ], variantTypes: [ 'variant586', 'variant587' ],
            genomicScores:  [
              { metric: '588', rangeStart: 589, rangeEnd: 590 }, { metric: '591', rangeStart: 592, rangeEnd: 593 }
            ], presentInParent: {
              presentInParent: [ 'parent594', 'parent595' ], rarity: { minFreq: 596, maxFreq: 597, ultraRare: true }
            }, presentInChild: ['yes419', 'no419']
          },
          overlapFilter:
          {
            datasetId: 'name598', geneSymbols: [ 'gene599', 'gene600' ],
            effectTypes: [ 'effectType601', 'effectType602' ],
            gender: [ 'gender603', 'gender604' ], personSetCollection: { id: 'id605', checkedValues: [ '606', '607' ] },
            studyTypes: [ 'studyType608', 'studyType609' ], variantTypes: [ 'variant610', 'variant611' ],
            genomicScores:  [
              { metric: '612', rangeStart: 613, rangeEnd: 614 }, { metric: '615', rangeStart: 616, rangeEnd: 617 }
            ], presentInParent: {
              presentInParent: [ 'parent618', 'parent619' ], rarity: { minFreq: 620, maxFreq: 621, ultraRare: false }
            }, presentInChild: ['yes420', 'no420']
          }
        }
      }, childrenStats: {
        M: 622,
        F: 623,
        U: 624
      }
    });

    expect(enrichmentResult).toEqual(enrichmentResultFromJson);
  });
});
