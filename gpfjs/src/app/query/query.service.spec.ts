import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { QueryService } from './query.service';
import { RouterModule } from '@angular/router';
import { APP_BASE_HREF } from '@angular/common';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { lastValueFrom, of, Subject, take } from 'rxjs';
import {
  Column,
  Dataset,
  GeneBrowser,
  GenotypeBrowser,
  PersonFilter} from 'app/datasets/datasets';
import { GenotypePreview, GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';

const queryMock = {
  data: {
    selectedDataset: {
      id: 'ALL_genotypes',
      name: 'ALL Genotypes',
      description: null,
    },
  },
  errorsState: 'errors',
  page: 'genotype'
};

const queryMockWithoutErrors = {
  data: {
    selectedDataset: {
      id: 'ALL_genotypes',
      name: 'ALL Genotypes',
      description: null,
    },
  },
  page: 'genotype'
};

const saveQueryMock = { uuid: 'e219957d-cf7f-4fe8-beed-1797f5f0d5cd' };

const userQueriesMock = {
  queries: [
    {
      query_uuid: 'bef687fb-1023-4141-84dc-e6bc2b0045ec',
      name: 'asd',
      description: '',
      page: 'phenotool'
    },
    {
      query_uuid: '4a44c6ef-f6f1-42f5-8d7f-b0c977060a65',
      name: 'zxc',
      description: '',
      page: 'genotype'
    }
  ]
};

const summaryVariantsMock = [
  {
    svuid: 'chr14:21431546.A.G.1',
    alleles: [
      {
        location: 'chr14:21431546',
        position: 21431546,
        end_position: null,
        chrom: 'chr14',
        frequency: 0.0006984120118431747,
        effect: 'missense',
        variant: 'sub(A->G)',
        family_variants_count: 1,
        is_denovo: false,
        seen_in_affected: true,
        seen_in_unaffected: true
      }
    ]
  },
  {
    svuid: 'chr14:21427997.G.A.1',
    alleles: [
      {
        location: 'chr14:21427997',
        position: 21427997,
        end_position: null,
        chrom: 'chr14',
        frequency: 0.008374740369617939,
        effect: 'synonymous',
        variant: 'sub(G->A)',
        family_variants_count: 2,
        is_denovo: false,
        seen_in_affected: true,
        seen_in_unaffected: true
      }
    ]
  }
];

const datasetMock = new Dataset(
  'id1',
  'name1',
  ['parent1', 'parent2'],
  false,
  ['study1', 'study2'],
  ['studyName1', 'studyName2'],
  ['studyType1', 'studyType2'],
  'phenotypeData1',
  false,
  true,
  true,
  false,
  {enabled: true},
  new GenotypeBrowser(
    false,
    true,
    false,
    false,
    true,
    false,
    true,
    false,
    false,
    [
      new Column('name1', 'source1', 'format1'),
      new Column('name2', 'source2', 'format2'),
      new Column('name2', 'source3', 'format3'),
    ],
    [
      new PersonFilter('personFilter1', 'string1', 'source1', 'sourceType1', 'filterType1', 'role1'),
      new PersonFilter('personFilter2', 'string2', 'source2', 'sourceType2', 'filterType2', 'role2')
    ],
    [
      new PersonFilter('familyFilter3', 'string3', 'source3', 'sourceType3', 'filterType3', 'role3'),
      new PersonFilter('familyFilter4', 'string4', 'source4', 'sourceType4', 'filterType4', 'role4')
    ],
    ['inheritance', 'string1'],
    ['selectedInheritance', 'string2'],
    ['variant', 'string3'],
    ['selectedVariant', 'string1'],
    5,
    false,
    false
  ),
  null,
  [],
  new GeneBrowser(true, 'frequencyCol1', 'frequencyName1', 'effectCol1', 'locationCol1', 5, 6, true),
  false,
  'genome1',
  true
);
describe('QueryService', () => {
  let service: QueryService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ConfigService,
        QueryService,
        { provide: APP_BASE_HREF, useValue: '' },
        provideHttpClient(),
        provideHttpClientTesting()
      ],
      imports: [
        RouterModule.forRoot([])
      ]
    });
    service = TestBed.inject(QueryService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should load query', async() => {
    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(queryMock));

    const loadQueryResult = service.loadQuery('8c50e203');
    expect(httpPostSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['loadQueryEndpoint'],
      { uuid: '8c50e203' },
      { headers: service['headers'], withCredentials: true }
    );
    const res = await lastValueFrom(loadQueryResult.pipe(take(1)));
    expect(res).toBe(queryMock);
  });

  it('should save query', async() => {
    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(saveQueryMock));

    const saveQueryResult = service.saveQuery(queryMock, '200', 'user');
    expect(httpPostSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['saveQueryEndpoint'],
      {
        data: queryMockWithoutErrors,
        page: '200',
        origin: 'user'
      },
      { headers: service['headers'] }
    );
    const res = await lastValueFrom(saveQueryResult.pipe(take(1)));
    expect(res).toBe(saveQueryMock);
  });

  it('should delete query', async() => {
    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(queryMock));

    const deleteQueryResult = service.deleteQuery('8c50e203');
    expect(httpPostSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['deleteQueryEndpoint'],
      { uuid: '8c50e203' },
      { headers: service['headers'], withCredentials: true }
    );
    const res = await lastValueFrom(deleteQueryResult.pipe(take(1)));
    expect(res).toBe(queryMock);
  });

  it('should create load query url', () => {
    const uuid = '8c50e203';
    const getUrl = service.getLoadUrl(uuid);
    expect(getUrl).toBe(window.location.origin + '/load-query/' + uuid);
  });

  it('should get load query url from query response', () => {
    const getUrl = service.getLoadUrlFromResponse(saveQueryMock);
    expect(getUrl).toBe(window.location.origin + '/load-query/e219957d-cf7f-4fe8-beed-1797f5f0d5cd');
  });

  it('should save query saved by user', async() => {
    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(saveQueryMock));

    const uuid = '8c50e203';
    const query_name = 'query_name';
    const query_description = 'query_description';

    const queryResponse = service.saveUserQuery(uuid, query_name, query_description);

    expect(httpPostSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['userSaveQueryEndpoint'],
      { query_uuid: uuid, name: query_name, description: query_description },
      { headers: service['headers'], withCredentials: true }
    );
    const res = await lastValueFrom(queryResponse.pipe(take(1)));
    expect(res).toBe(saveQueryMock);
  });

  it('should get user\'s saved queries', async() => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(userQueriesMock));

    const queryResponse = service.collectUserSavedQueries();

    expect(httpGetSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['userCollectQueriesEndpoint'],
      { withCredentials: true }
    );
    const res = await lastValueFrom(queryResponse.pipe(take(1)));
    expect(res).toBe(userQueriesMock);
  });

  it('should get summary variants when loading gene in gene browser', async() => {
    const filter = {
      datasetId: 'ALL_genotypes',
      geneSymbols: [
        'CHD3'
      ],
      maxVariantsCount: 100000,
      inheritanceTypeFilter: [
        'denovo',
        'mendelian'
      ],
      effectTypes: [
        'frame-shift',
        'nonsense',
      ]
    };
    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(summaryVariantsMock));

    const summaryVarinatsResponse = service.getSummaryVariants(filter);

    expect(httpPostSpy).toHaveBeenCalledWith(
      service['config'].baseUrl + service['geneViewVariantsUrl'],
      filter
    );
    const res = await lastValueFrom(summaryVarinatsResponse.pipe(take(1)));
    expect(res).toBe(summaryVariantsMock);
  });

  it('should get genotype preview variants', () => {
    const filter = {
      datasetId: 'ALL_genotypes',
      geneSymbols: [
        'CHD3'
      ],
      maxVariantsCount: 12,
      inheritanceTypeFilter: [
        'denovo',
        'mendelian'
      ],
      effectTypes: [
        'frame-shift',
        'nonsense',
      ]
    };

    const resMock = [
      ['14016'],
      ['SSC CSHL WGS'],
      ['chr14:21402010'],
    ];

    const genotypePreview = new GenotypePreview();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const dataMap = new Map<string, any>();
    dataMap.set('source1', resMock[0]);
    dataMap.set('source2', resMock[1]);
    dataMap.set('source3', resMock[2]);

    dataMap.set('genome', datasetMock.genome);
    genotypePreview.data = dataMap;
    const genotypePreviewArray = new GenotypePreviewVariantsArray();
    genotypePreviewArray.genotypePreviews = [genotypePreview];

    const spy = jest.spyOn(service, 'streamPost').mockImplementation(() => of(resMock) as Subject<unknown>);
    const arrSpy = jest.spyOn(GenotypePreviewVariantsArray.prototype, 'addPreviewVariant');
    const genotypePreviewResponse = service.getGenotypePreviewVariantsByFilter(datasetMock, filter, 12, () => {});

    expect(spy).toHaveBeenCalledWith(service['genotypePreviewVariantsUrl'], filter);
    expect(arrSpy).toHaveBeenCalledWith(resMock, datasetMock.genotypeBrowserConfig.columnIds);
    expect(genotypePreviewResponse).toStrictEqual(genotypePreviewArray);
  });

  it('should get genotype preview variants without passing max count and callback', () => {
    const filter = {
      datasetId: 'ALL_genotypes',
      geneSymbols: [
        'CHD3'
      ],
      maxVariantsCount: 1001,
      inheritanceTypeFilter: [
        'denovo',
        'mendelian'
      ],
      effectTypes: [
        'frame-shift',
        'nonsense',
      ]
    };

    const resMock = [['14016']];

    const genotypePreview = new GenotypePreview();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const dataMap = new Map<string, any>();
    dataMap.set('source1', resMock[0]);

    dataMap.set('genome', datasetMock.genome);
    genotypePreview.data = dataMap;
    const genotypePreviewArray = new GenotypePreviewVariantsArray();
    genotypePreviewArray.genotypePreviews = [genotypePreview];

    const spy = jest.spyOn(service, 'streamPost').mockImplementation(() => of(resMock) as Subject<unknown>);
    const arrSpy = jest.spyOn(GenotypePreviewVariantsArray.prototype, 'addPreviewVariant');
    const genotypePreviewResponse = service.getGenotypePreviewVariantsByFilter(datasetMock, filter);

    expect(spy).toHaveBeenCalledWith(service['genotypePreviewVariantsUrl'], filter);
    expect(arrSpy).toHaveBeenCalledWith(resMock, datasetMock.genotypeBrowserConfig.columnIds);
    expect(genotypePreviewResponse).toStrictEqual(genotypePreviewArray);
  });

  it('should cancel streaming', () => {
    service['oboeInstance'] = {
      url: 'url',
      abort: (): void => {}
    };

    const oboeInstanceSpy = jest.spyOn(service['oboeInstance'], 'abort');
    service.cancelStreamPost();

    expect(oboeInstanceSpy).toHaveBeenCalledWith();
    expect(service['oboeInstance']).toBeNull();
  });

  it('should cancel summary streaming', () => {
    service['summaryOboeInstance'] = {
      url: 'url',
      abort: (): void => {}
    };

    const summaryOboeInstanceSpy = jest.spyOn(service['summaryOboeInstance'], 'abort');
    service.cancelSummaryStreamPost();

    expect(summaryOboeInstanceSpy).toHaveBeenCalledWith();
    expect(service['summaryOboeInstance']).toBeNull();
  });
});
