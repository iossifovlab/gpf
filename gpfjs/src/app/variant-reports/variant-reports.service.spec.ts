import { TestBed, inject } from '@angular/core/testing';

import { VariantReportsService } from './variant-reports.service';
import { HttpClientModule } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';

describe('VariantReportsService', () => {
  beforeEach(() => {
    const configMock = { 'baseUrl': 'testUrl/' };
    TestBed.configureTestingModule({
      imports: [HttpClientModule],
      providers: [VariantReportsService, { provide: ConfigService, useValue: configMock }]
    });
  });

  it('should ...', inject([VariantReportsService], (service: VariantReportsService) => {
    expect(service).toBeTruthy();
  }));
});
