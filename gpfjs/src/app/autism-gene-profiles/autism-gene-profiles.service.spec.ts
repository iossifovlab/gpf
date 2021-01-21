import { TestBed } from '@angular/core/testing';

import { AutismGeneProfilesService } from './autism-gene-profiles.service';

describe('AutismGeneProfilesService', () => {
  let service: AutismGeneProfilesService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AutismGeneProfilesService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
