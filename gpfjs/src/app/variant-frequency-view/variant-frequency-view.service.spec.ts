import { TestBed } from '@angular/core/testing';

import { VariantFrequencyViewService } from './variant-frequency-view.service';

describe('VariantFrequencyViewService', () => {
  let service: VariantFrequencyViewService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(VariantFrequencyViewService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
