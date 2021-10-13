import { HttpClient } from '@angular/common/http';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { of } from 'rxjs/internal/observable/of';
import { PhenoToolResults } from './pheno-tool-results';
import { PhenoToolService } from './pheno-tool.service';

describe('PhenoToolService', () => {
  let service: PhenoToolService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfigService, HttpClientTestingModule, PhenoToolService],
      imports: [HttpClientTestingModule],
    });

    service = TestBed.inject(PhenoToolService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  /*
  it('should get pheno tool results', () => {
    const httpGetSpy = spyOn(HttpClient.prototype, 'get');
    httpGetSpy.and.returnValue(of('fakeResponse'));
  });
  */
});
