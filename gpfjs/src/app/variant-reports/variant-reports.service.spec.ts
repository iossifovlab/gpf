import { TestBed, inject } from '@angular/core/testing';

import { VariantReportsService } from './variant-reports.service';
import { HttpClient, HttpClientModule} from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { Observable, of } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';
import { environment } from 'environments/environment';

class MockDatasetsService {
  public getSelectedDatasetId(): string {
    return 'test_dataset';
  }
  public getSelectedDataset(): Observable<any> {
    return of({accessRights: true});
  }
  public getDataset(): Observable<any> {
    return of({accessRights: true});
  }
}

describe('VariantReportsService', () => {
  beforeEach(() => {
    const configMock = { baseUrl: 'testUrl/' };
    const datasetsMock = new MockDatasetsService();
    TestBed.configureTestingModule({
      imports: [HttpClientModule],
      providers: [VariantReportsService,
        { provide: ConfigService, useValue: configMock },
        { provide: DatasetsService, useValue: datasetsMock },
      ]
    });
  });

  it('should ...', inject([VariantReportsService], (service: VariantReportsService) => {
    expect(service).toBeTruthy();
  }));

  it('should download families', inject([VariantReportsService], (service: VariantReportsService) => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    service.downloadFamilies();
    expect(httpGetSpy).toHaveBeenCalledWith(`${environment.apiPath}common_reports/families_data/undefined`,
      {observe: 'response', responseType: 'blob'}
    );
    expect(JSON.stringify(httpGetSpy.mock.results)).toStrictEqual(JSON.stringify(
      [
        {
          type: 'return', value: { source: {source: {}}}
        }
      ]
    ));
  }));
});
