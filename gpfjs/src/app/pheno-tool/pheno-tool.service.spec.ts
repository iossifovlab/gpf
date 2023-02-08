import { HttpClient } from '@angular/common/http';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { of } from 'rxjs';
import { PhenoToolService } from './pheno-tool.service';

describe('PhenoToolService', () => {
  let service: PhenoToolService;

  beforeEach(() => {
    const configMock = { baseUrl: 'testUrl/' };
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

    expect(httpGetSpy.mock.calls).toEqual(
      [
        [
          'testUrl/pheno_tool',
          'filter',
          {
            headers: {
              'Content-Type': 'application/json'
            },
            withCredentials: true
          }
        ]
      ]
    );
  });

  it('should download pheno tool results', () => {
    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    service.downloadPhenoToolResults('filter' as any);
    expect(JSON.stringify(httpPostSpy.mock.calls)).toStrictEqual(JSON.stringify(
      [
        [
          'testUrl/pheno_tool',
          'filter',
          { headers: {'Content-Type': 'application/json'}, withCredentials: true }
        ],
        [
          'testUrl/pheno_tool/download',
          'filter',
          {
            observe: 'response',
            headers: {normalizedNames: {}, lazyUpdate: null},
            responseType: 'blob'
          }
        ]
      ]
    ));
    expect(JSON.stringify(httpPostSpy.mock.results)).toStrictEqual(JSON.stringify([
      {
        type: 'return',
        value: of([]),
      }, {
        type: 'return',
        value: {}}
    ]));
  });
});
