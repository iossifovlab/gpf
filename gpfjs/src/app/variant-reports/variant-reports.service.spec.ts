import { TestBed } from '@angular/core/testing';
import { VariantReportsService } from './variant-reports.service';
import { HttpClientModule} from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { APP_BASE_HREF } from '@angular/common';


describe('VariantReportsService', () => {
  let service: VariantReportsService;

  beforeEach(() => {
    const configMock = { baseUrl: 'testUrl/' };
    TestBed.configureTestingModule({
      imports: [HttpClientModule],
      providers: [VariantReportsService,
        { provide: ConfigService, useValue: configMock },
        { provide: APP_BASE_HREF, useValue: '' },
      ]
    });

    service = TestBed.inject(VariantReportsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get download link', () => {
    const expectedLink = 'http://localhost:8000/api/v3/common_reports/families_data/';

    const actualLink = service.getDownloadLink();

    expect(actualLink).toBe(expectedLink);
  });
});
