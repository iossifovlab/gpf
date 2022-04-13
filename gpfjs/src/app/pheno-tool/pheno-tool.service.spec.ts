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
    const configMock = { 'baseUrl': 'testUrl/' };
    TestBed.configureTestingModule({
      providers: [{provide: ConfigService, useValue: configMock}, HttpClientTestingModule, PhenoToolService],
      imports: [HttpClientTestingModule],
    });

    service = TestBed.inject(PhenoToolService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get pheno tool results', () => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpGetSpy.mockReturnValue(of('fakeResponse'));
    service.getPhenoToolResults('filter' as any);

    expect(httpGetSpy.calls.allArgs()).toEqual(
      [
        [
          'testUrl/pheno_tool',
          'filter',
          {
            'headers': {
              'Content-Type': 'application/json'
            },
            'withCredentials': true
          }
        ]
      ]
    );
  });
});
