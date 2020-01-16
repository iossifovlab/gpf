import { TestBed, inject } from '@angular/core/testing';

import { HttpModule } from '@angular/http';
import { VariantReportsService } from './variant-reports.service';

describe('VariantReportsService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpModule],
      providers: [VariantReportsService]
    });
  });

  it('should ...', inject([VariantReportsService], (service: VariantReportsService) => {
    expect(service).toBeTruthy();
  }));
});
