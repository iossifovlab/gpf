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

const enrichmentEffectResultMockFromJson = {
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
      expect(enrichmentEffectResultMock).toEqual(EnrichmentEffectResult.fromJson(enrichmentEffectResultMockFromJson));
    });
  }
);

const enrichmentResult1 = new EnrichmentResult('selector1', enrichmentEffectResultMock,
  new EnrichmentEffectResult(
    new EnrichmentTestResult('name208', 209, 210, 211, 212, browserQueryFilterMock1, browserQueryFilterMock2
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

const enrichmentResult2 = new EnrichmentResult('selector423',
  new EnrichmentEffectResult(
    new EnrichmentTestResult('name418', 419, 420, 421, 422,
      new BrowserQueryFilter(
        'name423', ['gene424', 'gene425'], ['effectType426', 'effectType427'],
        ['gender428', 'gender429'], new PersonSetCollection('id430', ['431', '432']),
        ['studyType433', 'studyType434'], ['variant435', 'variant436'], [
          new GenomicScore('437', 438, 439), new GenomicScore('440', 441, 442)
        ],
        new PresentInParent(['parent443', 'parent444'], new PresentInParentRarity(445, 446, true)),
        ['yes', 'no']
      ),
      new BrowserQueryFilter(
        'name447', ['gene448', 'gene449'], ['effectType450', 'effectType451'],
        ['gender452', 'gender453'], new PersonSetCollection('id454', ['455', '456']),
        ['studyType457', 'studyType458'], ['variant459', 'variant460'], [
          new GenomicScore('461', 462, 463), new GenomicScore('464', 465, 466)
        ],
        new PresentInParent(['parent467', 'parent468'], new PresentInParentRarity(469, 470, false)),
        ['notNo', 'trueNot']
      )
    ),
    new EnrichmentTestResult('name471', 472, 473, 474, 475,
      new BrowserQueryFilter(
        'name476', ['gene477', 'gene478'], ['effectType479', 'effectType480'],
        ['gender481', 'gender482'], new PersonSetCollection('id483', ['484', '485']),
        ['studyType486', 'studyType487'], ['variant488', 'variant489'], [
          new GenomicScore('490', 491, 492), new GenomicScore('493', 494, 495)
        ],
        new PresentInParent(['parent496', 'parent497'], new PresentInParentRarity(498, 499, false)),
        ['yes423', 'no423']
      ),
      new BrowserQueryFilter(
        'name500', ['gene501', 'gene502'], ['effectType503', 'effectType504'],
        ['gender505', 'gender506'], new PersonSetCollection('id507', ['508', '509']),
        ['studyType510', 'studyType511'], ['variant512', 'variant513'], [
          new GenomicScore('514', 515, 516), new GenomicScore('517', 518, 519)
        ],
        new PresentInParent(['parent520', 'parent521'], new PresentInParentRarity(522, 523, true)),
        ['yes419', 'no419']
      )
    ),
    new EnrichmentTestResult('name524', 525, 526, 527 , 528,
      new BrowserQueryFilter(
        'name529', ['gene530', 'gene531'], ['effectType532', 'effectType533'],
        ['gender534', 'gender535'], new PersonSetCollection('id536', ['537', '538']),
        ['studyType539', 'studyType540'], ['variant541', 'variant542'], [
          new GenomicScore('543', 544, 545), new GenomicScore('546', 547, 548)
        ],
        new PresentInParent(['parent549', 'parent550'], new PresentInParentRarity(551, 552, false)),
        ['yes425', 'no425']
      ),
      new BrowserQueryFilter(
        'name553', ['gene554', 'gene555'], ['effectType556', 'effectType557'],
        ['gender558', 'gender559'], new PersonSetCollection('id560', ['561', '562']),
        ['studyType563', 'studyType564'], ['variant565', 'variant566'], [
          new GenomicScore('567', 568, 569), new GenomicScore('570', 571, 572)
        ],
        new PresentInParent(['parent573', 'parent574'], new PresentInParentRarity(575, 576, true)),
        ['yes426', 'no426']
      )
    ),
    new EnrichmentTestResult('name577', 578, 579, 580 , 581,
      new BrowserQueryFilter(
        'name582', ['gene583', 'gene584'], ['effectType585', 'effectType586'],
        ['gender587', 'gender588'], new PersonSetCollection('id589', ['590', '591']),
        ['studyType592', 'studyType593'], ['variant594', 'variant595'], [
          new GenomicScore('596', 597, 598), new GenomicScore('599', 600, 601)
        ],
        new PresentInParent(['parent602', 'parent603'], new PresentInParentRarity(604, 605, true)),
        ['yes427', 'no427']
      ),
      new BrowserQueryFilter(
        'name606', ['gene607', 'gene608'], ['effectType609', 'effectType610'],
        ['gender611', 'gender612'], new PersonSetCollection('id613', ['614', '615']),
        ['studyType616', 'studyType617'], ['variant618', 'variant619'], [
          new GenomicScore('620', 621, 622), new GenomicScore('623', 624, 625)
        ],
        new PresentInParent(['parent626', 'parent627'], new PresentInParentRarity(628, 629, false)),
        ['yes428', 'no428']
      )
    )
  ),
  new EnrichmentEffectResult(
    new EnrichmentTestResult('name630', 631, 632, 633, 634,
      new BrowserQueryFilter(
        'name630', ['gene631', 'gene632'], ['effectType633', 'effectType634'],
        ['gender635', 'gender636'], new PersonSetCollection('id637', ['638', '639']),
        ['studyType640', 'studyType641'], ['variant642', 'variant643'], [
          new GenomicScore('644', 645, 646), new GenomicScore('647', 648, 649)
        ],
        new PresentInParent(['parent650', 'parent651'], new PresentInParentRarity(652, 653, true)),
        ['yes477', 'no477']
      ),
      new BrowserQueryFilter(
        'name654', ['gene655', 'gene656'], ['effectType657', 'effectType658'],
        ['gender659', 'gender660'], new PersonSetCollection('id661', ['662', '663']),
        ['studyType664', 'studyType665'], ['variant666', 'variant667'], [
          new GenomicScore('668', 669, 670), new GenomicScore('671', 672, 673)
        ],
        new PresentInParent(['parent674', 'parent675'], new PresentInParentRarity(676, 677, false)),
        ['notNo', 'trueNot']
      )
    ),
    new EnrichmentTestResult('name678', 679, 680, 681, 682,
      new BrowserQueryFilter(
        'name683', ['gene684', 'gene685'], ['effectType686', 'effectType687'],
        ['gender688', 'gender689'], new PersonSetCollection('id690', ['691', '692']),
        ['studyType693', 'studyType694'], ['variant695', 'variant696'], [
          new GenomicScore('697', 698, 699), new GenomicScore('700', 701, 702)
        ],
        new PresentInParent(['parent703', 'parent704'], new PresentInParentRarity(705, 706, false)),
        ['yes630', 'no630']
      ),
      new BrowserQueryFilter(
        'name707', ['gene708', 'gene709'], ['effectType710', 'effectType711'],
        ['gender712', 'gender713'], new PersonSetCollection('id714', ['715', '716']),
        ['studyType717', 'studyType718'], ['variant719', 'variant720'], [
          new GenomicScore('721', 722, 723), new GenomicScore('724', 725, 726)
        ],
        new PresentInParent(['parent727', 'parent728'], new PresentInParentRarity(729, 730, true)),
        ['yes631', 'no631']
      )
    ),
    new EnrichmentTestResult('name731', 732, 733, 734 , 735,
      new BrowserQueryFilter(
        'name736', ['gene737', 'gene738'], ['effectType739', 'effectType740'],
        ['gender741', 'gender742'], new PersonSetCollection('id743', ['744', '745']),
        ['studyType746', 'studyType747'], ['variant748', 'variant749'], [
          new GenomicScore('750', 751, 752), new GenomicScore('753', 754, 755)
        ],
        new PresentInParent(['parent756', 'parent757'], new PresentInParentRarity(758, 759, false)),
        ['yes632', 'no632']
      ),
      new BrowserQueryFilter(
        'name760', ['gene761', 'gene762'], ['effectType763', 'effectType764'],
        ['gender765', 'gender766'], new PersonSetCollection('id767', ['768', '769']),
        ['studyType770', 'studyType771'], ['variant772', 'variant773'], [
          new GenomicScore('774', 775, 776), new GenomicScore('777', 778, 779)
        ],
        new PresentInParent(['parent780', 'parent781'], new PresentInParentRarity(782, 783, true)),
        ['yes633', 'no633']
      )
    ),
    new EnrichmentTestResult('name784', 785, 786, 787 , 788,
      new BrowserQueryFilter(
        'name789', ['gene790', 'gene791'], ['effectType792', 'effectType793'],
        ['gender794', 'gender795'], new PersonSetCollection('id796', ['797', '798']),
        ['studyType799', 'studyType800'], ['variant801', 'variant802'], [
          new GenomicScore('803', 804, 805), new GenomicScore('806', 807, 808)
        ],
        new PresentInParent(['parent809', 'parent810'], new PresentInParentRarity(811, 812, true)),
        ['yes634', 'no634']
      ),
      new BrowserQueryFilter(
        'name813', ['gene814', 'gene815'], ['effectType816', 'effectType817'],
        ['gender818', 'gender819'], new PersonSetCollection('id820', ['821', '822']),
        ['studyType823', 'studyType824'], ['variant825', 'variant826'], [
          new GenomicScore('827', 828, 829), new GenomicScore('830', 831, 832)
        ],
        new PresentInParent(['parent833', 'parent834'], new PresentInParentRarity(835, 836, false)),
        ['yes635', 'no635']
      )
    )
  ),
  new EnrichmentEffectResult(
    new EnrichmentTestResult('name837', 838, 839, 840, 841,
      new BrowserQueryFilter(
        'name837', ['gene838', 'gene839'], ['effectType840', 'effectType841'],
        ['gender842', 'gender843'], new PersonSetCollection('id844', ['845', '846']),
        ['studyType847', 'studyType848'], ['variant849', 'variant850'], [
          new GenomicScore('851', 852, 853), new GenomicScore('854', 855, 856)
        ],
        new PresentInParent(['parent857', 'parent858'], new PresentInParentRarity(859, 860, true)),
        ['yes', 'no']
      ),
      new BrowserQueryFilter(
        'name861', ['gene862', 'gene863'], ['effectType864', 'effectType865'],
        ['gender866', 'gender867'], new PersonSetCollection('id868', ['869', '870']),
        ['studyType871', 'studyType872'], ['variant873', 'variant874'], [
          new GenomicScore('875', 876, 877), new GenomicScore('878', 879, 880)
        ],
        new PresentInParent(['parent881', 'parent882'], new PresentInParentRarity(883, 884, false)),
        ['notNo427', 'trueNot427']
      )
    ),
    new EnrichmentTestResult('name885', 886, 887, 888, 889,
      new BrowserQueryFilter(
        'name890', ['gene891', 'gene892'], ['effectType893', 'effectType894'],
        ['gender895', 'gender896'], new PersonSetCollection('id897', ['898', '899']),
        ['studyType900', 'studyType901'], ['variant902', 'variant903'], [
          new GenomicScore('904', 905, 906), new GenomicScore('907', 908, 909)
        ],
        new PresentInParent(['parent910', 'parent911'], new PresentInParentRarity(912, 913, false)),
        ['yes837', 'no837']
      ),
      new BrowserQueryFilter(
        'name914', ['gene915', 'gene916'], ['effectType917', 'effectType918'],
        ['gender919', 'gender920'], new PersonSetCollection('id921', ['922', '923']),
        ['studyType924', 'studyType925'], ['variant926', 'variant927'], [
          new GenomicScore('928', 929, 930), new GenomicScore('931', 932, 933)
        ],
        new PresentInParent(['parent934', 'parent935'], new PresentInParentRarity(936, 937, true)),
        ['yes838', 'no838']
      )
    ),
    new EnrichmentTestResult('name938', 939, 940, 941 , 942,
      new BrowserQueryFilter(
        'name943', ['gene944', 'gene945'], ['effectType946', 'effectType947'],
        ['gender948', 'gender949'], new PersonSetCollection('id950', ['951', '952']),
        ['studyType953', 'studyType954'], ['variant955', 'variant956'], [
          new GenomicScore('957', 958, 959), new GenomicScore('960', 961, 962)
        ],
        new PresentInParent(['parent963', 'parent964'], new PresentInParentRarity(965, 966, false)),
        ['yes839', 'no839']
      ),
      new BrowserQueryFilter(
        'name967', ['gene968', 'gene969'], ['effectType970', 'effectType971'],
        ['gender972', 'gender973'], new PersonSetCollection('id974', ['975', '976']),
        ['studyType977', 'studyType978'], ['variant979', 'variant980'], [
          new GenomicScore('981', 982, 983), new GenomicScore('984', 985, 986)
        ],
        new PresentInParent(['parent987', 'parent988'], new PresentInParentRarity(989, 990, true)),
        ['yes840', 'no840']
      )
    ),
    new EnrichmentTestResult('name991', 992, 993, 994 , 995,
      new BrowserQueryFilter(
        'name996', ['gene997', 'gene998'], ['effectType999', 'effectType1000'],
        ['gender1001', 'gender1002'], new PersonSetCollection('id1003', ['1004', '1005']),
        ['studyType1006', 'studyType1007'], ['variant1008', 'variant1009'], [
          new GenomicScore('1010', 1011, 1012), new GenomicScore('1013', 1014, 1015)
        ],
        new PresentInParent(['parent1016', 'parent1017'], new PresentInParentRarity(1018, 1019, true)),
        ['yes841', 'no841']
      ),
      new BrowserQueryFilter(
        'name1020', ['gene1021', 'gene1022'], ['effectType1023', 'effectType1024'],
        ['gender1025', 'gender1026'], new PersonSetCollection('id1027', ['1028', '1029']),
        ['studyType1030', 'studyType1031'], ['variant1032', 'variant1033'], [
          new GenomicScore('1034', 1035, 1036), new GenomicScore('1037', 1038, 1039)
        ],
        new PresentInParent(['parent1040', 'parent1041'], new PresentInParentRarity(1042, 1043, false)),
        ['yes842', 'no842']
      )
    )
  ), new ChildrenStats(1044, 1045, 1046)
);

const enrichmentResultFromJson1 = {
  selector: 'selector1',
  LGDs: {
    all: {
      name: 'name1', count: 2, expected: 3, overlapped: 4, pvalue: 5,
      countFilter: browserQueryFilterMockFromJson1,
      overlapFilter: browserQueryFilterMockFromJson2,
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
  },
  childrenStats: {
    M: 622,
    F: 623,
    U: 624
  }
};

const enrichmentResultFromJson2 = {
  selector: 'selector423',
  LGDs: {
    all: {
      name: 'name418', count: 419, expected: 420, overlapped: 421, pvalue: 422,
      countFilter:
      {
        datasetId: 'name423', geneSymbols: [ 'gene424', 'gene425' ], effectTypes: [ 'effectType426', 'effectType427' ],
        gender: [ 'gender428', 'gender429' ], personSetCollection: { id: 'id430', checkedValues: [ '431', '432' ] },
        studyTypes: [ 'studyType433', 'studyType434' ], variantTypes: [ 'variant435', 'variant436' ],
        genomicScores:  [
          { metric: '437', rangeStart: 438, rangeEnd: 439 }, { metric: '440', rangeStart: 441, rangeEnd: 442 }
        ], presentInParent: {
          presentInParent: [ 'parent443', 'parent444' ], rarity: { minFreq: 445, maxFreq: 446, ultraRare: true }
        }, presentInChild: ['yes', 'no']
      },
      overlapFilter:
      {
        datasetId: 'name447', geneSymbols: [ 'gene448', 'gene449' ], effectTypes: [ 'effectType450', 'effectType451' ],
        gender: [ 'gender452', 'gender453' ],
        personSetCollection: { id: 'id454', checkedValues: [ '455', '456' ] },
        studyTypes: [ 'studyType457', 'studyType458' ], variantTypes: [ 'variant459', 'variant460' ],
        genomicScores: [{
          metric: '461', rangeStart: 462, rangeEnd: 463 }, { metric: '464', rangeStart: 465, rangeEnd: 466
        }], presentInParent: {
          presentInParent: [ 'parent467', 'parent468' ], rarity: { minFreq: 469, maxFreq: 470, ultraRare: false }
        }, presentInChild: ['notNo', 'trueNot']
      },
    }, male: {
      name: 'name471', count: 472, expected: 473, overlapped: 474, pvalue: 475,
      countFilter:
      {
        datasetId: 'name476', geneSymbols: [ 'gene477', 'gene478' ], effectTypes: [ 'effectType479', 'effectType480' ],
        gender: [ 'gender481', 'gender482' ], personSetCollection: { id: 'id483', checkedValues: [ '484', '485' ] },
        studyTypes: [ 'studyType486', 'studyType487' ], variantTypes: [ 'variant488', 'variant489' ],
        genomicScores:  [
          { metric: '490', rangeStart: 491, rangeEnd: 492 }, { metric: '493', rangeStart: 494, rangeEnd: 495 }
        ], presentInParent: {
          presentInParent: [ 'parent496', 'parent497' ], rarity: { minFreq: 498, maxFreq: 499, ultraRare: false }
        }, presentInChild: ['yes423', 'no423']
      },
      overlapFilter:
      {
        datasetId: 'name500', geneSymbols: [ 'gene501', 'gene502' ], effectTypes: [ 'effectType503', 'effectType504' ],
        gender: [ 'gender505', 'gender506' ], personSetCollection: { id: 'id507', checkedValues: [ '508', '509' ] },
        studyTypes: [ 'studyType510', 'studyType511' ], variantTypes: [ 'variant512', 'variant513' ],
        genomicScores:  [
          { metric: '514', rangeStart: 515, rangeEnd: 516 }, { metric: '517', rangeStart: 518, rangeEnd: 519 }
        ], presentInParent: {
          presentInParent: [ 'parent520', 'parent521' ], rarity: { minFreq: 522, maxFreq: 523, ultraRare: true }
        }, presentInChild: ['yes419', 'no419']
      }
    }, female: {
      name: 'name524', count: 525, expected: 526, overlapped: 527, pvalue: 528,
      countFilter:
      {
        datasetId: 'name529', geneSymbols: [ 'gene530', 'gene531' ],
        effectTypes: [ 'effectType532', 'effectType533' ],
        gender: [ 'gender534', 'gender535' ], personSetCollection: { id: 'id536', checkedValues: [ '537', '538' ] },
        studyTypes: [ 'studyType539', 'studyType540' ], variantTypes: [ 'variant541', 'variant542' ],
        genomicScores:  [
          { metric: '543', rangeStart: 544, rangeEnd: 545 }, { metric: '546', rangeStart: 547, rangeEnd: 548 }
        ], presentInParent: {
          presentInParent: [ 'parent549', 'parent550' ], rarity: { minFreq: 551, maxFreq: 552, ultraRare: false }
        }, presentInChild: ['yes425', 'no425']
      },
      overlapFilter:
      {
        datasetId: 'name553', geneSymbols: [ 'gene554', 'gene555' ],
        effectTypes: [ 'effectType556', 'effectType557' ],
        gender: [ 'gender558', 'gender559' ], personSetCollection: { id: 'id560', checkedValues: [ '561', '562' ] },
        studyTypes: [ 'studyType563', 'studyType564' ], variantTypes: [ 'variant565', 'variant566' ],
        genomicScores:  [
          { metric: '567', rangeStart: 568, rangeEnd: 569 }, { metric: '570', rangeStart: 571, rangeEnd: 572 }
        ], presentInParent: {
          presentInParent: [ 'parent573', 'parent574' ], rarity: { minFreq: 575, maxFreq: 576, ultraRare: true }
        }, presentInChild: ['yes426', 'no426']
      }
    }, rec: {
      name: 'name577', count: 578, expected: 579, overlapped: 580, pvalue: 581,
      countFilter:
      {
        datasetId: 'name582', geneSymbols: [ 'gene583', 'gene584' ],
        effectTypes: [ 'effectType585', 'effectType586' ],
        gender: [ 'gender587', 'gender588' ], personSetCollection: { id: 'id589', checkedValues: [ '590', '591' ] },
        studyTypes: [ 'studyType592', 'studyType593' ], variantTypes: [ 'variant594', 'variant595' ],
        genomicScores:  [
          { metric: '596', rangeStart: 597, rangeEnd: 598 }, { metric: '599', rangeStart: 600, rangeEnd: 601 }
        ], presentInParent: {
          presentInParent: [ 'parent602', 'parent603' ], rarity: { minFreq: 604, maxFreq: 605, ultraRare: true }
        }, presentInChild: ['yes427', 'no427']
      },
      overlapFilter:
      {
        datasetId: 'name606', geneSymbols: [ 'gene607', 'gene608' ],
        effectTypes: [ 'effectType609', 'effectType610' ],
        gender: [ 'gender611', 'gender612' ], personSetCollection: { id: 'id613', checkedValues: [ '614', '615' ] },
        studyTypes: [ 'studyType616', 'studyType617' ], variantTypes: [ 'variant618', 'variant619' ],
        genomicScores:  [
          { metric: '620', rangeStart: 621, rangeEnd: 622 }, { metric: '623', rangeStart: 624, rangeEnd: 625 }
        ], presentInParent: {
          presentInParent: [ 'parent626', 'parent627' ], rarity: { minFreq: 628, maxFreq: 629, ultraRare: false }
        }, presentInChild: ['yes428', 'no428']
      }
    }
  }, missense: {
    all: {
      name: 'name630', count: 631, expected: 632, overlapped: 633, pvalue: 634,
      countFilter:
      {
        datasetId: 'name630', geneSymbols: [ 'gene631', 'gene632' ],
        effectTypes: [ 'effectType633', 'effectType634' ],
        gender: [ 'gender635', 'gender636' ], personSetCollection: { id: 'id637', checkedValues: [ '638', '639' ] },
        studyTypes: [ 'studyType640', 'studyType641' ], variantTypes: [ 'variant642', 'variant643' ],
        genomicScores:  [
          { metric: '644', rangeStart: 645, rangeEnd: 646 }, { metric: '647', rangeStart: 648, rangeEnd: 649 }
        ], presentInParent: {
          presentInParent: [ 'parent650', 'parent651' ], rarity: { minFreq: 652, maxFreq: 653, ultraRare: true }
        }, presentInChild: ['yes477', 'no477']
      },
      overlapFilter:
      {
        datasetId: 'name654', geneSymbols: [ 'gene655', 'gene656' ],
        effectTypes: [ 'effectType657', 'effectType658' ],
        gender: [ 'gender659', 'gender660' ],
        personSetCollection: { id: 'id661', checkedValues: [ '662', '663' ] },
        studyTypes: [ 'studyType664', 'studyType665' ], variantTypes: [ 'variant666', 'variant667' ],
        genomicScores: [{
          metric: '668', rangeStart: 669, rangeEnd: 670 }, { metric: '671', rangeStart: 672, rangeEnd: 673
        }], presentInParent: {
          presentInParent: [ 'parent674', 'parent675' ], rarity: { minFreq: 676, maxFreq: 677, ultraRare: false }
        }, presentInChild: ['notNo', 'trueNot']
      },
    }, male: {
      name: 'name678', count: 679, expected: 680, overlapped: 681, pvalue: 682,
      countFilter:
      {
        datasetId: 'name683', geneSymbols: [ 'gene684', 'gene685' ],
        effectTypes: [ 'effectType686', 'effectType687' ],
        gender: [ 'gender688', 'gender689' ], personSetCollection: { id: 'id690', checkedValues: [ '691', '692' ] },
        studyTypes: [ 'studyType693', 'studyType694' ], variantTypes: [ 'variant695', 'variant696' ],
        genomicScores:  [
          { metric: '697', rangeStart: 698, rangeEnd: 699 }, { metric: '700', rangeStart: 701, rangeEnd: 702 }
        ], presentInParent: {
          presentInParent: [ 'parent703', 'parent704' ], rarity: { minFreq: 705, maxFreq: 706, ultraRare: false }
        }, presentInChild: ['yes630', 'no630']
      },
      overlapFilter:
      {
        datasetId: 'name707', geneSymbols: [ 'gene708', 'gene709' ],
        effectTypes: [ 'effectType710', 'effectType711' ],
        gender: [ 'gender712', 'gender713' ], personSetCollection: { id: 'id714', checkedValues: [ '715', '716' ] },
        studyTypes: [ 'studyType717', 'studyType718' ], variantTypes: [ 'variant719', 'variant720' ],
        genomicScores:  [
          { metric: '721', rangeStart: 722, rangeEnd: 723 }, { metric: '724', rangeStart: 725, rangeEnd: 726 }
        ], presentInParent: {
          presentInParent: [ 'parent727', 'parent728' ], rarity: { minFreq: 729, maxFreq: 730, ultraRare: true }
        }, presentInChild: ['yes631', 'no631']
      }
    }, female: {
      name: 'name731', count: 732, expected: 733, overlapped: 734, pvalue: 735,
      countFilter:
      {
        datasetId: 'name736', geneSymbols: [ 'gene737', 'gene738' ],
        effectTypes: [ 'effectType739', 'effectType740' ],
        gender: [ 'gender741', 'gender742' ], personSetCollection: { id: 'id743', checkedValues: [ '744', '745' ] },
        studyTypes: [ 'studyType746', 'studyType747' ], variantTypes: [ 'variant748', 'variant749' ],
        genomicScores:  [
          { metric: '750', rangeStart: 751, rangeEnd: 752 }, { metric: '753', rangeStart: 754, rangeEnd: 755 }
        ], presentInParent: {
          presentInParent: [ 'parent756', 'parent757' ], rarity: { minFreq: 758, maxFreq: 759, ultraRare: false }
        }, presentInChild: ['yes632', 'no632']
      },
      overlapFilter:
      {
        datasetId: 'name760', geneSymbols: [ 'gene761', 'gene762' ],
        effectTypes: [ 'effectType763', 'effectType764' ],
        gender: [ 'gender765', 'gender766' ], personSetCollection: { id: 'id767', checkedValues: [ '768', '769' ] },
        studyTypes: [ 'studyType770', 'studyType771' ], variantTypes: [ 'variant772', 'variant773' ],
        genomicScores:  [
          { metric: '774', rangeStart: 775, rangeEnd: 776 }, { metric: '777', rangeStart: 778, rangeEnd: 779 }
        ], presentInParent: {
          presentInParent: [ 'parent780', 'parent781' ], rarity: { minFreq: 782, maxFreq: 783, ultraRare: true }
        }, presentInChild: ['yes633', 'no633']
      }
    }, rec: {
      name: 'name784', count: 785, expected: 786, overlapped: 787, pvalue: 788,
      countFilter:
      {
        datasetId: 'name789', geneSymbols: [ 'gene790', 'gene791' ],
        effectTypes: [ 'effectType792', 'effectType793' ],
        gender: [ 'gender794', 'gender795' ], personSetCollection: { id: 'id796', checkedValues: [ '797', '798' ] },
        studyTypes: [ 'studyType799', 'studyType800' ], variantTypes: [ 'variant801', 'variant802' ],
        genomicScores:  [
          { metric: '803', rangeStart: 804, rangeEnd: 805 }, { metric: '806', rangeStart: 807, rangeEnd: 808 }
        ], presentInParent: {
          presentInParent: [ 'parent809', 'parent810' ], rarity: { minFreq: 811, maxFreq: 812, ultraRare: true }
        }, presentInChild: ['yes634', 'no634']
      },
      overlapFilter:
      {
        datasetId: 'name813', geneSymbols: [ 'gene814', 'gene815' ],
        effectTypes: [ 'effectType816', 'effectType817' ],
        gender: [ 'gender818', 'gender819' ], personSetCollection: { id: 'id820', checkedValues: [ '821', '822' ] },
        studyTypes: [ 'studyType823', 'studyType824' ], variantTypes: [ 'variant825', 'variant826' ],
        genomicScores:  [
          { metric: '827', rangeStart: 828, rangeEnd: 829 }, { metric: '830', rangeStart: 831, rangeEnd: 832 }
        ], presentInParent: {
          presentInParent: [ 'parent833', 'parent834' ], rarity: { minFreq: 835, maxFreq: 836, ultraRare: false }
        }, presentInChild: ['yes635', 'no635']
      }
    }
  }, synonymous: {
    all: {
      name: 'name837', count: 838, expected: 839, overlapped: 840, pvalue: 841,
      countFilter:
      {
        datasetId: 'name837', geneSymbols: [ 'gene838', 'gene839' ],
        effectTypes: [ 'effectType840', 'effectType841' ],
        gender: [ 'gender842', 'gender843' ], personSetCollection: { id: 'id844', checkedValues: [ '845', '846' ] },
        studyTypes: [ 'studyType847', 'studyType848' ], variantTypes: [ 'variant849', 'variant850' ],
        genomicScores:  [
          { metric: '851', rangeStart: 852, rangeEnd: 853 }, { metric: '854', rangeStart: 855, rangeEnd: 856 }
        ], presentInParent: {
          presentInParent: [ 'parent857', 'parent858' ], rarity: { minFreq: 859, maxFreq: 860, ultraRare: true }
        }, presentInChild: ['yes', 'no']
      },
      overlapFilter:
      {
        datasetId: 'name861', geneSymbols: [ 'gene862', 'gene863' ],
        effectTypes: [ 'effectType864', 'effectType865' ],
        gender: [ 'gender866', 'gender867' ],
        personSetCollection: { id: 'id868', checkedValues: [ '869', '870' ] },
        studyTypes: [ 'studyType871', 'studyType872' ], variantTypes: [ 'variant873', 'variant874' ],
        genomicScores: [{
          metric: '875', rangeStart: 876, rangeEnd: 877 }, { metric: '878', rangeStart: 879, rangeEnd: 880
        }], presentInParent: {
          presentInParent: [ 'parent881', 'parent882' ], rarity: { minFreq: 883, maxFreq: 884, ultraRare: false }
        }, presentInChild: ['notNo427', 'trueNot427']
      },
    }, male: {
      name: 'name885', count: 886, expected: 887, overlapped: 888, pvalue: 889,
      countFilter:
      {
        datasetId: 'name890', geneSymbols: [ 'gene891', 'gene892' ],
        effectTypes: [ 'effectType893', 'effectType894' ],
        gender: [ 'gender895', 'gender896' ], personSetCollection: { id: 'id897', checkedValues: [ '898', '899' ] },
        studyTypes: [ 'studyType900', 'studyType901' ], variantTypes: [ 'variant902', 'variant903' ],
        genomicScores:  [
          { metric: '904', rangeStart: 905, rangeEnd: 906 }, { metric: '907', rangeStart: 908, rangeEnd: 909 }
        ], presentInParent: {
          presentInParent: [ 'parent910', 'parent911' ], rarity: { minFreq: 912, maxFreq: 913, ultraRare: false }
        }, presentInChild: ['yes837', 'no837']
      },
      overlapFilter:
      {
        datasetId: 'name914', geneSymbols: [ 'gene915', 'gene916' ],
        effectTypes: [ 'effectType917', 'effectType918' ],
        gender: [ 'gender919', 'gender920' ], personSetCollection: { id: 'id921', checkedValues: [ '922', '923' ] },
        studyTypes: [ 'studyType924', 'studyType925' ], variantTypes: [ 'variant926', 'variant927' ],
        genomicScores:  [
          { metric: '928', rangeStart: 929, rangeEnd: 930 }, { metric: '931', rangeStart: 932, rangeEnd: 933 }
        ], presentInParent: {
          presentInParent: [ 'parent934', 'parent935' ], rarity: { minFreq: 936, maxFreq: 937, ultraRare: true }
        }, presentInChild: ['yes838', 'no838']
      }
    }, female: {
      name: 'name938', count: 939, expected: 940, overlapped: 941, pvalue: 942,
      countFilter:
      {
        datasetId: 'name943', geneSymbols: [ 'gene944', 'gene945' ],
        effectTypes: [ 'effectType946', 'effectType947' ],
        gender: [ 'gender948', 'gender949' ], personSetCollection: { id: 'id950', checkedValues: [ '951', '952' ] },
        studyTypes: [ 'studyType953', 'studyType954' ], variantTypes: [ 'variant955', 'variant956' ],
        genomicScores:  [
          { metric: '957', rangeStart: 958, rangeEnd: 959 }, { metric: '960', rangeStart: 961, rangeEnd: 962 }
        ], presentInParent: {
          presentInParent: [ 'parent963', 'parent964' ], rarity: { minFreq: 965, maxFreq: 966, ultraRare: false }
        }, presentInChild: ['yes839', 'no839']
      },
      overlapFilter:
      {
        datasetId: 'name967', geneSymbols: [ 'gene968', 'gene969' ],
        effectTypes: [ 'effectType970', 'effectType971' ],
        gender: [ 'gender972', 'gender973' ], personSetCollection: { id: 'id974', checkedValues: [ '975', '976' ] },
        studyTypes: [ 'studyType977', 'studyType978' ], variantTypes: [ 'variant979', 'variant980' ],
        genomicScores:  [
          { metric: '981', rangeStart: 982, rangeEnd: 983 }, { metric: '984', rangeStart: 985, rangeEnd: 986 }
        ], presentInParent: {
          presentInParent: [ 'parent987', 'parent988' ], rarity: { minFreq: 989, maxFreq: 990, ultraRare: true }
        }, presentInChild: ['yes840', 'no840']
      }
    }, rec: {
      name: 'name991', count: 992, expected: 993, overlapped: 994, pvalue: 995,
      countFilter:
      {
        datasetId: 'name996', geneSymbols: [ 'gene997', 'gene998' ],
        effectTypes: [ 'effectType999', 'effectType1000' ],
        gender: [ 'gender1001', 'gender1002' ],
        personSetCollection: { id: 'id1003', checkedValues: [ '1004', '1005' ] },
        studyTypes: [ 'studyType1006', 'studyType1007' ], variantTypes: [ 'variant1008', 'variant1009' ],
        genomicScores:  [
          { metric: '1010', rangeStart: 1011, rangeEnd: 1012 }, { metric: '1013', rangeStart: 1014, rangeEnd: 1015 }
        ], presentInParent: {
          presentInParent: [ 'parent1016', 'parent1017' ], rarity: { minFreq: 1018, maxFreq: 1019, ultraRare: true }
        }, presentInChild: ['yes841', 'no841']
      },
      overlapFilter:
      {
        datasetId: 'name1020', geneSymbols: [ 'gene1021', 'gene1022' ],
        effectTypes: [ 'effectType1023', 'effectType1024' ],
        gender: [ 'gender1025', 'gender1026' ],
        personSetCollection: { id: 'id1027', checkedValues: [ '1028', '1029' ] },
        studyTypes: [ 'studyType1030', 'studyType1031' ], variantTypes: [ 'variant1032', 'variant1033' ],
        genomicScores:  [
          { metric: '1034', rangeStart: 1035, rangeEnd: 1036 }, { metric: '1037', rangeStart: 1038, rangeEnd: 1039 }
        ], presentInParent: {
          presentInParent: [ 'parent1040', 'parent1041' ], rarity: { minFreq: 1042, maxFreq: 1043, ultraRare: false }
        }, presentInChild: ['yes842', 'no842']
      }
    }
  }, childrenStats: {
    M: 1044,
    F: 1045,
    U: 1046
  }
};

describe('EnrichmentResult', () => {
  it('should create from json', () => {
    expect(enrichmentResult1).toEqual(EnrichmentResult.fromJson(enrichmentResultFromJson1));
  });

  it('should create from json array', () => {
    expect([enrichmentResult1, enrichmentResult2]).toEqual(EnrichmentResult.fromJsonArray([
      enrichmentResultFromJson1, enrichmentResultFromJson2
    ]));
  });
});
