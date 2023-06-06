import { TestBed } from '@angular/core/testing';
import { VariantReportsService } from './variant-reports.service';
import { HttpClientModule} from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { Observable, of } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';
import { APP_BASE_HREF } from '@angular/common';

class MockDatasetsService {
  public getSelectedDatasetId(): string {
    return 'test_dataset';
  }
  public getSelectedDataset(): object {
    return {id: 'test_dataset'};
  }
  public getDataset(): Observable<any> {
    return of({accessRights: true});
  }
}

describe('VariantReportsService', () => {
  let service: VariantReportsService;

  beforeEach(() => {
    const configMock = { baseUrl: 'testUrl/' };
    const datasetsMock = new MockDatasetsService();
    TestBed.configureTestingModule({
      imports: [HttpClientModule],
      providers: [VariantReportsService,
        { provide: ConfigService, useValue: configMock },
        { provide: DatasetsService, useValue: datasetsMock },
        { provide: APP_BASE_HREF, useValue: '' },
      ]
    });

    service = TestBed.inject(VariantReportsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get download link', () => {
    const expectedLink = 'http://localhost:8000/api/v3/common_reports/families_data/test_dataset';

    const actualLink = service.getDownloadLink();

    expect(actualLink).toBe(expectedLink);
  });
});
