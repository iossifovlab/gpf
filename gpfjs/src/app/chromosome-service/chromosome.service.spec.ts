import { TestBed, inject } from '@angular/core/testing';

import { ChromosomeService } from './chromosome.service';

describe('ChromosomeService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ChromosomeService]
    });
  });

  it('should be created', inject([ChromosomeService], (service: ChromosomeService) => {
    expect(service).toBeTruthy();
  }));
});
