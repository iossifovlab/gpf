import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed, inject } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';

import { ChromosomeService } from './chromosome.service';

describe('ChromosomeService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ChromosomeService, ConfigService],
      imports: [HttpClientTestingModule]
    });
  });

  it('should be created', inject([ChromosomeService], (service: ChromosomeService) => {
    expect(service).toBeTruthy();
  }));
});
