import { TestBed } from '@angular/core/testing';

import { AutismGeneSingleProfileService } from './autism-gene-single-profile.service';

describe('AutismGeneSingleProfileService', () => {
  let service: AutismGeneSingleProfileService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AutismGeneSingleProfileService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
