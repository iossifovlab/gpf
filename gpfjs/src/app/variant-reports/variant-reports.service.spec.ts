import { TestBed, inject } from '@angular/core/testing';

import { VariantReportsService } from './variant-reports.service';

describe('VariantReportsService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [VariantReportsService]
    });
  });

  it('should ...', inject([VariantReportsService], (service: VariantReportsService) => {
    expect(service).toBeTruthy();
  }));
});
