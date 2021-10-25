import { BrowserQueryFilter, GenomicScore, PersonSetCollection } from 'app/genotype-browser/genotype-browser';
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
    ['studyType11', 'studyType12'], ['variant13', 'variant14']
  ),
  new BrowserQueryFilter(
    'name25', ['gene26', 'gene27'], ['effectType28', 'effectType29'],
    ['gender30', 'gender31'], new PersonSetCollection('id32', ['33', '34']),
    ['studyType35', 'studyType36'], ['variant37', 'variant38']
  )
];

const [
  browserQueryFilterMockFromJson1,
  browserQueryFilterMockFromJson2
] = [
  {
    datasetId: 'name1', geneSymbols: [ 'gene2', 'gene3' ], effectTypes: [ 'effectType4', 'effectType5' ],
    gender: [ 'gender6', 'gender7' ], peopleGroup: { id: 'id8', checkedValues: [ '9', '10' ] },
    studyTypes: [ 'studyType11', 'studyType12' ], variantTypes: [ 'variant13', 'variant14' ]
  },
  {
    datasetId: 'name25', geneSymbols: [ 'gene26', 'gene27' ], effectTypes: [ 'effectType28', 'effectType29' ],
    gender: [ 'gender30', 'gender31' ],
    peopleGroup: { id: 'id32', checkedValues: [ '33', '34' ] },
    studyTypes: [ 'studyType35', 'studyType36' ], variantTypes: [ 'variant37', 'variant38' ]
  }
];

const enrichmentEffectResultMock = new EnrichmentEffectResult(
  new EnrichmentTestResult('name1', 2, 3, 4, 5, browserQueryFilterMock1, browserQueryFilterMock2),
  new EnrichmentTestResult('name49', 50, 51, 52, 53,
    new BrowserQueryFilter(
      'name54', ['gene55', 'gene56'], ['effectType57', 'effectType58'],
      ['gender59', 'gender60'], new PersonSetCollection('id61', ['62', '63']),
      ['studyType64', 'studyType65'], ['variant66', 'variant67']
    ),
    new BrowserQueryFilter(
      'name78', ['gene79', 'gene80'], ['effectType81', 'effectType82'],
      ['gender83', 'gender84'], new PersonSetCollection('id85', ['86', '87']),
      ['studyType88', 'studyType89'], ['variant90', 'variant91']
    )
  ),
  new EnrichmentTestResult('name102', 103, 104, 105 , 106,
    new BrowserQueryFilter(
      'name107', ['gene108', 'gene109'], ['effectType110', 'effectType111'],
      ['gender112', 'gender113'], new PersonSetCollection('id114', ['115', '116']),
      ['studyType117', 'studyType118'], ['variant119', 'variant120']
    ),
    new BrowserQueryFilter(
      'name131', ['gene132', 'gene133'], ['effectType134', 'effectType135'],
      ['gender136', 'gender137'], new PersonSetCollection('id138', ['139', '140']),
      ['studyType141', 'studyType142'], ['variant143', 'variant144']
    )
  ),
  new EnrichmentTestResult('name155', 156, 157, 158 , 159,
    new BrowserQueryFilter(
      'name160', ['gene161', 'gene162'], ['effectType163', 'effectType164'],
      ['gender165', 'gender166'], new PersonSetCollection('id167', ['168', '169']),
      ['studyType170', 'studyType171'], ['variant172', 'variant173']
    ),
    new BrowserQueryFilter(
      'name184', ['gene185', 'gene186'], ['effectType187', 'effectType188'],
      ['gender189', 'gender190'], new PersonSetCollection('id191', ['192', '193']),
      ['studyType194', 'studyType195'], ['variant196', 'variant197']
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
      gender: [ 'gender59', 'gender60' ], peopleGroup: { id: 'id61', checkedValues: [ '62', '63' ] },
      studyTypes: [ 'studyType64', 'studyType65' ], variantTypes: [ 'variant66', 'variant67' ]
    },
    overlapFilter:
    {
      datasetId: 'name78', geneSymbols: [ 'gene79', 'gene80' ], effectTypes: [ 'effectType81', 'effectType82' ],
      gender: [ 'gender83', 'gender84' ], peopleGroup: { id: 'id85', checkedValues: [ '86', '87' ] },
      studyTypes: [ 'studyType88', 'studyType89' ], variantTypes: [ 'variant90', 'variant91' ]
    }
  }, female: {
    name: 'name102', count: 103, expected: 104, overlapped: 105, pvalue: 106,
    countFilter:
    {
      datasetId: 'name107', geneSymbols: [ 'gene108', 'gene109' ],
      effectTypes: [ 'effectType110', 'effectType111' ],
      gender: [ 'gender112', 'gender113' ], peopleGroup: { id: 'id114', checkedValues: [ '115', '116' ] },
      studyTypes: [ 'studyType117', 'studyType118' ], variantTypes: [ 'variant119', 'variant120' ]
    },
    overlapFilter:
    {
      datasetId: 'name131', geneSymbols: [ 'gene132', 'gene133' ],
      effectTypes: [ 'effectType134', 'effectType135' ],
      gender: [ 'gender136', 'gender137' ], peopleGroup: { id: 'id138', checkedValues: [ '139', '140' ] },
      studyTypes: [ 'studyType141', 'studyType142' ], variantTypes: [ 'variant143', 'variant144' ]
    }
  }, rec: {
    name: 'name155', count: 156, expected: 157, overlapped: 158, pvalue: 159,
    countFilter:
    {
      datasetId: 'name160', geneSymbols: [ 'gene161', 'gene162' ],
      effectTypes: [ 'effectType163', 'effectType164' ],
      gender: [ 'gender165', 'gender166' ], peopleGroup: { id: 'id167', checkedValues: [ '168', '169' ] },
      studyTypes: [ 'studyType170', 'studyType171' ], variantTypes: [ 'variant172', 'variant173' ]
    },
    overlapFilter:
    {
      datasetId: 'name184', geneSymbols: [ 'gene185', 'gene186' ],
      effectTypes: [ 'effectType187', 'effectType188' ],
      gender: [ 'gender189', 'gender190' ], peopleGroup: { id: 'id191', checkedValues: [ '192', '193' ] },
      studyTypes: [ 'studyType194', 'studyType195' ], variantTypes: [ 'variant196', 'variant197' ]
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
    new EnrichmentTestResult('name208', 209, 210, 211, 212,
      new BrowserQueryFilter(
        'name208', ['gene209', 'gene210'], ['effectType211', 'effectType212'],
        ['gender213', 'gender214'], new PersonSetCollection('id215', ['216', '217']),
        ['studyType218', 'studyType219'], ['variant220', 'variant221']
      ),
      new BrowserQueryFilter(
        'name232', ['gene233', 'gene234'], ['effectType235', 'effectType236'],
        ['gender237', 'gender238'], new PersonSetCollection('id239', ['240', '241']),
        ['studyType242', 'studyType243'], ['variant244', 'variant245']
      )
    ),
    new EnrichmentTestResult('name256', 257, 258, 259, 260,
      new BrowserQueryFilter(
        'name261', ['gene262', 'gene263'], ['effectType264', 'effectType265'],
        ['gender266', 'gender267'], new PersonSetCollection('id268', ['269', '270']),
        ['studyType271', 'studyType272'], ['variant273', 'variant274']
      ),
      new BrowserQueryFilter(
        'name285', ['gene286', 'gene287'], ['effectType288', 'effectType289'],
        ['gender290', 'gender291'], new PersonSetCollection('id292', ['293', '294']),
        ['studyType295', 'studyType296'], ['variant297', 'variant298']
      )
    ),
    new EnrichmentTestResult('name309', 310, 311, 312 , 313,
      new BrowserQueryFilter(
        'name314', ['gene315', 'gene316'], ['effectType317', 'effectType318'],
        ['gender319', 'gender320'], new PersonSetCollection('id321', ['322', '323']),
        ['studyType324', 'studyType325'], ['variant326', 'variant327']
      ),
      new BrowserQueryFilter(
        'name338', ['gene339', 'gene340'], ['effectType341', 'effectType342'],
        ['gender343', 'gender344'], new PersonSetCollection('id345', ['346', '347']),
        ['studyType348', 'studyType349'], ['variant350', 'variant351']
      )
    ),
    new EnrichmentTestResult('name362', 363, 364, 365 , 366,
      new BrowserQueryFilter(
        'name367', ['gene368', 'gene369'], ['effectType370', 'effectType371'],
        ['gender372', 'gender373'], new PersonSetCollection('id374', ['375', '376']),
        ['studyType377', 'studyType378'], ['variant379', 'variant380']
      ),
      new BrowserQueryFilter(
        'name391', ['gene392', 'gene393'], ['effectType394', 'effectType395'],
        ['gender396', 'gender397'], new PersonSetCollection('id398', ['399', '400']),
        ['studyType401', 'studyType402'], ['variant403', 'variant404']
      )
    )
  ), new EnrichmentEffectResult(
    new EnrichmentTestResult('name415', 416, 417, 418, 419,
      new BrowserQueryFilter(
        'name415', ['gene416', 'gene417'], ['effectType418', 'effectType419'],
        ['gender420', 'gender421'], new PersonSetCollection('id422', ['423', '424']),
        ['studyType425', 'studyType426'], ['variant427', 'variant428']
      ),
      new BrowserQueryFilter(
        'name439', ['gene440', 'gene441'], ['effectType442', 'effectType443'],
        ['gender444', 'gender445'], new PersonSetCollection('id446', ['447', '448']),
        ['studyType449', 'studyType450'], ['variant451', 'variant452']
      )
    ),
    new EnrichmentTestResult('name463', 464, 465, 466, 467,
      new BrowserQueryFilter(
        'name468', ['gene469', 'gene470'], ['effectType471', 'effectType472'],
        ['gender473', 'gender474'], new PersonSetCollection('id475', ['476', '477']),
        ['studyType478', 'studyType479'], ['variant480', 'variant481']
      ),
      new BrowserQueryFilter(
        'name492', ['gene493', 'gene494'], ['effectType495', 'effectType496'],
        ['gender497', 'gender498'], new PersonSetCollection('id499', ['500', '501']),
        ['studyType502', 'studyType503'], ['variant504', 'variant505']
      )
    ),
    new EnrichmentTestResult('name516', 517, 518, 519 , 520,
      new BrowserQueryFilter(
        'name521', ['gene522', 'gene523'], ['effectType524', 'effectType525'],
        ['gender526', 'gender527'], new PersonSetCollection('id528', ['529', '530']),
        ['studyType531', 'studyType532'], ['variant533', 'variant534']
      ),
      new BrowserQueryFilter(
        'name545', ['gene546', 'gene547'], ['effectType548', 'effectType549'],
        ['gender550', 'gender551'], new PersonSetCollection('id552', ['553', '554']),
        ['studyType555', 'studyType556'], ['variant557', 'variant558']
      )
    ),
    new EnrichmentTestResult('name569', 570, 571, 572 , 573,
      new BrowserQueryFilter(
        'name574', ['gene575', 'gene576'], ['effectType577', 'effectType578'],
        ['gender579', 'gender580'], new PersonSetCollection('id581', ['582', '583']),
        ['studyType584', 'studyType585'], ['variant586', 'variant587']
      ),
      new BrowserQueryFilter(
        'name598', ['gene599', 'gene600'], ['effectType601', 'effectType602'],
        ['gender603', 'gender604'], new PersonSetCollection('id605', ['606', '607']),
        ['studyType608', 'studyType609'], ['variant610', 'variant611']
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
        ['studyType433', 'studyType434'], ['variant435', 'variant436']
      ),
      new BrowserQueryFilter(
        'name447', ['gene448', 'gene449'], ['effectType450', 'effectType451'],
        ['gender452', 'gender453'], new PersonSetCollection('id454', ['455', '456']),
        ['studyType457', 'studyType458'], ['variant459', 'variant460']
      )
    ),
    new EnrichmentTestResult('name471', 472, 473, 474, 475,
      new BrowserQueryFilter(
        'name476', ['gene477', 'gene478'], ['effectType479', 'effectType480'],
        ['gender481', 'gender482'], new PersonSetCollection('id483', ['484', '485']),
        ['studyType486', 'studyType487'], ['variant488', 'variant489']
      ),
      new BrowserQueryFilter(
        'name500', ['gene501', 'gene502'], ['effectType503', 'effectType504'],
        ['gender505', 'gender506'], new PersonSetCollection('id507', ['508', '509']),
        ['studyType510', 'studyType511'], ['variant512', 'variant513']
      )
    ),
    new EnrichmentTestResult('name524', 525, 526, 527 , 528,
      new BrowserQueryFilter(
        'name529', ['gene530', 'gene531'], ['effectType532', 'effectType533'],
        ['gender534', 'gender535'], new PersonSetCollection('id536', ['537', '538']),
        ['studyType539', 'studyType540'], ['variant541', 'variant542']
      ),
      new BrowserQueryFilter(
        'name553', ['gene554', 'gene555'], ['effectType556', 'effectType557'],
        ['gender558', 'gender559'], new PersonSetCollection('id560', ['561', '562']),
        ['studyType563', 'studyType564'], ['variant565', 'variant566']
      )
    ),
    new EnrichmentTestResult('name577', 578, 579, 580 , 581,
      new BrowserQueryFilter(
        'name582', ['gene583', 'gene584'], ['effectType585', 'effectType586'],
        ['gender587', 'gender588'], new PersonSetCollection('id589', ['590', '591']),
        ['studyType592', 'studyType593'], ['variant594', 'variant595']
      ),
      new BrowserQueryFilter(
        'name606', ['gene607', 'gene608'], ['effectType609', 'effectType610'],
        ['gender611', 'gender612'], new PersonSetCollection('id613', ['614', '615']),
        ['studyType616', 'studyType617'], ['variant618', 'variant619']
      )
    )
  ),
  new EnrichmentEffectResult(
    new EnrichmentTestResult('name630', 631, 632, 633, 634,
      new BrowserQueryFilter(
        'name630', ['gene631', 'gene632'], ['effectType633', 'effectType634'],
        ['gender635', 'gender636'], new PersonSetCollection('id637', ['638', '639']),
        ['studyType640', 'studyType641'], ['variant642', 'variant643']
      ),
      new BrowserQueryFilter(
        'name654', ['gene655', 'gene656'], ['effectType657', 'effectType658'],
        ['gender659', 'gender660'], new PersonSetCollection('id661', ['662', '663']),
        ['studyType664', 'studyType665'], ['variant666', 'variant667']
      )
    ),
    new EnrichmentTestResult('name678', 679, 680, 681, 682,
      new BrowserQueryFilter(
        'name683', ['gene684', 'gene685'], ['effectType686', 'effectType687'],
        ['gender688', 'gender689'], new PersonSetCollection('id690', ['691', '692']),
        ['studyType693', 'studyType694'], ['variant695', 'variant696']
      ),
      new BrowserQueryFilter(
        'name707', ['gene708', 'gene709'], ['effectType710', 'effectType711'],
        ['gender712', 'gender713'], new PersonSetCollection('id714', ['715', '716']),
        ['studyType717', 'studyType718'], ['variant719', 'variant720']
      )
    ),
    new EnrichmentTestResult('name731', 732, 733, 734 , 735,
      new BrowserQueryFilter(
        'name736', ['gene737', 'gene738'], ['effectType739', 'effectType740'],
        ['gender741', 'gender742'], new PersonSetCollection('id743', ['744', '745']),
        ['studyType746', 'studyType747'], ['variant748', 'variant749']
      ),
      new BrowserQueryFilter(
        'name760', ['gene761', 'gene762'], ['effectType763', 'effectType764'],
        ['gender765', 'gender766'], new PersonSetCollection('id767', ['768', '769']),
        ['studyType770', 'studyType771'], ['variant772', 'variant773']
      )
    ),
    new EnrichmentTestResult('name784', 785, 786, 787 , 788,
      new BrowserQueryFilter(
        'name789', ['gene790', 'gene791'], ['effectType792', 'effectType793'],
        ['gender794', 'gender795'], new PersonSetCollection('id796', ['797', '798']),
        ['studyType799', 'studyType800'], ['variant801', 'variant802']
      ),
      new BrowserQueryFilter(
        'name813', ['gene814', 'gene815'], ['effectType816', 'effectType817'],
        ['gender818', 'gender819'], new PersonSetCollection('id820', ['821', '822']),
        ['studyType823', 'studyType824'], ['variant825', 'variant826']
      )
    )
  ),
  new EnrichmentEffectResult(
    new EnrichmentTestResult('name837', 838, 839, 840, 841,
      new BrowserQueryFilter(
        'name837', ['gene838', 'gene839'], ['effectType840', 'effectType841'],
        ['gender842', 'gender843'], new PersonSetCollection('id844', ['845', '846']),
        ['studyType847', 'studyType848'], ['variant849', 'variant850']
      ),
      new BrowserQueryFilter(
        'name861', ['gene862', 'gene863'], ['effectType864', 'effectType865'],
        ['gender866', 'gender867'], new PersonSetCollection('id868', ['869', '870']),
        ['studyType871', 'studyType872'], ['variant873', 'variant874']
      )
    ),
    new EnrichmentTestResult('name885', 886, 887, 888, 889,
      new BrowserQueryFilter(
        'name890', ['gene891', 'gene892'], ['effectType893', 'effectType894'],
        ['gender895', 'gender896'], new PersonSetCollection('id897', ['898', '899']),
        ['studyType900', 'studyType901'], ['variant902', 'variant903']
      ),
      new BrowserQueryFilter(
        'name914', ['gene915', 'gene916'], ['effectType917', 'effectType918'],
        ['gender919', 'gender920'], new PersonSetCollection('id921', ['922', '923']),
        ['studyType924', 'studyType925'], ['variant926', 'variant927']
      )
    ),
    new EnrichmentTestResult('name938', 939, 940, 941 , 942,
      new BrowserQueryFilter(
        'name943', ['gene944', 'gene945'], ['effectType946', 'effectType947'],
        ['gender948', 'gender949'], new PersonSetCollection('id950', ['951', '952']),
        ['studyType953', 'studyType954'], ['variant955', 'variant956']
      ),
      new BrowserQueryFilter(
        'name967', ['gene968', 'gene969'], ['effectType970', 'effectType971'],
        ['gender972', 'gender973'], new PersonSetCollection('id974', ['975', '976']),
        ['studyType977', 'studyType978'], ['variant979', 'variant980']
      )
    ),
    new EnrichmentTestResult('name991', 992, 993, 994 , 995,
      new BrowserQueryFilter(
        'name996', ['gene997', 'gene998'], ['effectType999', 'effectType1000'],
        ['gender1001', 'gender1002'], new PersonSetCollection('id1003', ['1004', '1005']),
        ['studyType1006', 'studyType1007'], ['variant1008', 'variant1009']
      ),
      new BrowserQueryFilter(
        'name1020', ['gene1021', 'gene1022'], ['effectType1023', 'effectType1024'],
        ['gender1025', 'gender1026'], new PersonSetCollection('id1027', ['1028', '1029']),
        ['studyType1030', 'studyType1031'], ['variant1032', 'variant1033']
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
        gender: [ 'gender59', 'gender60' ], peopleGroup: { id: 'id61', checkedValues: [ '62', '63' ] },
        studyTypes: [ 'studyType64', 'studyType65' ], variantTypes: [ 'variant66', 'variant67' ]
      },
      overlapFilter:
      {
        datasetId: 'name78', geneSymbols: [ 'gene79', 'gene80' ], effectTypes: [ 'effectType81', 'effectType82' ],
        gender: [ 'gender83', 'gender84' ], peopleGroup: { id: 'id85', checkedValues: [ '86', '87' ] },
        studyTypes: [ 'studyType88', 'studyType89' ], variantTypes: [ 'variant90', 'variant91' ]
      }
    }, female: {
      name: 'name102', count: 103, expected: 104, overlapped: 105, pvalue: 106,
      countFilter:
      {
        datasetId: 'name107', geneSymbols: [ 'gene108', 'gene109' ],
        effectTypes: [ 'effectType110', 'effectType111' ],
        gender: [ 'gender112', 'gender113' ], peopleGroup: { id: 'id114', checkedValues: [ '115', '116' ] },
        studyTypes: [ 'studyType117', 'studyType118' ], variantTypes: [ 'variant119', 'variant120' ]
      },
      overlapFilter:
      {
        datasetId: 'name131', geneSymbols: [ 'gene132', 'gene133' ],
        effectTypes: [ 'effectType134', 'effectType135' ],
        gender: [ 'gender136', 'gender137' ], peopleGroup: { id: 'id138', checkedValues: [ '139', '140' ] },
        studyTypes: [ 'studyType141', 'studyType142' ], variantTypes: [ 'variant143', 'variant144' ]
      }
    }, rec: {
      name: 'name155', count: 156, expected: 157, overlapped: 158, pvalue: 159,
      countFilter:
      {
        datasetId: 'name160', geneSymbols: [ 'gene161', 'gene162' ],
        effectTypes: [ 'effectType163', 'effectType164' ],
        gender: [ 'gender165', 'gender166' ], peopleGroup: { id: 'id167', checkedValues: [ '168', '169' ] },
        studyTypes: [ 'studyType170', 'studyType171' ], variantTypes: [ 'variant172', 'variant173' ]
      },
      overlapFilter:
      {
        datasetId: 'name184', geneSymbols: [ 'gene185', 'gene186' ],
        effectTypes: [ 'effectType187', 'effectType188' ],
        gender: [ 'gender189', 'gender190' ], peopleGroup: { id: 'id191', checkedValues: [ '192', '193' ] },
        studyTypes: [ 'studyType194', 'studyType195' ], variantTypes: [ 'variant196', 'variant197' ]
      }
    }
  }, missense: {
    all: {
      name: 'name208', count: 209, expected: 210, overlapped: 211, pvalue: 212,
      countFilter:
      {
        datasetId: 'name208', geneSymbols: [ 'gene209', 'gene210' ],
        effectTypes: [ 'effectType211', 'effectType212' ],
        gender: [ 'gender213', 'gender214' ], peopleGroup: { id: 'id215', checkedValues: [ '216', '217' ] },
        studyTypes: [ 'studyType218', 'studyType219' ], variantTypes: [ 'variant220', 'variant221' ]
      },
      overlapFilter:
      {
        datasetId: 'name232', geneSymbols: [ 'gene233', 'gene234' ],
        effectTypes: [ 'effectType235', 'effectType236' ],
        gender: [ 'gender237', 'gender238' ],
        peopleGroup: { id: 'id239', checkedValues: [ '240', '241' ] },
        studyTypes: [ 'studyType242', 'studyType243' ], variantTypes: [ 'variant244', 'variant245' ]
      },
    }, male: {
      name: 'name256', count: 257, expected: 258, overlapped: 259, pvalue: 260,
      countFilter:
      {
        datasetId: 'name261', geneSymbols: [ 'gene262', 'gene263' ],
        effectTypes: [ 'effectType264', 'effectType265' ],
        gender: [ 'gender266', 'gender267' ], peopleGroup: { id: 'id268', checkedValues: [ '269', '270' ] },
        studyTypes: [ 'studyType271', 'studyType272' ], variantTypes: [ 'variant273', 'variant274' ]
      },
      overlapFilter:
      {
        datasetId: 'name285', geneSymbols: [ 'gene286', 'gene287' ],
        effectTypes: [ 'effectType288', 'effectType289' ],
        gender: [ 'gender290', 'gender291' ], peopleGroup: { id: 'id292', checkedValues: [ '293', '294' ] },
        studyTypes: [ 'studyType295', 'studyType296' ], variantTypes: [ 'variant297', 'variant298' ]
      }
    }, female: {
      name: 'name309', count: 310, expected: 311, overlapped: 312, pvalue: 313,
      countFilter:
      {
        datasetId: 'name314', geneSymbols: [ 'gene315', 'gene316' ],
        effectTypes: [ 'effectType317', 'effectType318' ],
        gender: [ 'gender319', 'gender320' ], peopleGroup: { id: 'id321', checkedValues: [ '322', '323' ] },
        studyTypes: [ 'studyType324', 'studyType325' ], variantTypes: [ 'variant326', 'variant327' ]
      },
      overlapFilter:
      {
        datasetId: 'name338', geneSymbols: [ 'gene339', 'gene340' ],
        effectTypes: [ 'effectType341', 'effectType342' ],
        gender: [ 'gender343', 'gender344' ], peopleGroup: { id: 'id345', checkedValues: [ '346', '347' ] },
        studyTypes: [ 'studyType348', 'studyType349' ], variantTypes: [ 'variant350', 'variant351' ]
      }
    }, rec: {
      name: 'name362', count: 363, expected: 364, overlapped: 365, pvalue: 366,
      countFilter:
      {
        datasetId: 'name367', geneSymbols: [ 'gene368', 'gene369' ],
        effectTypes: [ 'effectType370', 'effectType371' ],
        gender: [ 'gender372', 'gender373' ], peopleGroup: { id: 'id374', checkedValues: [ '375', '376' ] },
        studyTypes: [ 'studyType377', 'studyType378' ], variantTypes: [ 'variant379', 'variant380' ]
      },
      overlapFilter:
      {
        datasetId: 'name391', geneSymbols: [ 'gene392', 'gene393' ],
        effectTypes: [ 'effectType394', 'effectType395' ],
        gender: [ 'gender396', 'gender397' ], peopleGroup: { id: 'id398', checkedValues: [ '399', '400' ] },
        studyTypes: [ 'studyType401', 'studyType402' ], variantTypes: [ 'variant403', 'variant404' ]
      }
    }
  }, synonymous: {
    all: {
      name: 'name415', count: 416, expected: 417, overlapped: 418, pvalue: 419,
      countFilter:
      {
        datasetId: 'name415', geneSymbols: [ 'gene416', 'gene417' ],
        effectTypes: [ 'effectType418', 'effectType419' ],
        gender: [ 'gender420', 'gender421' ], peopleGroup: { id: 'id422', checkedValues: [ '423', '424' ] },
        studyTypes: [ 'studyType425', 'studyType426' ], variantTypes: [ 'variant427', 'variant428' ]
      },
      overlapFilter:
      {
        datasetId: 'name439', geneSymbols: [ 'gene440', 'gene441' ],
        effectTypes: [ 'effectType442', 'effectType443' ],
        gender: [ 'gender444', 'gender445' ],
        peopleGroup: { id: 'id446', checkedValues: [ '447', '448' ] },
        studyTypes: [ 'studyType449', 'studyType450' ], variantTypes: [ 'variant451', 'variant452' ]
      },
    }, male: {
      name: 'name463', count: 464, expected: 465, overlapped: 466, pvalue: 467,
      countFilter:
      {
        datasetId: 'name468', geneSymbols: [ 'gene469', 'gene470' ],
        effectTypes: [ 'effectType471', 'effectType472' ],
        gender: [ 'gender473', 'gender474' ], peopleGroup: { id: 'id475', checkedValues: [ '476', '477' ] },
        studyTypes: [ 'studyType478', 'studyType479' ], variantTypes: [ 'variant480', 'variant481' ]
      },
      overlapFilter:
      {
        datasetId: 'name492', geneSymbols: [ 'gene493', 'gene494' ],
        effectTypes: [ 'effectType495', 'effectType496' ],
        gender: [ 'gender497', 'gender498' ], peopleGroup: { id: 'id499', checkedValues: [ '500', '501' ] },
        studyTypes: [ 'studyType502', 'studyType503' ], variantTypes: [ 'variant504', 'variant505' ]
      }
    }, female: {
      name: 'name516', count: 517, expected: 518, overlapped: 519, pvalue: 520,
      countFilter:
      {
        datasetId: 'name521', geneSymbols: [ 'gene522', 'gene523' ],
        effectTypes: [ 'effectType524', 'effectType525' ],
        gender: [ 'gender526', 'gender527' ], peopleGroup: { id: 'id528', checkedValues: [ '529', '530' ] },
        studyTypes: [ 'studyType531', 'studyType532' ], variantTypes: [ 'variant533', 'variant534' ]
      },
      overlapFilter:
      {
        datasetId: 'name545', geneSymbols: [ 'gene546', 'gene547' ],
        effectTypes: [ 'effectType548', 'effectType549' ],
        gender: [ 'gender550', 'gender551' ], peopleGroup: { id: 'id552', checkedValues: [ '553', '554' ] },
        studyTypes: [ 'studyType555', 'studyType556' ], variantTypes: [ 'variant557', 'variant558' ]
      }
    }, rec: {
      name: 'name569', count: 570, expected: 571, overlapped: 572, pvalue: 573,
      countFilter:
      {
        datasetId: 'name574', geneSymbols: [ 'gene575', 'gene576' ],
        effectTypes: [ 'effectType577', 'effectType578' ],
        gender: [ 'gender579', 'gender580' ], peopleGroup: { id: 'id581', checkedValues: [ '582', '583' ] },
        studyTypes: [ 'studyType584', 'studyType585' ], variantTypes: [ 'variant586', 'variant587' ]
      },
      overlapFilter:
      {
        datasetId: 'name598', geneSymbols: [ 'gene599', 'gene600' ],
        effectTypes: [ 'effectType601', 'effectType602' ],
        gender: [ 'gender603', 'gender604' ], peopleGroup: { id: 'id605', checkedValues: [ '606', '607' ] },
        studyTypes: [ 'studyType608', 'studyType609' ], variantTypes: [ 'variant610', 'variant611' ]
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
        gender: [ 'gender428', 'gender429' ], peopleGroup: { id: 'id430', checkedValues: [ '431', '432' ] },
        studyTypes: [ 'studyType433', 'studyType434' ], variantTypes: [ 'variant435', 'variant436' ]
      },
      overlapFilter:
      {
        datasetId: 'name447', geneSymbols: [ 'gene448', 'gene449' ], effectTypes: [ 'effectType450', 'effectType451' ],
        gender: [ 'gender452', 'gender453' ],
        peopleGroup: { id: 'id454', checkedValues: [ '455', '456' ] },
        studyTypes: [ 'studyType457', 'studyType458' ], variantTypes: [ 'variant459', 'variant460' ]
      },
    }, male: {
      name: 'name471', count: 472, expected: 473, overlapped: 474, pvalue: 475,
      countFilter:
      {
        datasetId: 'name476', geneSymbols: [ 'gene477', 'gene478' ], effectTypes: [ 'effectType479', 'effectType480' ],
        gender: [ 'gender481', 'gender482' ], peopleGroup: { id: 'id483', checkedValues: [ '484', '485' ] },
        studyTypes: [ 'studyType486', 'studyType487' ], variantTypes: [ 'variant488', 'variant489' ]
      },
      overlapFilter:
      {
        datasetId: 'name500', geneSymbols: [ 'gene501', 'gene502' ], effectTypes: [ 'effectType503', 'effectType504' ],
        gender: [ 'gender505', 'gender506' ], peopleGroup: { id: 'id507', checkedValues: [ '508', '509' ] },
        studyTypes: [ 'studyType510', 'studyType511' ], variantTypes: [ 'variant512', 'variant513' ]
      }
    }, female: {
      name: 'name524', count: 525, expected: 526, overlapped: 527, pvalue: 528,
      countFilter:
      {
        datasetId: 'name529', geneSymbols: [ 'gene530', 'gene531' ],
        effectTypes: [ 'effectType532', 'effectType533' ],
        gender: [ 'gender534', 'gender535' ], peopleGroup: { id: 'id536', checkedValues: [ '537', '538' ] },
        studyTypes: [ 'studyType539', 'studyType540' ], variantTypes: [ 'variant541', 'variant542' ]
      },
      overlapFilter:
      {
        datasetId: 'name553', geneSymbols: [ 'gene554', 'gene555' ],
        effectTypes: [ 'effectType556', 'effectType557' ],
        gender: [ 'gender558', 'gender559' ], peopleGroup: { id: 'id560', checkedValues: [ '561', '562' ] },
        studyTypes: [ 'studyType563', 'studyType564' ], variantTypes: [ 'variant565', 'variant566' ]
      }
    }, rec: {
      name: 'name577', count: 578, expected: 579, overlapped: 580, pvalue: 581,
      countFilter:
      {
        datasetId: 'name582', geneSymbols: [ 'gene583', 'gene584' ],
        effectTypes: [ 'effectType585', 'effectType586' ],
        gender: [ 'gender587', 'gender588' ], peopleGroup: { id: 'id589', checkedValues: [ '590', '591' ] },
        studyTypes: [ 'studyType592', 'studyType593' ], variantTypes: [ 'variant594', 'variant595' ]
      },
      overlapFilter:
      {
        datasetId: 'name606', geneSymbols: [ 'gene607', 'gene608' ],
        effectTypes: [ 'effectType609', 'effectType610' ],
        gender: [ 'gender611', 'gender612' ], peopleGroup: { id: 'id613', checkedValues: [ '614', '615' ] },
        studyTypes: [ 'studyType616', 'studyType617' ], variantTypes: [ 'variant618', 'variant619' ]
      }
    }
  }, missense: {
    all: {
      name: 'name630', count: 631, expected: 632, overlapped: 633, pvalue: 634,
      countFilter:
      {
        datasetId: 'name630', geneSymbols: [ 'gene631', 'gene632' ],
        effectTypes: [ 'effectType633', 'effectType634' ],
        gender: [ 'gender635', 'gender636' ], peopleGroup: { id: 'id637', checkedValues: [ '638', '639' ] },
        studyTypes: [ 'studyType640', 'studyType641' ], variantTypes: [ 'variant642', 'variant643' ]
      },
      overlapFilter:
      {
        datasetId: 'name654', geneSymbols: [ 'gene655', 'gene656' ],
        effectTypes: [ 'effectType657', 'effectType658' ],
        gender: [ 'gender659', 'gender660' ],
        peopleGroup: { id: 'id661', checkedValues: [ '662', '663' ] },
        studyTypes: [ 'studyType664', 'studyType665' ], variantTypes: [ 'variant666', 'variant667' ]
      },
    }, male: {
      name: 'name678', count: 679, expected: 680, overlapped: 681, pvalue: 682,
      countFilter:
      {
        datasetId: 'name683', geneSymbols: [ 'gene684', 'gene685' ],
        effectTypes: [ 'effectType686', 'effectType687' ],
        gender: [ 'gender688', 'gender689' ], peopleGroup: { id: 'id690', checkedValues: [ '691', '692' ] },
        studyTypes: [ 'studyType693', 'studyType694' ], variantTypes: [ 'variant695', 'variant696' ]
      },
      overlapFilter:
      {
        datasetId: 'name707', geneSymbols: [ 'gene708', 'gene709' ],
        effectTypes: [ 'effectType710', 'effectType711' ],
        gender: [ 'gender712', 'gender713' ], peopleGroup: { id: 'id714', checkedValues: [ '715', '716' ] },
        studyTypes: [ 'studyType717', 'studyType718' ], variantTypes: [ 'variant719', 'variant720' ]
      }
    }, female: {
      name: 'name731', count: 732, expected: 733, overlapped: 734, pvalue: 735,
      countFilter:
      {
        datasetId: 'name736', geneSymbols: [ 'gene737', 'gene738' ],
        effectTypes: [ 'effectType739', 'effectType740' ],
        gender: [ 'gender741', 'gender742' ], peopleGroup: { id: 'id743', checkedValues: [ '744', '745' ] },
        studyTypes: [ 'studyType746', 'studyType747' ], variantTypes: [ 'variant748', 'variant749' ]
      },
      overlapFilter:
      {
        datasetId: 'name760', geneSymbols: [ 'gene761', 'gene762' ],
        effectTypes: [ 'effectType763', 'effectType764' ],
        gender: [ 'gender765', 'gender766' ], peopleGroup: { id: 'id767', checkedValues: [ '768', '769' ] },
        studyTypes: [ 'studyType770', 'studyType771' ], variantTypes: [ 'variant772', 'variant773' ]
      }
    }, rec: {
      name: 'name784', count: 785, expected: 786, overlapped: 787, pvalue: 788,
      countFilter:
      {
        datasetId: 'name789', geneSymbols: [ 'gene790', 'gene791' ],
        effectTypes: [ 'effectType792', 'effectType793' ],
        gender: [ 'gender794', 'gender795' ], peopleGroup: { id: 'id796', checkedValues: [ '797', '798' ] },
        studyTypes: [ 'studyType799', 'studyType800' ], variantTypes: [ 'variant801', 'variant802' ]
      },
      overlapFilter:
      {
        datasetId: 'name813', geneSymbols: [ 'gene814', 'gene815' ],
        effectTypes: [ 'effectType816', 'effectType817' ],
        gender: [ 'gender818', 'gender819' ], peopleGroup: { id: 'id820', checkedValues: [ '821', '822' ] },
        studyTypes: [ 'studyType823', 'studyType824' ], variantTypes: [ 'variant825', 'variant826' ]
      }
    }
  }, synonymous: {
    all: {
      name: 'name837', count: 838, expected: 839, overlapped: 840, pvalue: 841,
      countFilter:
      {
        datasetId: 'name837', geneSymbols: [ 'gene838', 'gene839' ],
        effectTypes: [ 'effectType840', 'effectType841' ],
        gender: [ 'gender842', 'gender843' ], peopleGroup: { id: 'id844', checkedValues: [ '845', '846' ] },
        studyTypes: [ 'studyType847', 'studyType848' ], variantTypes: [ 'variant849', 'variant850' ]
      },
      overlapFilter:
      {
        datasetId: 'name861', geneSymbols: [ 'gene862', 'gene863' ],
        effectTypes: [ 'effectType864', 'effectType865' ],
        gender: [ 'gender866', 'gender867' ],
        peopleGroup: { id: 'id868', checkedValues: [ '869', '870' ] },
        studyTypes: [ 'studyType871', 'studyType872' ], variantTypes: [ 'variant873', 'variant874' ]
      },
    }, male: {
      name: 'name885', count: 886, expected: 887, overlapped: 888, pvalue: 889,
      countFilter:
      {
        datasetId: 'name890', geneSymbols: [ 'gene891', 'gene892' ],
        effectTypes: [ 'effectType893', 'effectType894' ],
        gender: [ 'gender895', 'gender896' ], peopleGroup: { id: 'id897', checkedValues: [ '898', '899' ] },
        studyTypes: [ 'studyType900', 'studyType901' ], variantTypes: [ 'variant902', 'variant903' ]
      },
      overlapFilter:
      {
        datasetId: 'name914', geneSymbols: [ 'gene915', 'gene916' ],
        effectTypes: [ 'effectType917', 'effectType918' ],
        gender: [ 'gender919', 'gender920' ], peopleGroup: { id: 'id921', checkedValues: [ '922', '923' ] },
        studyTypes: [ 'studyType924', 'studyType925' ], variantTypes: [ 'variant926', 'variant927' ]
      }
    }, female: {
      name: 'name938', count: 939, expected: 940, overlapped: 941, pvalue: 942,
      countFilter:
      {
        datasetId: 'name943', geneSymbols: [ 'gene944', 'gene945' ],
        effectTypes: [ 'effectType946', 'effectType947' ],
        gender: [ 'gender948', 'gender949' ], peopleGroup: { id: 'id950', checkedValues: [ '951', '952' ] },
        studyTypes: [ 'studyType953', 'studyType954' ], variantTypes: [ 'variant955', 'variant956' ]
      },
      overlapFilter:
      {
        datasetId: 'name967', geneSymbols: [ 'gene968', 'gene969' ],
        effectTypes: [ 'effectType970', 'effectType971' ],
        gender: [ 'gender972', 'gender973' ], peopleGroup: { id: 'id974', checkedValues: [ '975', '976' ] },
        studyTypes: [ 'studyType977', 'studyType978' ], variantTypes: [ 'variant979', 'variant980' ]
      }
    }, rec: {
      name: 'name991', count: 992, expected: 993, overlapped: 994, pvalue: 995,
      countFilter:
      {
        datasetId: 'name996', geneSymbols: [ 'gene997', 'gene998' ],
        effectTypes: [ 'effectType999', 'effectType1000' ],
        gender: [ 'gender1001', 'gender1002' ],
        peopleGroup: { id: 'id1003', checkedValues: [ '1004', '1005' ] },
        studyTypes: [ 'studyType1006', 'studyType1007' ], variantTypes: [ 'variant1008', 'variant1009' ]
      },
      overlapFilter:
      {
        datasetId: 'name1020', geneSymbols: [ 'gene1021', 'gene1022' ],
        effectTypes: [ 'effectType1023', 'effectType1024' ],
        gender: [ 'gender1025', 'gender1026' ],
        peopleGroup: { id: 'id1027', checkedValues: [ '1028', '1029' ] },
        studyTypes: [ 'studyType1030', 'studyType1031' ], variantTypes: [ 'variant1032', 'variant1033' ]
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
