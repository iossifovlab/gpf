import { TestBed } from '@angular/core/testing';
import { PhenoBrowserService } from './pheno-browser.service';
import { PhenoInstrument, PhenoInstruments, PhenoMeasure, PhenoMeasures } from './pheno-browser';
import { ConfigService } from '../config/config.service';
import { CookieService } from 'ngx-cookie-service';
import * as lodash from 'lodash';
import { lastValueFrom, of, take, throwError } from 'rxjs';
import { fakeJsonMeasure } from './pheno-browser.spec';
import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';
import { APP_BASE_HREF } from '@angular/common';
import { AuthService } from 'app/auth.service';

class AuthServiceMock {
  public accessToken = 'accessTokenMock';
}
describe('pheno browser service', () => {
  let phenoBrowserService: PhenoBrowserService;
  const authServiceMock = new AuthServiceMock();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  let httpSpy; // used in beforeEach

  beforeEach(() => {
    const cookieSpyObj = {
      get: jest.fn()
    };
    const configMock = { baseUrl: 'http://testUrl/' };
    const httpSpyObj = {
      get: jest.fn(),
      head: jest.fn()
    };

    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      providers: [
        PhenoBrowserService,
        { provide: CookieService, useValue: cookieSpyObj },
        { provide: AuthService, useValue: authServiceMock },
        { provide: ConfigService, useValue: configMock },
        { provide: HttpClient, useValue: httpSpyObj },
        { provide: APP_BASE_HREF, useValue: '' },
      ]
    });

    phenoBrowserService = TestBed.inject(PhenoBrowserService);
    httpSpy = TestBed.inject(HttpClient);
  });

  it('should fetch instruments', async() => {
    // 'as unknown' is used to bypass warnings, since string[] does not overlap with PhenoInstruments
    const expectedInstruments: PhenoInstruments = ['i1', 'i2', 'i3'] as unknown as PhenoInstruments;
    const response = ['i1', 'i2', 'i3'];

    jest.spyOn(phenoBrowserService['cookieService'], 'get').mockReturnValue('tokenMock');
    const httpGetSpy = jest.spyOn(phenoBrowserService['http'], 'get');
    httpGetSpy.mockReturnValue(of(response));

    const searchParams = new HttpParams().set('dataset_id', 'datasetId');

    const getResult = phenoBrowserService.getInstruments('datasetId');

    expect(httpGetSpy).toHaveBeenCalledWith(
      phenoBrowserService['config'].baseUrl + phenoBrowserService['instrumentsUrl'],
      {
        headers: { 'X-CSRFToken': 'tokenMock', 'Content-Type': 'application/json' },
        withCredentials: true,
        params: searchParams
      }
    );

    const res = await lastValueFrom(getResult.pipe(take(1)));
    expect(res).toStrictEqual(expectedInstruments);
  });

  it('should fetch measures by instrument', async() => {
    const fakeJsonMeasureCopy = lodash.cloneDeep(fakeJsonMeasure);

    const expectedMeasure: PhenoMeasure = PhenoMeasure.fromJson(fakeJsonMeasureCopy);

    const getMeasuresSpy = jest.spyOn(phenoBrowserService['http'], 'get');
    getMeasuresSpy.mockReturnValue(of([{measure: fakeJsonMeasureCopy}]));
    const instrument = 'i1' as PhenoInstrument;

    const resObservable = phenoBrowserService.getMeasures('datasetId', instrument, '');

    const url =
      phenoBrowserService['config'].baseUrl +
      phenoBrowserService['measuresUrl'] +
      '?instrument=i1&dataset_id=datasetId';

    const options = {
      headers: {
        'Authorization': 'Bearer accessTokenMock',
        'Content-Type': 'application/json',
        'X-CSRFToken': undefined
      },
      withCredentials: true
    };

    expect(getMeasuresSpy).toHaveBeenCalledWith(url, options);

    const res = await lastValueFrom(resObservable);
    expect(res).toBeInstanceOf(Array<PhenoMeasure>);
    expect(res).toStrictEqual([expectedMeasure]);
  });

  it('should fetch measures by search and return undefined response', async() => {
    const getMeasuresSpy = jest.spyOn(phenoBrowserService['http'], 'get');
    getMeasuresSpy.mockReturnValue(of(undefined));

    const resObservable = phenoBrowserService.getMeasures('datasetId', null, 'searchValue');

    const url =
      phenoBrowserService['config'].baseUrl +
      phenoBrowserService['measuresUrl'] +
      '?instrument=null&dataset_id=datasetId&search=searchValue';

    const options = {
      headers: {
        'Authorization': 'Bearer accessTokenMock',
        'Content-Type': 'application/json',
        'X-CSRFToken': undefined
      },
      withCredentials: true
    };
    expect(getMeasuresSpy).toHaveBeenCalledWith(url, options);

    const res = await lastValueFrom(resObservable);
    expect(res).toBeInstanceOf(Array<PhenoMeasure>);
    expect(res).toStrictEqual([]);
  });

  it('should provide a correct download link', () => {
    const instrumentName = 'testInstrument';
    const datasetName = 'testDataset';
    const expectedUrl = 'http://testUrl/pheno_browser/download'
                        + `?dataset_id=${datasetName}&instrument=${instrumentName}`;
    expect(phenoBrowserService.getDownloadLink(instrumentName, datasetName)).toBe(expectedUrl);
  });

  it('should get description of a measure', async() => {
    const getMeasuresSpy = jest.spyOn(phenoBrowserService['http'], 'get');
    getMeasuresSpy.mockReturnValue(of({desc: 'measureDesc'}));

    const resObservable = phenoBrowserService.getMeasureDescription('datasetId', 'measureId');

    const params = new HttpParams().set('dataset_id', 'datasetId').set('measure_id', 'measureId');

    const url =
      phenoBrowserService['config'].baseUrl +
      phenoBrowserService['measureDescription'];

    const options = {
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': undefined
      },
      withCredentials: true,
      params: params
    };

    expect(getMeasuresSpy).toHaveBeenCalledWith(url, options);

    const res = await lastValueFrom(resObservable);
    expect(res).toStrictEqual({desc: 'measureDesc'});
  });


  it('should cancel streaming', () => {
    phenoBrowserService['oboeInstance'] = {
      url: 'url',
      abort: (): void => {}
    };

    const oboeInstanceSpy = jest.spyOn(phenoBrowserService['oboeInstance'], 'abort');
    phenoBrowserService.cancelStreamPost();

    expect(oboeInstanceSpy).toHaveBeenCalledWith();
    expect(phenoBrowserService['oboeInstance']).toBeNull();
  });

  it('should provide a correct measures download link', () => {
    const downloadData = {
      dataset_id: 'testDatasetId',
      instrument: 'testInstrument',
      search_term: 'searchValue'
    };

    const expectedUrl =
      'http://testUrl/pheno_browser/download' +
      '?dataset_id=testDatasetId' +
      '&instrument=testInstrument' +
      '&search_term=searchValue';
    expect(phenoBrowserService.getDownloadMeasuresLink(downloadData)).toBe(expectedUrl);
  });

  it('should validate measure download', async() => {
    const downloadData = {
      dataset_id: 'testDatasetId',
      instrument: 'testInstrument',
      search_term: 'searchValue'
    };

    const params = new HttpParams()
      .set('dataset_id', downloadData.dataset_id)
      .set('instrument', downloadData.instrument)
      .set('search_term', downloadData.search_term);

    const url = phenoBrowserService['config'].baseUrl + 'pheno_browser/download';

    const options = {
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': undefined
      },
      withCredentials: true,
      params: params,
      observe: 'response'
    };

    const httpResponse = new HttpResponse<object>();
    const headSpy = jest.spyOn(phenoBrowserService['http'], 'head');
    headSpy.mockReturnValue(of(httpResponse));

    const resObservable = phenoBrowserService.validateMeasureDownload(downloadData);

    expect(headSpy).toHaveBeenCalledWith(url, options);

    const res = await lastValueFrom(resObservable);
    expect(res).toStrictEqual(httpResponse);
  });

  it('should catch error when validating measure download', async() => {
    const downloadData = {
      dataset_id: 'testDatasetId',
      instrument: 'testInstrument',
      search_term: 'searchValue'
    };

    const httpError = new HttpResponse<object>({statusText: 'status fail'});
    const headSpy = jest.spyOn(phenoBrowserService['http'], 'head');
    headSpy.mockReturnValue(throwError(() => httpError));

    const resObservable = phenoBrowserService.validateMeasureDownload(downloadData);
    const res = await lastValueFrom(resObservable.pipe(take(1)));
    expect(res).toStrictEqual(httpError);
  });

  it('should get measures info', async() => {
    const measures = {
      base_image_url: 'imgUrl',
      measures: [],
      has_descriptions: true,
      regression_names: {}
    };

    const url = phenoBrowserService['config'].baseUrl + phenoBrowserService['measuresInfoUrl'];
    const searchParams = new HttpParams().set('dataset_id', 'datasetId');
    const options = {
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': undefined
      },
      withCredentials: true,
      params: searchParams
    };

    const getSpy = jest.spyOn(phenoBrowserService['http'], 'get');
    getSpy.mockReturnValue(of(measures));

    const resObservable = phenoBrowserService.getMeasuresInfo('datasetId');

    expect(getSpy).toHaveBeenCalledWith(url, options);

    const res = await lastValueFrom(resObservable.pipe(take(1)));
    expect(res).toStrictEqual(new PhenoMeasures('imgUrl', [], true, {}));
  });
});
