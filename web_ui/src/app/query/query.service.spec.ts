// QueryService imports `oboe` as a default export. Mock it at the top
// so subsequent `import oboe from 'oboe'` in the SUT resolves to the
// jest.fn() — makeOboeStub() (tb-z39.1) wires up the fluent chain on
// top of this. jest.mock is hoisted per-file by jest-preset-angular.
jest.mock('oboe', () => ({ __esModule: true, default: jest.fn() }));

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
import { makeOboeStub } from './_test-helpers/oboe-stub';

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
  true,
  true,
  true,

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
    const genomeMock = 'hg38';
    const genotypePreview = new GenotypePreview();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const dataMap = new Map<string, any>();

    dataMap.set('source1', resMock[0]);
    dataMap.set('source2', resMock[1]);
    dataMap.set('source3', resMock[2]);
    dataMap.set('genome', genomeMock);

    genotypePreview.data = dataMap;
    const genotypePreviewArray = new GenotypePreviewVariantsArray();
    genotypePreviewArray.genotypePreviews = [genotypePreview];

    const spy = jest.spyOn(service, 'streamPost').mockImplementation(() => of(resMock) as Subject<unknown>);
    const arrSpy = jest.spyOn(GenotypePreviewVariantsArray.prototype, 'addPreviewVariant');
    jest.spyOn(service['instanceService'], 'getGenome').mockReturnValue(of(genomeMock));

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
    const genomeMock = 'hg38';
    const genotypePreview = new GenotypePreview();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const dataMap = new Map<string, any>();
    dataMap.set('source1', resMock[0]);
    dataMap.set('genome', genomeMock);

    genotypePreview.data = dataMap;
    const genotypePreviewArray = new GenotypePreviewVariantsArray();
    genotypePreviewArray.genotypePreviews = [genotypePreview];

    const spy = jest.spyOn(service, 'streamPost').mockImplementation(() => of(resMock) as Subject<unknown>);
    const arrSpy = jest.spyOn(GenotypePreviewVariantsArray.prototype, 'addPreviewVariant');
    jest.spyOn(service['instanceService'], 'getGenome').mockReturnValue(of(genomeMock));

    const genotypePreviewResponse = service.getGenotypePreviewVariantsByFilter(datasetMock, filter);

    expect(spy).toHaveBeenCalledWith(service['genotypePreviewVariantsUrl'], filter);
    expect(arrSpy).toHaveBeenCalledWith(resMock, datasetMock.genotypeBrowserConfig.columnIds);
    expect(genotypePreviewResponse).toStrictEqual(genotypePreviewArray);
  });

  it('should cancel streaming', () => {
    service['oboeInstance'] = {
      url: 'url',
      abort: (): void => {}
    } as unknown as typeof service['oboeInstance'];

    const oboeInstanceSpy = jest.spyOn(service['oboeInstance'], 'abort');
    service.cancelStreamPost();

    expect(oboeInstanceSpy).toHaveBeenCalledWith();
    expect(service['oboeInstance']).toBeNull();
  });

  it('should cancel summary streaming', () => {
    service['summaryOboeInstance'] = {
      url: 'url',
      abort: (): void => {}
    } as unknown as typeof service['summaryOboeInstance'];

    const summaryOboeInstanceSpy = jest.spyOn(service['summaryOboeInstance'], 'abort');
    service.cancelSummaryStreamPost();

    expect(summaryOboeInstanceSpy).toHaveBeenCalledWith();
    expect(service['summaryOboeInstance']).toBeNull();
  });

  it('makeOboeStub captures callbacks for later invocation (smoke)', () => {
    const oboe = makeOboeStub();

    const subject = service.streamPost('test/url', { foo: 'bar' });
    expect(oboe.instance).toHaveBeenCalledTimes(1);

    const emitted: unknown[] = [];
    const sub = subject.subscribe(value => emitted.push(value));

    const cb = oboe.latest();
    expect(cb.node).toBeDefined();
    expect(cb.done).toBeDefined();
    expect(cb.fail).toBeDefined();

    cb.node?.({ row: 1 });
    cb.node?.({ row: 2 });
    cb.done?.();

    // streamPost emits each .node payload then a null sentinel on .done
    expect(emitted).toStrictEqual([{ row: 1 }, { row: 2 }, null]);
    sub.unsubscribe();
  });

  describe('streamPost lifecycle', () => {
    // Pulls the Nth argument of the Mth call out of a jest.Mock without
    // tripping @typescript-eslint/no-unsafe-member-access. The mock-call
    // tuple is typed as `unknown[]` in jest, but `mock.calls` itself is
    // `any[][]` — this helper localises that cast.
    const getCallArg = (mock: jest.Mock, callIdx: number, argIdx = 0): unknown => {
      const calls = mock.mock.calls as unknown[][];
      return calls[callIdx][argIdx];
    };

    let oboe: ReturnType<typeof makeOboeStub>;

    beforeEach(() => {
      oboe = makeOboeStub();
      // AuthService.accessToken is a getter returning `this.authToken || ''`.
      // Default to empty so we don't accidentally smuggle an Authorization
      // header into the non-token tests; specific tests below override the
      // backing field as needed.
      service['authService']['authToken'] = null;
    });

    it('happy path: emits start, per-node updates, and finishes with null sentinel', () => {
      const startSpy = jest.fn();
      const updateSpy = jest.fn();
      const dataSpy = jest.fn();
      const finishedSpy = jest.fn();

      service.streamingStartSubject.subscribe(startSpy);
      service.streamingUpdateSubject.subscribe(updateSpy);
      service.streamingSubject.subscribe(dataSpy);
      service.streamingFinishedSubject.subscribe(finishedSpy);

      const filter = { foo: 'bar' };
      service.streamPost('test/url', filter);

      expect(oboe.instance).toHaveBeenCalledTimes(1);
      const opts = getCallArg(oboe.instance, 0) as Record<string, unknown>;
      expect(opts).toStrictEqual(expect.objectContaining({
        url: `${'http://localhost:8000/api/v3/'}test/url`,
        method: 'POST',
        body: filter,
        withCredentials: true,
      }));

      expect(startSpy).toHaveBeenCalledTimes(1);
      expect(startSpy).toHaveBeenCalledWith(true);

      const cb = oboe.latest();
      cb.node?.({ a: 1 });
      cb.node?.({ a: 2 });
      cb.node?.({ a: 3 });

      expect(updateSpy).toHaveBeenCalledTimes(3);
      expect(updateSpy).toHaveBeenNthCalledWith(1, true);
      expect(updateSpy).toHaveBeenNthCalledWith(2, true);
      expect(updateSpy).toHaveBeenNthCalledWith(3, true);
      expect(dataSpy).toHaveBeenCalledTimes(3);
      expect(dataSpy).toHaveBeenNthCalledWith(1, { a: 1 });
      expect(dataSpy).toHaveBeenNthCalledWith(2, { a: 2 });
      expect(dataSpy).toHaveBeenNthCalledWith(3, { a: 3 });

      cb.done?.();

      expect(finishedSpy).toHaveBeenCalledTimes(1);
      expect(finishedSpy).toHaveBeenCalledWith(true);
      // After done(): the null sentinel should be the last value emitted
      // on streamingSubject (4th overall).
      expect(dataSpy).toHaveBeenCalledTimes(4);
      expect(dataSpy).toHaveBeenLastCalledWith(null);
      expect(service['oboeInstance']).toBeNull();
    });

    it('empty stream: emits finished THEN null sentinel (tb-iuv NULL-SENTINEL ordering)', () => {
      // Capture order across BOTH subjects by tagging events as they arrive.
      const events: Array<{ subject: string; value: unknown }> = [];
      service.streamingFinishedSubject.subscribe(value =>
        events.push({ subject: 'finished', value: value })
      );
      service.streamingSubject.subscribe(value =>
        events.push({ subject: 'data', value: value })
      );

      service.streamPost('test/url', { foo: 'bar' });
      const cb = oboe.latest();
      // No cb.node?.(...) — empty stream.
      cb.done?.();

      expect(events).toStrictEqual([
        { subject: 'finished', value: true },
        { subject: 'data', value: null },
      ]);
      expect(service['oboeInstance']).toBeNull();
    });

    it('failure path: logs to console.warn/error, emits finished + null sentinel, clears oboeInstance', () => {
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
      const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      const finishedSpy = jest.fn();
      const dataSpy = jest.fn();
      service.streamingFinishedSubject.subscribe(finishedSpy);
      service.streamingSubject.subscribe(dataSpy);

      service.streamPost('test/url', { foo: 'bar' });
      const cb = oboe.latest();
      const err = new Error('boom');
      cb.fail?.(err);

      expect(warnSpy).toHaveBeenCalledTimes(1);
      expect(errorSpy).toHaveBeenCalledTimes(1);
      expect(errorSpy).toHaveBeenCalledWith(err);
      expect(finishedSpy).toHaveBeenCalledTimes(1);
      expect(finishedSpy).toHaveBeenCalledWith(true);
      expect(dataSpy).toHaveBeenCalledTimes(1);
      expect(dataSpy).toHaveBeenCalledWith(null);
      expect(service['oboeInstance']).toBeNull();

      warnSpy.mockRestore();
      errorSpy.mockRestore();
    });

    it('cancellation mid-stream: aborts + clears oboeInstance; subsequent done() still emits (oboe unaware)', () => {
      const finishedSpy = jest.fn();
      const dataSpy = jest.fn();
      service.streamingFinishedSubject.subscribe(finishedSpy);
      service.streamingSubject.subscribe(dataSpy);

      service.streamPost('test/url', { foo: 'bar' });
      const cb = oboe.latest();

      service.cancelStreamPost();

      expect(cb.abort).toHaveBeenCalledTimes(1);
      expect(service['oboeInstance']).toBeNull();

      // Snapshot pre-done emission counts so we can detect any post-done
      // emissions deterministically.
      const finishedBefore = finishedSpy.mock.calls.length;
      const dataBefore = dataSpy.mock.calls.length;

      // The SUT's done() callback closure is still wired to the same
      // subjects, and oboe (at the JS layer) doesn't know it was aborted.
      // So if the test invokes cb.done?.() it WILL fire emissions on the
      // shared subjects. We assert what the SUT actually does:
      //   - streamingFinishedSubject fires `true`
      //   - streamingSubject fires `null`
      //   - oboeInstance stays null (it was already null after cancel; the
      //     done() handler unconditionally re-assigns it to null)
      cb.done?.();

      expect(finishedSpy.mock.calls).toHaveLength(finishedBefore + 1);
      expect(finishedSpy).toHaveBeenLastCalledWith(true);
      expect(dataSpy.mock.calls).toHaveLength(dataBefore + 1);
      expect(dataSpy).toHaveBeenLastCalledWith(null);
      expect(service['oboeInstance']).toBeNull();
    });

    it('double-submit: second streamPost aborts the first; oboe.latest() points to the second call', () => {
      service.streamPost('first/url', { call: 1 });
      const firstCb = oboe.latest();

      service.streamPost('second/url', { call: 2 });
      const secondCb = oboe.latest();

      expect(oboe.instance).toHaveBeenCalledTimes(2);
      expect(firstCb.abort).toHaveBeenCalledTimes(1);
      // Latest is genuinely the SECOND call (different captured object).
      expect(secondCb).not.toBe(firstCb);
      // And the second oboe(opts) carried the second filter.
      const secondOpts = getCallArg(oboe.instance, 1) as Record<string, unknown>;
      expect(secondOpts.body).toStrictEqual({ call: 2 });
      expect(secondOpts.url).toBe(`${'http://localhost:8000/api/v3/'}second/url`);
    });

    it('auth header — token present: opts.headers.Authorization === "Bearer <token>"', () => {
      // accessToken getter reads `this.authToken || ''`.
      service['authService']['authToken'] = 'tok-abc';

      service.streamPost('test/url', { foo: 'bar' });

      const opts = getCallArg(oboe.instance, 0) as { headers: Record<string, string> };
      expect(opts.headers.Authorization).toBe('Bearer tok-abc');
      expect(opts.headers['Content-Type']).toBe('application/json');
    });

    it('auth header — token empty: opts.headers has no Authorization key', () => {
      // Default beforeEach sets authToken = null → accessToken returns ''.
      service.streamPost('test/url', { foo: 'bar' });

      const opts = getCallArg(oboe.instance, 0) as { headers: Record<string, string> };
      // No Authorization header should be present at all.
      expect('Authorization' in opts.headers).toBe(false);
      expect(opts.headers.Authorization).toBeUndefined();
      expect(opts.headers['Content-Type']).toBe('application/json');
    });

    it('isStreamingActive reflects state across start/done/cancel', () => {
      expect(service.isStreamingActive()).toBe(false);

      service.streamPost('test/url', { foo: 'bar' });
      expect(service.isStreamingActive()).toBe(true);

      const cb = oboe.latest();
      cb.done?.();
      expect(service.isStreamingActive()).toBe(false);

      // Reset and verify cancel also returns to inactive.
      service.streamPost('test/url', { foo: 'bar' });
      expect(service.isStreamingActive()).toBe(true);
      service.cancelStreamPost();
      expect(service.isStreamingActive()).toBe(false);
    });
  });

  describe('summaryStreamPost lifecycle', () => {
    // Mirrors the helper from streamPost lifecycle: pulls the Nth argument
    // of the Mth call out of a jest.Mock without tripping
    // @typescript-eslint/no-unsafe-member-access. mock.calls is `any[][]`
    // — this localises that cast.
    const getCallArg = (mock: jest.Mock, callIdx: number, argIdx = 0): unknown => {
      const calls = mock.mock.calls as unknown[][];
      return calls[callIdx][argIdx];
    };

    let oboe: ReturnType<typeof makeOboeStub>;

    beforeEach(() => {
      oboe = makeOboeStub();
      // AuthService.accessToken is a getter returning `this.authToken || ''`.
      // Default to empty so we don't accidentally smuggle an Authorization
      // header into the non-token tests; specific tests below override the
      // backing field as needed.
      service['authService']['authToken'] = null;
    });

    it('happy path: per-node updates + null sentinel; no streamingStartSubject emit', () => {
      // streamingStartSubject must NOT fire — this is the key behavioural
      // diff from streamPost. Easy to silently regress, so spy on it.
      const startSpy = jest.fn();
      const dataSpy = jest.fn();
      const finishedSpy = jest.fn();

      service.streamingStartSubject.subscribe(startSpy);
      service.summaryStreamingSubject.subscribe(dataSpy);
      service.summaryStreamingFinishedSubject.subscribe(finishedSpy);

      const filter = { foo: 'bar' };
      service.summaryStreamPost('test/url', filter);

      expect(oboe.instance).toHaveBeenCalledTimes(1);
      const opts = getCallArg(oboe.instance, 0) as Record<string, unknown>;
      expect(opts).toStrictEqual(expect.objectContaining({
        url: `${'http://localhost:8000/api/v3/'}test/url`,
        method: 'POST',
        body: filter,
        withCredentials: true,
      }));
      expect((opts.headers as Record<string, string>)['Content-Type'])
        .toBe('application/json');

      const cb = oboe.latest();
      cb.node?.({ x: 1 });
      cb.node?.({ x: 2 });

      expect(dataSpy).toHaveBeenCalledTimes(2);
      expect(dataSpy).toHaveBeenNthCalledWith(1, { x: 1 });
      expect(dataSpy).toHaveBeenNthCalledWith(2, { x: 2 });

      cb.done?.();

      expect(finishedSpy).toHaveBeenCalledTimes(1);
      expect(finishedSpy).toHaveBeenCalledWith(true);
      // After done(): the null sentinel is the last value emitted on
      // summaryStreamingSubject (3rd overall, after the 2 nodes).
      expect(dataSpy).toHaveBeenCalledTimes(3);
      expect(dataSpy).toHaveBeenLastCalledWith(null);
      // Surprise: summaryStreamPost.done() does NOT clear
      // summaryOboeInstance (unlike streamPost.done(), which assigns
      // oboeInstance = null). We pin the actual SUT behaviour: after
      // done() the instance handle remains set. Compare with
      // cancelSummaryStreamPost(), which DOES clear it.
      expect(service['summaryOboeInstance']).not.toBeNull();

      // streamingStartSubject MUST NOT have fired — summaryStreamPost has
      // no `streamingStartSubject.next(true)` (unlike streamPost).
      expect(startSpy).not.toHaveBeenCalled();
    });

    it('empty stream: emits finished THEN null sentinel (order matters)', () => {
      // Capture order across BOTH subjects by tagging events as they arrive.
      const events: Array<{ subject: string; value: unknown }> = [];
      service.summaryStreamingFinishedSubject.subscribe(value =>
        events.push({ subject: 'finished', value: value })
      );
      service.summaryStreamingSubject.subscribe(value =>
        events.push({ subject: 'data', value: value })
      );

      service.summaryStreamPost('test/url', { foo: 'bar' });
      const cb = oboe.latest();
      // No cb.node?.(...) — empty stream.
      cb.done?.();

      expect(events).toStrictEqual([
        { subject: 'finished', value: true },
        { subject: 'data', value: null },
      ]);
      // Surprise: done() does NOT clear summaryOboeInstance (see happy
      // path test). Pin actual SUT behaviour.
      expect(service['summaryOboeInstance']).not.toBeNull();
    });

    it('failure path: logs warn/error, emits finished + null; leaves summaryOboeInstance set', () => {
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
      const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      const finishedSpy = jest.fn();
      const dataSpy = jest.fn();
      service.summaryStreamingFinishedSubject.subscribe(finishedSpy);
      service.summaryStreamingSubject.subscribe(dataSpy);

      service.summaryStreamPost('test/url', { foo: 'bar' });
      const cb = oboe.latest();
      const err = new Error('boom');
      cb.fail?.(err);

      expect(warnSpy).toHaveBeenCalledTimes(1);
      expect(errorSpy).toHaveBeenCalledTimes(1);
      expect(errorSpy).toHaveBeenCalledWith(err);
      expect(finishedSpy).toHaveBeenCalledTimes(1);
      expect(finishedSpy).toHaveBeenCalledWith(true);
      expect(dataSpy).toHaveBeenCalledTimes(1);
      expect(dataSpy).toHaveBeenCalledWith(null);
      // Surprise: fail() does NOT clear summaryOboeInstance (see happy
      // path test). Pin actual SUT behaviour.
      expect(service['summaryOboeInstance']).not.toBeNull();

      warnSpy.mockRestore();
      errorSpy.mockRestore();
    });

    it('cancel mid-stream: aborts + clears instance; later done() still emits (oboe unaware)', () => {
      const finishedSpy = jest.fn();
      const dataSpy = jest.fn();
      service.summaryStreamingFinishedSubject.subscribe(finishedSpy);
      service.summaryStreamingSubject.subscribe(dataSpy);

      service.summaryStreamPost('test/url', { foo: 'bar' });
      const cb = oboe.latest();

      service.cancelSummaryStreamPost();

      expect(cb.abort).toHaveBeenCalledTimes(1);
      expect(service['summaryOboeInstance']).toBeNull();

      // Snapshot pre-done emission counts so we can detect any post-done
      // emissions deterministically.
      const finishedBefore = finishedSpy.mock.calls.length;
      const dataBefore = dataSpy.mock.calls.length;

      // The SUT's done() callback closure is still wired to the same
      // subjects, and oboe (at the JS layer) doesn't know it was aborted.
      // Mirroring streamPost: the SUT has no abort-aware guard, so a
      // subsequent cb.done?.() WILL re-emit through the subjects.
      cb.done?.();

      expect(finishedSpy.mock.calls).toHaveLength(finishedBefore + 1);
      expect(finishedSpy).toHaveBeenLastCalledWith(true);
      expect(dataSpy.mock.calls).toHaveLength(dataBefore + 1);
      expect(dataSpy).toHaveBeenLastCalledWith(null);
      // Note: summaryStreamPost's done() does NOT clear summaryOboeInstance
      // (unlike streamPost.done(), which clears oboeInstance). After cancel
      // it was already null, and done() leaves it null because there's no
      // assignment in summaryStreamPost.done().
      expect(service['summaryOboeInstance']).toBeNull();
    });

    it('double-submit: second summaryStreamPost aborts the first; oboe.latest() points to the second call', () => {
      service.summaryStreamPost('first/url', { call: 1 });
      const firstCb = oboe.latest();

      service.summaryStreamPost('second/url', { call: 2 });
      const secondCb = oboe.latest();

      expect(oboe.instance).toHaveBeenCalledTimes(2);
      expect(firstCb.abort).toHaveBeenCalledTimes(1);
      // Latest is genuinely the SECOND call (different captured object).
      expect(secondCb).not.toBe(firstCb);
      // And the second oboe(opts) carried the second filter.
      const secondOpts = getCallArg(oboe.instance, 1) as Record<string, unknown>;
      expect(secondOpts.body).toStrictEqual({ call: 2 });
      expect(secondOpts.url).toBe(`${'http://localhost:8000/api/v3/'}second/url`);
    });

    it('auth header — token present: opts.headers.Authorization === "Bearer <token>"', () => {
      // accessToken getter reads `this.authToken || ''`.
      service['authService']['authToken'] = 'tok-summary';

      service.summaryStreamPost('test/url', { foo: 'bar' });

      const opts = getCallArg(oboe.instance, 0) as { headers: Record<string, string> };
      expect(opts.headers.Authorization).toBe('Bearer tok-summary');
      expect(opts.headers['Content-Type']).toBe('application/json');
    });

    it('auth header — token empty: opts.headers has no Authorization key', () => {
      // Default beforeEach sets authToken = null → accessToken returns ''.
      service.summaryStreamPost('test/url', { foo: 'bar' });

      const opts = getCallArg(oboe.instance, 0) as { headers: Record<string, string> };
      // No Authorization header should be present at all.
      expect('Authorization' in opts.headers).toBe(false);
      expect(opts.headers.Authorization).toBeUndefined();
      expect(opts.headers['Content-Type']).toBe('application/json');
    });
  });
});
