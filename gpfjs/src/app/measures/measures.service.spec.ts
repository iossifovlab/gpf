import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed, inject } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';

import { MeasuresService } from './measures.service';

describe('MeasuresService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [MeasuresService, ConfigService],
      imports: [HttpClientTestingModule, RouterTestingModule]
    });
  });

  it('should ...', inject([MeasuresService], (service: MeasuresService) => {
    expect(service).toBeTruthy();
  }));
});
