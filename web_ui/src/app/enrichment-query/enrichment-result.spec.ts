import { BrowserQueryFilter, PersonSetCollection } from 'app/genotype-browser/genotype-browser';
import { ChildrenStats, EnrichmentEffectResult, EnrichmentResult, EnrichmentTestResult } from './enrichment-result';

describe('ChildrenStats', () => {
  it('should create from json', () => {
    const childrenStatsMock = new ChildrenStats(1, 2, 3);

    const childrenStatsMockFromJson = ChildrenStats.fromJson({
      M: 1, // eslint-disable-line
      F: 2, // eslint-disable-line
      U: 3 // eslint-disable-line
    });

    expect(childrenStatsMock).toStrictEqual(childrenStatsMockFromJson);
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
    datasetId: 'name1', geneSymbols: ['gene2', 'gene3'], effectTypes: ['effectType4', 'effectType5'],
    gender: ['gender6', 'gender7'], peopleGroup: { id: 'id8', checkedValues: ['9', '10'] },
    studyTypes: ['studyType11', 'studyType12'], variantTypes: ['variant13', 'variant14']
  },
  {
    datasetId: 'name25', geneSymbols: ['gene26', 'gene27'], effectTypes: ['effectType28', 'effectType29'],
    gender: ['gender30', 'gender31'],
    peopleGroup: { id: 'id32', checkedValues: ['33', '34'] },
    studyTypes: ['studyType35', 'studyType36'], variantTypes: ['variant37', 'variant38']
  }
];

const enrichmentEffectResultMock = new EnrichmentEffectResult(
  new EnrichmentTestResult('name0', 2, 3, 4, 5, browserQueryFilterMock1, browserQueryFilterMock2),
  new EnrichmentTestResult('name39', 40, 41, 42, 43,
    new BrowserQueryFilter(
      'name44', ['gene45', 'gene46'], ['effectType47', 'effectType48'],
      ['gender49', 'gender50'], new PersonSetCollection('id51', ['52', '53']),
      ['studyType54', 'studyType55'], ['variant56', 'variant57']
    ),
    new BrowserQueryFilter(
      'name58', ['gene59', 'gene60'], ['effectType61', 'effectType62'],
      ['gender63', 'gender64'], new PersonSetCollection('id65', ['66', '67']),
      ['studyType68', 'studyType69'], ['variant70', 'variant71']
    )
  ),
  new EnrichmentTestResult('name72', 73, 74, 75, 76,
    new BrowserQueryFilter(
      'name77', ['gene78', 'gene79'], ['effectType80', 'effectType81'],
      ['gender82', 'gender83'], new PersonSetCollection('id84', ['85', '86']),
      ['studyType87', 'studyType88'], ['variant89', 'variant90']
    ),
    new BrowserQueryFilter(
      'name91', ['gene92', 'gene93'], ['effectType94', 'effectType95'],
      ['gender96', 'gender97'], new PersonSetCollection('id98', ['99', '100']),
      ['studyType101', 'studyType102'], ['variant103', 'variant104']
    )
  )
);

const enrichmentEffectResultMockFromJson = {
  all: {
    name: 'name0', count: 2, expected: 3, overlapped: 4, pvalue: 5,
    countFilter: browserQueryFilterMockFromJson1,
    overlapFilter: browserQueryFilterMockFromJson2
  }, male: {
    name: 'name39', count: 40, expected: 41, overlapped: 42, pvalue: 43,
    countFilter:
    {
      datasetId: 'name44', geneSymbols: ['gene45', 'gene46'], effectTypes: ['effectType47', 'effectType48'],
      gender: ['gender49', 'gender50'], peopleGroup: { id: 'id51', checkedValues: ['52', '53'] },
      studyTypes: ['studyType54', 'studyType55'], variantTypes: ['variant56', 'variant57']
    },
    overlapFilter:
    {
      datasetId: 'name58', geneSymbols: ['gene59', 'gene60'], effectTypes: ['effectType61', 'effectType62'],
      gender: ['gender63', 'gender64'], peopleGroup: { id: 'id65', checkedValues: ['66', '67'] },
      studyTypes: ['studyType68', 'studyType69'], variantTypes: ['variant70', 'variant71']
    }
  }, female: {
    name: 'name72', count: 73, expected: 74, overlapped: 75, pvalue: 76,
    countFilter:
    {
      datasetId: 'name77', geneSymbols: ['gene78', 'gene79'],
      effectTypes: ['effectType80', 'effectType81'],
      gender: ['gender82', 'gender83'], peopleGroup: { id: 'id84', checkedValues: ['85', '86'] },
      studyTypes: ['studyType87', 'studyType88'], variantTypes: ['variant89', 'variant90']
    },
    overlapFilter:
    {
      datasetId: 'name91', geneSymbols: ['gene92', 'gene93'],
      effectTypes: ['effectType94', 'effectType95'],
      gender: ['gender96', 'gender97'], peopleGroup: { id: 'id98', checkedValues: ['99', '100'] },
      studyTypes: ['studyType101', 'studyType102'], variantTypes: ['variant103', 'variant104']
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
    expect(enrichmentTestResultMock).toStrictEqual(enrichmentTestResultFromJson);
  });
});

describe('EnrichmentEffectResult', () => {
  it('should create from json', () => {
    expect(enrichmentEffectResultMock).toStrictEqual(
      EnrichmentEffectResult.fromJson(enrichmentEffectResultMockFromJson)
    );
  });
}
);

const enrichmentResult1 = new EnrichmentResult('selector1', enrichmentEffectResultMock,
  new EnrichmentEffectResult(
    new EnrichmentTestResult('name138', 139, 140, 141, 142,
      new BrowserQueryFilter(
        'name139', ['gene140', 'gene141'], ['effectType142', 'effectType143'],
        ['gender144', 'gender145'], new PersonSetCollection('id146', ['147', '148']),
        ['studyType149', 'studyType150'], ['variant151', 'variant152']
      ),
      new BrowserQueryFilter(
        'name153', ['gene154', 'gene155'], ['effectType156', 'effectType157'],
        ['gender158', 'gender159'], new PersonSetCollection('id160', ['161', '162']),
        ['studyType163', 'studyType164'], ['variant165', 'variant166']
      )
    ),
    new EnrichmentTestResult('name167', 168, 169, 170, 171,
      new BrowserQueryFilter(
        'name172', ['gene173', 'gene174'], ['effectType175', 'effectType176'],
        ['gender177', 'gender178'], new PersonSetCollection('id179', ['180', '181']),
        ['studyType182', 'studyType183'], ['variant184', 'variant185']
      ),
      new BrowserQueryFilter(
        'name186', ['gene187', 'gene188'], ['effectType189', 'effectType190'],
        ['gender191', 'gender192'], new PersonSetCollection('id193', ['194', '195']),
        ['studyType196', 'studyType197'], ['variant198', 'variant199']
      )
    ),
    new EnrichmentTestResult('name200', 201, 202, 203, 204,
      new BrowserQueryFilter(
        'name205', ['gene206', 'gene207'], ['effectType208', 'effectType209'],
        ['gender210', 'gender211'], new PersonSetCollection('id212', ['213', '214']),
        ['studyType215', 'studyType216'], ['variant217', 'variant218']
      ),
      new BrowserQueryFilter(
        'name219', ['gene220', 'gene221'], ['effectType222', 'effectType223'],
        ['gender224', 'gender225'], new PersonSetCollection('id226', ['227', '228']),
        ['studyType229', 'studyType230'], ['variant231', 'variant232']
      )
    )
  ), new EnrichmentEffectResult(
    new EnrichmentTestResult('name266', 267, 268, 269, 270,
      new BrowserQueryFilter(
        'name266', ['gene267', 'gene268'], ['effectType269', 'effectType270'],
        ['gender271', 'gender272'], new PersonSetCollection('id273', ['274', '275']),
        ['studyType276', 'studyType277'], ['variant278', 'variant279']
      ),
      new BrowserQueryFilter(
        'name280', ['gene281', 'gene282'], ['effectType283', 'effectType284'],
        ['gender285', 'gender286'], new PersonSetCollection('id287', ['288', '289']),
        ['studyType290', 'studyType291'], ['variant292', 'variant293']
      )
    ),
    new EnrichmentTestResult('name294', 295, 296, 297, 298,
      new BrowserQueryFilter(
        'name299', ['gene300', 'gene301'], ['effectType302', 'effectType303'],
        ['gender304', 'gender305'], new PersonSetCollection('id306', ['307', '308']),
        ['studyType309', 'studyType310'], ['variant311', 'variant312']
      ),
      new BrowserQueryFilter(
        'name313', ['gene314', 'gene315'], ['effectType316', 'effectType317'],
        ['gender318', 'gender319'], new PersonSetCollection('id320', ['321', '322']),
        ['studyType323', 'studyType324'], ['variant325', 'variant326']
      )
    ),
    new EnrichmentTestResult('name327', 328, 329, 330, 331,
      new BrowserQueryFilter(
        'name332', ['gene333', 'gene334'], ['effectType335', 'effectType336'],
        ['gender337', 'gender338'], new PersonSetCollection('id339', ['340', '341']),
        ['studyType342', 'studyType343'], ['variant344', 'variant345']
      ),
      new BrowserQueryFilter(
        'name346', ['gene347', 'gene348'], ['effectType349', 'effectType350'],
        ['gender351', 'gender352'], new PersonSetCollection('id353', ['354', '355']),
        ['studyType356', 'studyType357'], ['variant358', 'variant359']
      )
    )
  ), new ChildrenStats(393, 394, 395)
);

const enrichmentResult2 = new EnrichmentResult('selector396',
  new EnrichmentEffectResult(
    new EnrichmentTestResult('name396', 397, 398, 399, 400,
      new BrowserQueryFilter(
        'name401', ['gene402', 'gene403'], ['effectType404', 'effectType405'],
        ['gender406', 'gender407'], new PersonSetCollection('id408', ['409', '410']),
        ['studyType411', 'studyType412'], ['variant413', 'variant414']
      ),
      new BrowserQueryFilter(
        'name415', ['gene416', 'gene417'], ['effectType418', 'effectType419'],
        ['gender420', 'gender421'], new PersonSetCollection('id422', ['423', '424']),
        ['studyType425', 'studyType426'], ['variant427', 'variant428']
      )
    ),
    new EnrichmentTestResult('name429', 430, 431, 432, 433,
      new BrowserQueryFilter(
        'name434', ['gene435', 'gene436'], ['effectType437', 'effectType438'],
        ['gender439', 'gender440'], new PersonSetCollection('id441', ['442', '443']),
        ['studyType444', 'studyType445'], ['variant446', 'variant447']
      ),
      new BrowserQueryFilter(
        'name448', ['gene449', 'gene450'], ['effectType451', 'effectType452'],
        ['gender453', 'gender454'], new PersonSetCollection('id455', ['456', '457']),
        ['studyType458', 'studyType459'], ['variant460', 'variant461']
      )
    ),
    new EnrichmentTestResult('name462', 463, 464, 465, 466,
      new BrowserQueryFilter(
        'name467', ['gene468', 'gene469'], ['effectType470', 'effectType471'],
        ['gender472', 'gender473'], new PersonSetCollection('id474', ['475', '476']),
        ['studyType477', 'studyType478'], ['variant479', 'variant480']
      ),
      new BrowserQueryFilter(
        'name481', ['gene482', 'gene483'], ['effectType484', 'effectType485'],
        ['gender486', 'gender487'], new PersonSetCollection('id488', ['489', '490']),
        ['studyType491', 'studyType492'], ['variant493', 'variant494']
      )
    )
  ),
  new EnrichmentEffectResult(
    new EnrichmentTestResult('name528', 529, 530, 531, 532,
      new BrowserQueryFilter(
        'name528', ['gene529', 'gene530'], ['effectType531', 'effectType532'],
        ['gender533', 'gender534'], new PersonSetCollection('id535', ['536', '537']),
        ['studyType538', 'studyType539'], ['variant540', 'variant541']
      ),
      new BrowserQueryFilter(
        'name542', ['gene543', 'gene544'], ['effectType545', 'effectType546'],
        ['gender547', 'gender548'], new PersonSetCollection('id549', ['550', '551']),
        ['studyType552', 'studyType553'], ['variant554', 'variant555']
      )
    ),
    new EnrichmentTestResult('name556', 557, 558, 559, 560,
      new BrowserQueryFilter(
        'name561', ['gene562', 'gene563'], ['effectType564', 'effectType565'],
        ['gender566', 'gender567'], new PersonSetCollection('id568', ['569', '570']),
        ['studyType571', 'studyType572'], ['variant573', 'variant574']
      ),
      new BrowserQueryFilter(
        'name575', ['gene576', 'gene577'], ['effectType578', 'effectType579'],
        ['gender580', 'gender581'], new PersonSetCollection('id582', ['583', '584']),
        ['studyType585', 'studyType586'], ['variant587', 'variant588']
      )
    ),
    new EnrichmentTestResult('name589', 590, 591, 592, 593,
      new BrowserQueryFilter(
        'name594', ['gene595', 'gene596'], ['effectType597', 'effectType598'],
        ['gender599', 'gender600'], new PersonSetCollection('id601', ['602', '603']),
        ['studyType604', 'studyType605'], ['variant606', 'variant607']
      ),
      new BrowserQueryFilter(
        'name608', ['gene609', 'gene610'], ['effectType611', 'effectType612'],
        ['gender613', 'gender614'], new PersonSetCollection('id615', ['616', '617']),
        ['studyType618', 'studyType619'], ['variant620', 'variant621']
      )
    )
  ),
  new EnrichmentEffectResult(
    new EnrichmentTestResult('name655', 656, 657, 658, 659,
      new BrowserQueryFilter(
        'name655', ['gene656', 'gene657'], ['effectType658', 'effectType659'],
        ['gender660', 'gender661'], new PersonSetCollection('id662', ['663', '664']),
        ['studyType665', 'studyType666'], ['variant667', 'variant668']
      ),
      new BrowserQueryFilter(
        'name669', ['gene670', 'gene671'], ['effectType672', 'effectType673'],
        ['gender674', 'gender675'], new PersonSetCollection('id676', ['677', '678']),
        ['studyType679', 'studyType680'], ['variant681', 'variant682']
      )
    ),
    new EnrichmentTestResult('name683', 684, 685, 686, 687,
      new BrowserQueryFilter(
        'name688', ['gene689', 'gene690'], ['effectType691', 'effectType692'],
        ['gender693', 'gender694'], new PersonSetCollection('id695', ['696', '697']),
        ['studyType698', 'studyType699'], ['variant700', 'variant701']
      ),
      new BrowserQueryFilter(
        'name702', ['gene703', 'gene704'], ['effectType705', 'effectType706'],
        ['gender707', 'gender708'], new PersonSetCollection('id709', ['710', '711']),
        ['studyType712', 'studyType713'], ['variant714', 'variant715']
      )
    ),
    new EnrichmentTestResult('name716', 717, 718, 719, 720,
      new BrowserQueryFilter(
        'name721', ['gene722', 'gene723'], ['effectType724', 'effectType725'],
        ['gender726', 'gender727'], new PersonSetCollection('id728', ['729', '730']),
        ['studyType731', 'studyType732'], ['variant733', 'variant734']
      ),
      new BrowserQueryFilter(
        'name735', ['gene736', 'gene737'], ['effectType738', 'effectType739'],
        ['gender740', 'gender741'], new PersonSetCollection('id742', ['743', '744']),
        ['studyType745', 'studyType746'], ['variant747', 'variant748']
      )
    )
  ), new ChildrenStats(782, 783, 784)
);

const enrichmentResultFromJson1 = {
  selector: 'selector1',
  LGDs: enrichmentEffectResultMockFromJson, // eslint-disable-line
  missense: {
    all: {
      name: 'name138', count: 139, expected: 140, overlapped: 141, pvalue: 142,
      countFilter:
      {
        datasetId: 'name139', geneSymbols: ['gene140', 'gene141'],
        effectTypes: ['effectType142', 'effectType143'],
        gender: ['gender144', 'gender145'], peopleGroup: { id: 'id146', checkedValues: ['147', '148'] },
        studyTypes: ['studyType149', 'studyType150'], variantTypes: ['variant151', 'variant152']
      },
      overlapFilter:
      {
        datasetId: 'name153', geneSymbols: ['gene154', 'gene155'],
        effectTypes: ['effectType156', 'effectType157'],
        gender: ['gender158', 'gender159'],
        peopleGroup: { id: 'id160', checkedValues: ['161', '162'] },
        studyTypes: ['studyType163', 'studyType164'], variantTypes: ['variant165', 'variant166']
      },
    }, male: {
      name: 'name167', count: 168, expected: 169, overlapped: 170, pvalue: 171,
      countFilter:
      {
        datasetId: 'name172', geneSymbols: ['gene173', 'gene174'],
        effectTypes: ['effectType175', 'effectType176'],
        gender: ['gender177', 'gender178'], peopleGroup: { id: 'id179', checkedValues: ['180', '181'] },
        studyTypes: ['studyType182', 'studyType183'], variantTypes: ['variant184', 'variant185']
      },
      overlapFilter:
      {
        datasetId: 'name186', geneSymbols: ['gene187', 'gene188'],
        effectTypes: ['effectType189', 'effectType190'],
        gender: ['gender191', 'gender192'], peopleGroup: { id: 'id193', checkedValues: ['194', '195'] },
        studyTypes: ['studyType196', 'studyType197'], variantTypes: ['variant198', 'variant199']
      }
    }, female: {
      name: 'name200', count: 201, expected: 202, overlapped: 203, pvalue: 204,
      countFilter:
      {
        datasetId: 'name205', geneSymbols: ['gene206', 'gene207'],
        effectTypes: ['effectType208', 'effectType209'],
        gender: ['gender210', 'gender211'], peopleGroup: { id: 'id212', checkedValues: ['213', '214'] },
        studyTypes: ['studyType215', 'studyType216'], variantTypes: ['variant217', 'variant218']
      },
      overlapFilter:
      {
        datasetId: 'name219', geneSymbols: ['gene220', 'gene221'],
        effectTypes: ['effectType222', 'effectType223'],
        gender: ['gender224', 'gender225'], peopleGroup: { id: 'id226', checkedValues: ['227', '228'] },
        studyTypes: ['studyType229', 'studyType230'], variantTypes: ['variant231', 'variant232']
      }
    }
  }, synonymous: {
    all: {
      name: 'name266', count: 267, expected: 268, overlapped: 269, pvalue: 270,
      countFilter:
      {
        datasetId: 'name266', geneSymbols: ['gene267', 'gene268'],
        effectTypes: ['effectType269', 'effectType270'],
        gender: ['gender271', 'gender272'], peopleGroup: { id: 'id273', checkedValues: ['274', '275'] },
        studyTypes: ['studyType276', 'studyType277'], variantTypes: ['variant278', 'variant279']
      },
      overlapFilter:
      {
        datasetId: 'name280', geneSymbols: ['gene281', 'gene282'],
        effectTypes: ['effectType283', 'effectType284'],
        gender: ['gender285', 'gender286'],
        peopleGroup: { id: 'id287', checkedValues: ['288', '289'] },
        studyTypes: ['studyType290', 'studyType291'], variantTypes: ['variant292', 'variant293']
      },
    }, male: {
      name: 'name294', count: 295, expected: 296, overlapped: 297, pvalue: 298,
      countFilter:
      {
        datasetId: 'name299', geneSymbols: ['gene300', 'gene301'],
        effectTypes: ['effectType302', 'effectType303'],
        gender: ['gender304', 'gender305'], peopleGroup: { id: 'id306', checkedValues: ['307', '308'] },
        studyTypes: ['studyType309', 'studyType310'], variantTypes: ['variant311', 'variant312']
      },
      overlapFilter:
      {
        datasetId: 'name313', geneSymbols: ['gene314', 'gene315'],
        effectTypes: ['effectType316', 'effectType317'],
        gender: ['gender318', 'gender319'], peopleGroup: { id: 'id320', checkedValues: ['321', '322'] },
        studyTypes: ['studyType323', 'studyType324'], variantTypes: ['variant325', 'variant326']
      }
    }, female: {
      name: 'name327', count: 328, expected: 329, overlapped: 330, pvalue: 331,
      countFilter:
      {
        datasetId: 'name332', geneSymbols: ['gene333', 'gene334'],
        effectTypes: ['effectType335', 'effectType336'],
        gender: ['gender337', 'gender338'], peopleGroup: { id: 'id339', checkedValues: ['340', '341'] },
        studyTypes: ['studyType342', 'studyType343'], variantTypes: ['variant344', 'variant345']
      },
      overlapFilter:
      {
        datasetId: 'name346', geneSymbols: ['gene347', 'gene348'],
        effectTypes: ['effectType349', 'effectType350'],
        gender: ['gender351', 'gender352'], peopleGroup: { id: 'id353', checkedValues: ['354', '355'] },
        studyTypes: ['studyType356', 'studyType357'], variantTypes: ['variant358', 'variant359']
      }
    }
  },
  childrenStats: {
    M: 393, // eslint-disable-line
    F: 394, // eslint-disable-line
    U: 395 // eslint-disable-line
  }
};

const enrichmentResultFromJson2 = {
  selector: 'selector396',
  LGDs: { // eslint-disable-line
    all: {
      name: 'name396', count: 397, expected: 398, overlapped: 399, pvalue: 400,
      countFilter:
      {
        datasetId: 'name401', geneSymbols: ['gene402', 'gene403'], effectTypes: ['effectType404', 'effectType405'],
        gender: ['gender406', 'gender407'], peopleGroup: { id: 'id408', checkedValues: ['409', '410'] },
        studyTypes: ['studyType411', 'studyType412'], variantTypes: ['variant413', 'variant414']
      },
      overlapFilter:
      {
        datasetId: 'name415', geneSymbols: ['gene416', 'gene417'], effectTypes: ['effectType418', 'effectType419'],
        gender: ['gender420', 'gender421'],
        peopleGroup: { id: 'id422', checkedValues: ['423', '424'] },
        studyTypes: ['studyType425', 'studyType426'], variantTypes: ['variant427', 'variant428']
      },
    }, male: {
      name: 'name429', count: 430, expected: 431, overlapped: 432, pvalue: 433,
      countFilter:
      {
        datasetId: 'name434', geneSymbols: ['gene435', 'gene436'], effectTypes: ['effectType437', 'effectType438'],
        gender: ['gender439', 'gender440'], peopleGroup: { id: 'id441', checkedValues: ['442', '443'] },
        studyTypes: ['studyType444', 'studyType445'], variantTypes: ['variant446', 'variant447']
      },
      overlapFilter:
      {
        datasetId: 'name448', geneSymbols: ['gene449', 'gene450'], effectTypes: ['effectType451', 'effectType452'],
        gender: ['gender453', 'gender454'], peopleGroup: { id: 'id455', checkedValues: ['456', '457'] },
        studyTypes: ['studyType458', 'studyType459'], variantTypes: ['variant460', 'variant461']
      }
    }, female: {
      name: 'name462', count: 463, expected: 464, overlapped: 465, pvalue: 466,
      countFilter:
      {
        datasetId: 'name467', geneSymbols: ['gene468', 'gene469'],
        effectTypes: ['effectType470', 'effectType471'],
        gender: ['gender472', 'gender473'], peopleGroup: { id: 'id474', checkedValues: ['475', '476'] },
        studyTypes: ['studyType477', 'studyType478'], variantTypes: ['variant479', 'variant480']
      },
      overlapFilter:
      {
        datasetId: 'name481', geneSymbols: ['gene482', 'gene483'],
        effectTypes: ['effectType484', 'effectType485'],
        gender: ['gender486', 'gender487'], peopleGroup: { id: 'id488', checkedValues: ['489', '490'] },
        studyTypes: ['studyType491', 'studyType492'], variantTypes: ['variant493', 'variant494']
      }
    }
  }, missense: {
    all: {
      name: 'name528', count: 529, expected: 530, overlapped: 531, pvalue: 532,
      countFilter:
      {
        datasetId: 'name528', geneSymbols: ['gene529', 'gene530'],
        effectTypes: ['effectType531', 'effectType532'],
        gender: ['gender533', 'gender534'], peopleGroup: { id: 'id535', checkedValues: ['536', '537'] },
        studyTypes: ['studyType538', 'studyType539'], variantTypes: ['variant540', 'variant541']
      },
      overlapFilter:
      {
        datasetId: 'name542', geneSymbols: ['gene543', 'gene544'],
        effectTypes: ['effectType545', 'effectType546'],
        gender: ['gender547', 'gender548'],
        peopleGroup: { id: 'id549', checkedValues: ['550', '551'] },
        studyTypes: ['studyType552', 'studyType553'], variantTypes: ['variant554', 'variant555']
      },
    }, male: {
      name: 'name556', count: 557, expected: 558, overlapped: 559, pvalue: 560,
      countFilter:
      {
        datasetId: 'name561', geneSymbols: ['gene562', 'gene563'],
        effectTypes: ['effectType564', 'effectType565'],
        gender: ['gender566', 'gender567'], peopleGroup: { id: 'id568', checkedValues: ['569', '570'] },
        studyTypes: ['studyType571', 'studyType572'], variantTypes: ['variant573', 'variant574']
      },
      overlapFilter:
      {
        datasetId: 'name575', geneSymbols: ['gene576', 'gene577'],
        effectTypes: ['effectType578', 'effectType579'],
        gender: ['gender580', 'gender581'], peopleGroup: { id: 'id582', checkedValues: ['583', '584'] },
        studyTypes: ['studyType585', 'studyType586'], variantTypes: ['variant587', 'variant588']
      }
    }, female: {
      name: 'name589', count: 590, expected: 591, overlapped: 592, pvalue: 593,
      countFilter:
      {
        datasetId: 'name594', geneSymbols: ['gene595', 'gene596'],
        effectTypes: ['effectType597', 'effectType598'],
        gender: ['gender599', 'gender600'], peopleGroup: { id: 'id601', checkedValues: ['602', '603'] },
        studyTypes: ['studyType604', 'studyType605'], variantTypes: ['variant606', 'variant607']
      },
      overlapFilter:
      {
        datasetId: 'name608', geneSymbols: ['gene609', 'gene610'],
        effectTypes: ['effectType611', 'effectType612'],
        gender: ['gender613', 'gender614'], peopleGroup: { id: 'id615', checkedValues: ['616', '617'] },
        studyTypes: ['studyType618', 'studyType619'], variantTypes: ['variant620', 'variant621']
      }
    }
  }, synonymous: {
    all: {
      name: 'name655', count: 656, expected: 657, overlapped: 658, pvalue: 659,
      countFilter:
      {
        datasetId: 'name655', geneSymbols: ['gene656', 'gene657'],
        effectTypes: ['effectType658', 'effectType659'],
        gender: ['gender660', 'gender661'], peopleGroup: { id: 'id662', checkedValues: ['663', '664'] },
        studyTypes: ['studyType665', 'studyType666'], variantTypes: ['variant667', 'variant668']
      },
      overlapFilter:
      {
        datasetId: 'name669', geneSymbols: ['gene670', 'gene671'],
        effectTypes: ['effectType672', 'effectType673'],
        gender: ['gender674', 'gender675'],
        peopleGroup: { id: 'id676', checkedValues: ['677', '678'] },
        studyTypes: ['studyType679', 'studyType680'], variantTypes: ['variant681', 'variant682']
      },
    }, male: {
      name: 'name683', count: 684, expected: 685, overlapped: 686, pvalue: 687,
      countFilter:
      {
        datasetId: 'name688', geneSymbols: ['gene689', 'gene690'],
        effectTypes: ['effectType691', 'effectType692'],
        gender: ['gender693', 'gender694'], peopleGroup: { id: 'id695', checkedValues: ['696', '697'] },
        studyTypes: ['studyType698', 'studyType699'], variantTypes: ['variant700', 'variant701']
      },
      overlapFilter:
      {
        datasetId: 'name702', geneSymbols: ['gene703', 'gene704'],
        effectTypes: ['effectType705', 'effectType706'],
        gender: ['gender707', 'gender708'], peopleGroup: { id: 'id709', checkedValues: ['710', '711'] },
        studyTypes: ['studyType712', 'studyType713'], variantTypes: ['variant714', 'variant715']
      }
    }, female: {
      name: 'name716', count: 717, expected: 718, overlapped: 719, pvalue: 720,
      countFilter:
      {
        datasetId: 'name721', geneSymbols: ['gene722', 'gene723'],
        effectTypes: ['effectType724', 'effectType725'],
        gender: ['gender726', 'gender727'], peopleGroup: { id: 'id728', checkedValues: ['729', '730'] },
        studyTypes: ['studyType731', 'studyType732'], variantTypes: ['variant733', 'variant734']
      },
      overlapFilter:
      {
        datasetId: 'name735', geneSymbols: ['gene736', 'gene737'],
        effectTypes: ['effectType738', 'effectType739'],
        gender: ['gender740', 'gender741'], peopleGroup: { id: 'id742', checkedValues: ['743', '744'] },
        studyTypes: ['studyType745', 'studyType746'], variantTypes: ['variant747', 'variant748']
      }
    }
  }, childrenStats: {
    M: 782, // eslint-disable-line
    F: 783, // eslint-disable-line
    U: 784 // eslint-disable-line
  }
};

describe('EnrichmentResult', () => {
  it('should create from json', () => {
    expect(enrichmentResult1).toStrictEqual(EnrichmentResult.fromJson(enrichmentResultFromJson1));
  });

  it('should create from json array', () => {
    expect([enrichmentResult1, enrichmentResult2]).toStrictEqual(EnrichmentResult.fromJsonArray([
      enrichmentResultFromJson1, enrichmentResultFromJson2
    ]));
  });
});
