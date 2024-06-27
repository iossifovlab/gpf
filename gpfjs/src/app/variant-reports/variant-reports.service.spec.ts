import { TestBed } from '@angular/core/testing';
import { VariantReportsService } from './variant-reports.service';
import { HttpClientModule} from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { APP_BASE_HREF } from '@angular/common';
import { NgxsModule } from '@ngxs/store';
import { Dataset } from 'app/datasets/datasets';
import { DatasetModel } from 'app/datasets/datasets.state';
import { of } from 'rxjs';


describe('VariantReportsService', () => {
  let service: VariantReportsService;

  beforeEach(() => {
    const configMock = { baseUrl: 'testUrl/' };
    TestBed.configureTestingModule({
      imports: [HttpClientModule, NgxsModule.forRoot([], {developmentMode: true})],
      providers: [VariantReportsService,
        { provide: ConfigService, useValue: configMock },
        { provide: APP_BASE_HREF, useValue: '' },
      ]
    });

    service = TestBed.inject(VariantReportsService);

    // eslint-disable-next-line max-len
    const selectedDatasetMock = new Dataset('testId', 'desc', '', 'testDataset', [], true, [], [], [], '', true, true, true, true, null, null, null, [], null, null, '', null);
    const selectedDatasetMockModel: DatasetModel = {selectedDataset: selectedDatasetMock};

    service['store'] = {
      selectOnce: () => of(selectedDatasetMockModel)
    } as never;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get download link', () => {
    const expectedLink = 'http://localhost:8000/api/v3/common_reports/families_data/testId';

    const actualLink = service.getDownloadLink();

    expect(actualLink).toBe(expectedLink);
  });
});
