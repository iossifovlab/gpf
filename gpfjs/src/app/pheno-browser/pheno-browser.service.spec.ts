import { TestBed } from '@angular/core/testing';
import { PhenoBrowserService } from './pheno-browser.service';
import { PhenoInstruments, PhenoMeasure } from './pheno-browser';
import { ConfigService } from '../config/config.service';
import { CookieService } from 'ngx-cookie-service';
import * as lodash from 'lodash';
import { lastValueFrom, of } from 'rxjs';
import { fakeJsonMeasure } from './pheno-browser.spec';
import { HttpClient } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';
import { APP_BASE_HREF } from '@angular/common';

describe('pheno browser service', () => {
  let phenoBrowserService: PhenoBrowserService;
  let httpSpy;

  beforeEach(() => {
    const cookieSpyObj = {
      get: jest.fn()
    };
    const configMock = { baseUrl: 'http://testUrl/' };
    const httpSpyObj = {
      get: jest.fn()
    };

    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      providers: [
        PhenoBrowserService,
        { provide: CookieService, useValue: cookieSpyObj },
        { provide: ConfigService, useValue: configMock },
        { provide: HttpClient, useValue: httpSpyObj },
        { provide: APP_BASE_HREF, useValue: '' },
      ]
    });

    phenoBrowserService = TestBed.inject(PhenoBrowserService);
    httpSpy = TestBed.inject(HttpClient);
  });

  it('should fetch instruments', (done) => {
    // 'as unknown' is used to bypass warnings, since string[] does not overlap with PhenoInstruments
    const expectedInstruments: PhenoInstruments = ['i1', 'i2', 'i3'] as unknown as PhenoInstruments;
    const response = ['i1', 'i2', 'i3'];

    httpSpy.get.mockReturnValue(of(response));
    phenoBrowserService.getInstruments(null).subscribe(instruments => {
      expect(instruments).toStrictEqual(expectedInstruments);
      done();
    });
  });

  it('should fetch measures by parameters', async() => {
    const fakeJsonMeasureCopy = lodash.cloneDeep(fakeJsonMeasure);

    const expectedMeasure: PhenoMeasure = PhenoMeasure.fromJson(fakeJsonMeasureCopy);

    const getMeasuresSpy = jest.spyOn(phenoBrowserService['http'], 'get');
    getMeasuresSpy.mockReturnValue(of([{measure: fakeJsonMeasureCopy}]));

    const resObservable = phenoBrowserService.getMeasures('datasetId', null, '');

    const url = phenoBrowserService['config'].baseUrl +
      phenoBrowserService['measuresUrl'] + '?instrument=null&dataset_id=datasetId';
    const options =
      // eslint-disable-next-line @typescript-eslint/naming-convention
      {headers: {'Content-Type': 'application/json', 'X-CSRFToken': undefined}, withCredentials: true};
    expect(getMeasuresSpy).toHaveBeenCalledWith(url, options);

    const res = await lastValueFrom(resObservable);
    expect(res).toBeInstanceOf(Array<PhenoMeasure>);
    expect(res).toStrictEqual([expectedMeasure]);
  });

  it('should provide a correct download link', () => {
    const instrumentName = 'testInstrument';
    const datasetName = 'testDataset';
    const expectedUrl = 'http://testUrl/pheno_browser/download'
                        + `?dataset_id=${datasetName}&instrument=${instrumentName}`;
    expect(phenoBrowserService.getDownloadLink(instrumentName, datasetName)).toBe(expectedUrl);
  });
});
