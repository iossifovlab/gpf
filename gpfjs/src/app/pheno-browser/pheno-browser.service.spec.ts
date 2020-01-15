import { TestBed } from '@angular/core/testing';
import { PhenoBrowserService } from './pheno-browser.service';
import { PhenoInstruments, PhenoMeasures } from './pheno-browser';
import { ConfigService } from '../config/config.service';
import { CookieService } from 'ngx-cookie';
// tslint:disable-next-line:import-blacklist
import { Observable, of } from 'rxjs';
import { fakeJsonMeasure } from './pheno-browser.spec';
import 'rxjs/add/operator/map';
import { HttpClient } from '@angular/common/http';

describe('pheno browser service', () => {
  let phenoBrowserService: PhenoBrowserService;
  let httpSpy: { get: jasmine.Spy };

  beforeEach(() => {
    const cookieSpyObj = jasmine.createSpyObj('CookieService', ['get']);
    const configMock = { 'baseUrl': 'testUrl/' };
    const httpSpyObj = jasmine.createSpyObj('HttpClient', ['get']);

    TestBed.configureTestingModule({
      'providers': [
        PhenoBrowserService,
        { provide: CookieService, useValue: cookieSpyObj },
        { provide: ConfigService, useValue: configMock },
        { provide: HttpClient, useValue: httpSpyObj },
      ]
    });

    phenoBrowserService = TestBed.get(PhenoBrowserService);
    httpSpy = TestBed.get(HttpClient);
  });

  it('should fetch instruments', () => {
    // 'as unknown' is used to bypass warnings, since string[] does not overlap with PhenoInstruments
    const expectedInstruments: PhenoInstruments = ['i1', 'i2', 'i3'] as unknown as PhenoInstruments;
    const response = ['i1', 'i2', 'i3'];

    httpSpy.get.and.returnValue(of(response));
    phenoBrowserService.getInstruments(null).subscribe(
      instruments => expect(instruments).toEqual(expectedInstruments),
      fail
    );
  });

  it('should fetch measures by parameters', () => {
    const phenoMeasuresJson = {'base_image_url': 'base', 'measures': [fakeJsonMeasure], 'has_descriptions': true, 'regression_names': []};
    const expectedMeasures: PhenoMeasures = PhenoMeasures.fromJson(phenoMeasuresJson);
    const response = phenoMeasuresJson;

    httpSpy.get.and.returnValue(of(response));
    phenoBrowserService.getMeasures(null, null, null).subscribe(
      measures => expect(measures).toEqual(PhenoMeasures.addBasePath(expectedMeasures)),
      fail
    );
  });

  it('should provide a correct download link', () => {
    const instrumentName = 'testInstrument';
    const datasetName = 'testDataset';
    const expectedUrl = `testUrl/pheno_browser/download`
                        + `?dataset_id=${datasetName}&instrument=${instrumentName}`;
    expect(phenoBrowserService.getDownloadLink(instrumentName, datasetName)).toBe(expectedUrl);
  });
});
